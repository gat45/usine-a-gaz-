"""
HX365 Command Center - Moteur Central Amélioré
===============================================

Moteur central avec gestion améliorée des erreurs, de la mémoire et des chemins Windows.
"""

import asyncio
import os
import time
import psutil
import logging
import json
import gc
import uuid
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from pathlib import Path

import httpx
from pydantic import BaseModel

# Configuration avec encodage UTF-8 pour Windows
if os.name == 'nt':  # Windows
    os.environ['PYTHONIOENCODING'] = 'utf-8'

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('hx365_core.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("HX365-Core")

# Configuration
FASTFLOWLM_BASE = os.getenv("FASTFLOWLM_BASE", "http://127.0.0.1:52625/v1")
COMPANION_BASE = os.getenv("COMPANION_BASE", "http://127.0.0.1:52626/v1")
DEFAULT_EMBEDDING_DIM = int(os.getenv("EMBEDDING_DIM", "384"))
MAX_CONTEXT_TOKENS = int(os.getenv("MAX_CONTEXT_TOKENS", "4096"))

class ServiceStatus(Enum):
    UNKNOWN = "unknown"
    READY = "ready"
    BUSY = "busy"
    ERROR = "error"
    OFFLINE = "offline"

class HardwareComponent(Enum):
    CPU = "cpu"
    GPU = "gpu"
    NPU = "npud"
    RAM = "ram"

@dataclass
class ServiceState:
    """Représente l'état d'un service"""
    name: str
    status: ServiceStatus
    last_check: datetime
    response_time: float = 0.0
    details: Dict[str, Any] = field(default_factory=dict)

@dataclass
class SystemMetrics:
    """Métriques de ressources système"""
    cpu_percent: float
    ram_percent: float
    ram_used_gb: float
    npu_utilization: float = 0.0
    npu_power: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)

class ServiceOrchestrator:
    """
    Gère la communication entre utilisateur, FastFlowLM et FastFlow Companion
    """
    
    def __init__(self):
        self.fastflowlm_state = ServiceState("FastFlowLM", ServiceStatus.UNKNOWN, datetime.now())
        self.companion_state = ServiceState("FastFlow Companion", ServiceStatus.UNKNOWN, datetime.now())
        self.services = {
            "fastflowlm": self.fastflowlm_state,
            "companion": self.companion_state
        }
        self.client = httpx.AsyncClient(timeout=httpx.Timeout(30.0))
        self._poll_task = None
    
    async def start_polling(self):
        """Démarrer l'interrogation en arrière-plan des états de service"""
        if self._poll_task is None:
            self._poll_task = asyncio.create_task(self._poll_services())
    
    async def stop_polling(self):
        """Arrêter l'interrogation en arrière-plan"""
        if self._poll_task:
            self._poll_task.cancel()
            try:
                await self._poll_task
            except asyncio.CancelledError:
                pass
            self._poll_task = None
    
    async def _poll_services(self):
        """Tâche d'arrière-plan pour interroger les états de service"""
        while True:
            try:
                await self.poll_fastflowlm()
                await self.poll_companion()
                await asyncio.sleep(2.0)  # Interroger toutes les 2 secondes
            except asyncio.CancelledError:
                logger.info("Interrogation des services annulée")
                break
            except Exception as e:
                logger.error(f"Erreur lors de l'interrogation des services: {e}")
                await asyncio.sleep(5.0)  # Attendre plus longtemps en cas d'erreur
    
    async def poll_fastflowlm(self):
        """Interroger l'état de FastFlowLM"""
        start_time = time.time()
        try:
            response = await self.client.get(f"{FASTFLOWLM_BASE}/models")
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                self.fastflowlm_state.status = ServiceStatus.READY
                self.fastflowlm_state.response_time = response_time
                self.fastflowlm_state.details = response.json()
            else:
                self.fastflowlm_state.status = ServiceStatus.ERROR
                self.fastflowlm_state.response_time = response_time
        except Exception as e:
            self.fastflowlm_state.status = ServiceStatus.OFFLINE
            self.fastflowlm_state.response_time = time.time() - start_time
            logger.debug(f"FastFlowLM inaccessible: {e}")
        
        self.fastflowlm_state.last_check = datetime.now()
    
    async def poll_companion(self):
        """Interroger l'état de FastFlow Companion"""
        start_time = time.time()
        try:
            response = await self.client.get(f"{COMPANION_BASE}/health")
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                self.companion_state.status = ServiceStatus.READY
                self.companion_state.response_time = response_time
                self.companion_state.details = response.json()
            else:
                self.companion_state.status = ServiceStatus.ERROR
                self.companion_state.response_time = response_time
        except Exception as e:
            self.companion_state.status = ServiceStatus.OFFLINE
            self.companion_state.response_time = time.time() - start_time
            logger.debug(f"Companion inaccessible: {e}")
        
        self.companion_state.last_check = datetime.now()
    
    async def route_request(self, 
                          user_request: Dict[str, Any],
                          use_companion: bool = False,
                          enrich_with_companion: bool = False) -> Dict[str, Any]:
        """
        Acheminer les requêtes entre FastFlowLM et Companion selon les besoins
        """
        # Vérifier si les services sont disponibles
        if self.fastflowlm_state.status != ServiceStatus.READY:
            return {
                "error": f"FastFlowLM n'est pas prêt ({self.fastflowlm_state.status.value})",
                "service_status": self.fastflowlm_state.status.value
            }
        
        # Si l'enrichissement par le compagnon est demandé, appeler le compagnon en premier
        enriched_context = ""
        if enrich_with_companion and self.companion_state.status == ServiceStatus.READY:
            try:
                companion_payload = {
                    "query": user_request.get("messages", [])[-1]["content"] if user_request.get("messages") else "",
                    "mode": "search"
                }
                companion_response = await self.client.post(
                    f"{COMPANION_BASE}/search",
                    json=companion_payload
                )
                
                if companion_response.status_code == 200:
                    companion_data = companion_response.json()
                    enriched_context = f"\nContexte enrichi du Companion:\n{companion_data.get('results', '')}"
            except Exception as e:
                logger.warning(f"Échec de l'enrichissement par le Companion: {e}")
        
        # Préparer la charge utile finale pour FastFlowLM
        messages = user_request.get("messages", [])
        if enriched_context:
            # Ajouter le contexte enrichi en tant que message système
            messages = [{"role": "system", "content": enriched_context}] + messages
        
        # Mettre à jour la requête avec les messages enrichis
        llm_payload = {**user_request, "messages": messages}
        
        # Envoyer à FastFlowLM
        try:
            response = await self.client.post(
                f"{FASTFLOWLM_BASE}/chat/completions",
                json=llm_payload
            )
            
            if response.status_code == 200:
                result = response.json()
                # Mettre à jour l'état du service à BUSY pendant le traitement
                self.fastflowlm_state.status = ServiceStatus.BUSY
                return result
            else:
                return {
                    "error": f"FastFlowLM a retourné le statut {response.status_code}",
                    "details": response.text
                }
        except Exception as e:
            logger.error(f"Erreur lors de l'appel à FastFlowLM: {e}")
            return {"error": f"Échec de l'appel à FastFlowLM: {str(e)}"}
    
    def get_service_status(self) -> Dict[str, ServiceState]:
        """Obtenir le statut actuel de tous les services"""
        return self.services.copy()

class RequestRouter:
    """
    Achemine les requêtes selon le type et les besoins
    """
    
    def __init__(self, orchestrator: ServiceOrchestrator):
        self.orchestrator = orchestrator
        self.allowed_agents = [
            "fastflow-hx", 
            "companion-search", 
            "companion-tools", 
            "system-info"
        ]
    
    def validate_agent(self, agent_name: str) -> bool:
        """Valider si un agent est autorisé à s'exécuter"""
        return agent_name in self.allowed_agents
    
    async def process_request(self, 
                            request_data: Dict[str, Any], 
                            use_companion: bool = False,
                            enrich_with_companion: bool = False) -> Dict[str, Any]:
        """Traiter une requête utilisateur via le canal approprié"""
        return await self.orchestrator.route_request(
            request_data, 
            use_companion, 
            enrich_with_companion
        )

class StatePoller:
    """
    Interroge l'état système y compris les métriques matérielles
    """
    
    def __init__(self):
        self.metrics_history: List[SystemMetrics] = []
        self.max_history = 100  # Garder les 100 dernières mesures
    
    def get_current_metrics(self) -> SystemMetrics:
        """Obtenir les métriques système actuelles"""
        # Obtenir les métriques CPU et RAM
        cpu_percent = psutil.cpu_percent(interval=0.1)
        memory = psutil.virtual_memory()
        ram_percent = memory.percent
        ram_used_gb = memory.used / (1024**3)
        
        # Valeurs factices pour les métriques NPU (nécessiterait des bibliothèques AMD spécifiques)
        # Dans une implémentation réelle, cela interfaçerait avec les pilotes MCDM
        npu_utilization = 0.0  # Viendrait des compteurs MCDM
        npu_power = 0.0        # Viendrait des compteurs MCDM
        
        metrics = SystemMetrics(
            cpu_percent=cpu_percent,
            ram_percent=ram_percent,
            ram_used_gb=ram_used_gb,
            npu_utilization=npu_utilization,
            npu_power=npu_power
        )
        
        # Ajouter à l'historique
        self.metrics_history.append(metrics)
        if len(self.metrics_history) > self.max_history:
            self.metrics_history.pop(0)
        
        return metrics
    
    def get_historical_metrics(self, minutes: int = 5) -> List[SystemMetrics]:
        """Obtenir les métriques historiques pour les N dernières minutes"""
        cutoff_time = datetime.now().timestamp() - (minutes * 60)
        return [m for m in self.metrics_history if m.timestamp.timestamp() >= cutoff_time]

class HX365CoreEngine:
    """
    Moteur central qui relie tout
    """
    
    def __init__(self):
        self.orchestrator = ServiceOrchestrator()
        self.router = RequestRouter(self.orchestrator)
        self.state_poller = StatePoller()
        self.sessions: Dict[str, List[Dict[str, str]]] = {}
        self.session_params: Dict[str, Dict[str, Any]] = {}
        self.max_session_history = 50  # Limite pour éviter la surconsommation mémoire
        self.gc_threshold = 100  # Seuil pour la collecte de garbage
        self.request_count = 0  # Compteur pour la gestion de la mémoire
    
    async def initialize(self):
        """Initialiser le moteur central"""
        await self.orchestrator.start_polling()
        logger.info("Moteur central HX365 initialisé")
    
    async def shutdown(self):
        """Arrêter le moteur central"""
        await self.orchestrator.stop_polling()
        await self.orchestrator.client.aclose()
        logger.info("Moteur central HX365 arrêté")
    
    def create_session(self, user_id: Optional[str] = None) -> str:
        """Créer une nouvelle session pour un utilisateur"""
        session_id = user_id or str(uuid.uuid4())
        self.sessions[session_id] = []
        self.session_params[session_id] = {
            "temperature": 0.7,
            "max_tokens": 2048,
            "top_p": 0.9,
            "presence_penalty": 0.0,
            "frequency_penalty": 0.0
        }
        return session_id
    
    def add_message_to_session(self, session_id: str, role: str, content: str):
        """Ajouter un message à une session"""
        if session_id not in self.sessions:
            self.create_session(session_id)
        
        self.sessions[session_id].append({
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat()
        })
        
        # Limiter l'historique de session pour éviter les problèmes de mémoire
        if len(self.sessions[session_id]) > self.max_session_history:
            # Garder les messages les plus récents
            self.sessions[session_id] = self.sessions[session_id][-20:]
        
        # Incrémenter le compteur de requêtes pour la gestion de la mémoire
        self.request_count += 1
        
        # Effectuer une collecte de garbage périodique
        if self.request_count % self.gc_threshold == 0:
            collected = gc.collect()
            logger.debug(f"Collecte de garbage effectuée: {collected} objets récupérés")
    
    def get_session_history(self, session_id: str) -> List[Dict[str, str]]:
        """Obtenir l'historique d'une session"""
        return self.sessions.get(session_id, [])
    
    def reset_session(self, session_id: str):
        """Réinitialiser une session"""
        if session_id in self.sessions:
            self.sessions[session_id] = []
    
    async def process_user_request(self, 
                                 session_id: str, 
                                 user_message: str, 
                                 use_companion: bool = False,
                                 enrich_with_companion: bool = False,
                                 **kwargs) -> Dict[str, Any]:
        """Traiter une requête utilisateur via l'ensemble du pipeline"""
        
        # Ajouter le message utilisateur à la session
        self.add_message_to_session(session_id, "user", user_message)
        
        # Obtenir les paramètres de session actuels
        params = self.session_params.get(session_id, {})
        params.update(kwargs)  # Remplacer par les paramètres spécifiques à la requête
        
        # Préparer la charge utile de la requête
        request_payload = {
            "model": "fastflow-hx",
            "messages": self.get_session_history(session_id),
            "temperature": params.get("temperature", 0.7),
            "max_tokens": params.get("max_tokens", 2048),
            "top_p": params.get("top_p", 0.9),
            "presence_penalty": params.get("presence_penalty", 0.0),
            "frequency_penalty": params.get("frequency_penalty", 0.0),
            "stream": False  # Pour simplifier dans cette implémentation
        }
        
        # Traiter via le routeur
        result = await self.router.process_request(
            request_payload,
            use_companion,
            enrich_with_companion
        )
        
        # Ajouter la réponse de l'assistant à la session si succès
        if "choices" in result and len(result["choices"]) > 0:
            assistant_response = result["choices"][0]["message"]["content"]
            self.add_message_to_session(session_id, "assistant", assistant_response)
        elif "error" in result:
            # Ajouter le message d'erreur à la session
            self.add_message_to_session(session_id, "assistant", f"Erreur: {result['error']}")
        
        return result
    
    def get_system_status(self) -> Dict[str, Any]:
        """Obtenir le statut système global"""
        service_status = self.orchestrator.get_service_status()
        current_metrics = self.state_poller.get_current_metrics()
        
        return {
            "timestamp": datetime.now().isoformat(),
            "services": {
                name: {
                    "status": state.status.value,
                    "last_check": state.last_check.isoformat(),
                    "response_time": state.response_time,
                    "details": state.details
                }
                for name, state in service_status.items()
            },
            "system_metrics": {
                "cpu_percent": current_metrics.cpu_percent,
                "ram_percent": current_metrics.ram_percent,
                "ram_used_gb": current_metrics.ram_used_gb,
                "npu_utilization": current_metrics.npu_utilization,
                "npu_power": current_metrics.npu_power
            },
            "active_sessions": len(self.sessions),
            "request_count": self.request_count
        }

# Instance globale
hx365_engine = HX365CoreEngine()

# Initialiser le moteur quand le module est utilisé
def init_engine_sync():
    """Version synchrone de l'initialisation pour éviter les erreurs d'événement loop"""
    # L'initialisation asynchrone sera faite par le système principal
    logger.info("Moteur central HX365 prêt pour l'initialisation")

# Appeler la version synchrone pour éviter les erreurs
init_engine_sync()