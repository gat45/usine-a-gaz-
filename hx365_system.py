"""
HX365 Command Center - Point d'Entrée Unique et Coordination
=============================================================

Ce module coordonne tous les composants du système HX365 Command Center
sans causer de problèmes d'initialisation anticipée.
"""

# Ce fichier permet d'importer les composants sans exécuter l'initialisation automatique
# L'initialisation est effectuée explicitement par le système principal

from .hx365_core_fixed import HX365CoreEngine
from .hx365_hardware import HX365HardwareOptimizer
from .hx365_rag import RAGEngine
from .hx365_power_user import PowerUserFeatures

# Instances globales mais non-initialisées
hx365_engine = None
hardware_optimizer = None
rag_engine = None
power_user_features = None

def initialize_engines():
    """Initialiser toutes les instances de moteur"""
    global hx365_engine, hardware_optimizer, rag_engine, power_user_features
    
    if hx365_engine is None:
        from .hx365_core_fixed import hx365_engine as core_engine
        hx365_engine = core_engine
    
    if hardware_optimizer is None:
        from .hx365_hardware import hardware_optimizer as hw_optimizer
        hardware_optimizer = hw_optimizer
    
    if rag_engine is None:
        from .hx365_rag import rag_engine as rag_instance
        rag_engine = rag_instance
    
    if power_user_features is None:
        from .hx365_power_user import power_user_features as power_features
        power_user_features = power_features

def get_engines():
    """Obtenir toutes les instances de moteur"""
    initialize_engines()
    return {
        'core': hx365_engine,
        'hardware': hardware_optimizer,
        'rag': rag_engine,
        'power_user': power_user_features
    }

# Fonction utilitaire pour le système
def get_system_status():
    """Obtenir l'état du système sans initialisation anticipée"""
    engines = get_engines()
    if engines['core'] is not None:
        try:
            return engines['core'].get_system_status()
        except Exception:
            return {"status": "not_initialized", "engines_loaded": list(engines.keys())}
    return {"status": "engines_not_loaded"}