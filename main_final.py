#!/usr/bin/env python3
"""
HX365 Command Center - Point d'Entrée Principal Final
======================================================

Ce script lance l'application complète du centre de commande HX365 avec:
- Serveur API
- Optimisation matérielle
- Système RAG
- Fonctions avancées
Avec une gestion correcte des initialisations asynchrones.
"""

import asyncio
import os
import sys
import argparse
import webbrowser
import time
from pathlib import Path
import logging

# Configuration de l'encodage pour Windows
if sys.platform.startswith('win'):
    os.environ['PYTHONIOENCODING'] = 'utf-8'

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('hx365_main.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("HX365-Main")

def check_dependencies():
    """Vérifier si les dépendances requises sont disponibles"""
    missing_deps = []
    
    modules_to_check = [
        ('fastapi', 'FastAPI'),
        ('httpx', 'HTTPX'),
        ('usearch', 'USearch'),
        ('transformers', 'Transformers'),
        ('torch', 'PyTorch'),
        ('psutil', 'Psutil'),
        ('nltk', 'NLTK')
    ]
    
    for module_name, description in modules_to_check:
        try:
            __import__(module_name)
        except ImportError:
            missing_deps.append(f"{description} ({module_name})")
    
    if missing_deps:
        logger.error(f"Dépendances manquantes: {', '.join(missing_deps)}")
        logger.error("Veuillez installer les dépendances avec: pip install -r requirements.txt")
        return False
    
    logger.info("✅ Toutes les dépendances sont disponibles")
    return True

def start_api_server(host="127.0.0.1", port=8080):
    """Démarrer le serveur API"""
    try:
        import uvicorn
        from hx365_api import app  # Importer ici pour éviter les problèmes d'initialisation anticipée
        logger.info(f"Démarrage du serveur API sur http://{host}:{port}")
        uvicorn.run(app, host=host, port=port, log_level="info", access_log=True)
    except ImportError as e:
        logger.error(f"Impossible d'importer le serveur API: {e}")
        logger.error("Vérifiez que FastAPI est installé: pip install fastapi uvicorn")
        return
    except Exception as e:
        logger.error(f"Erreur lors du démarrage du serveur API: {e}")

def open_gui():
    """Ouvrir l'interface graphique dans le navigateur par défaut"""
    # Utiliser des chemins résolus pour éviter les problèmes Windows
    gui_path = Path("hx365_gui.html").resolve()
    if not gui_path.exists():
        logger.error(f"Fichier GUI non trouvé: {gui_path}")
        return False
    
    try:
        webbrowser.open(f"file://{gui_path.as_uri()}")
        logger.info("Interface graphique ouverte dans le navigateur par défaut")
        return True
    except Exception as e:
        logger.error(f"Impossible d'ouvrir l'interface graphique: {e}")
        return False

async def initialize_components():
    """Initialiser tous les composants"""
    logger.info("Initialisation des composants...")
    
    try:
        # Importer et initialiser les composants ici
        from hx365_system import get_engines
        engines = get_engines()
        
        # Initialiser chaque moteur
        await engines['core'].initialize()
        await engines['hardware'].initialize()
        await engines['power_user'].initialize()
        
        logger.info("✅ Tous les composants ont été initialisés avec succès")
        return True
    except Exception as e:
        logger.error(f"❌ Échec de l'initialisation des composants: {e}")
        import traceback
        traceback.print_exc()
        return False

async def shutdown_components():
    """Arrêter tous les composants"""
    logger.info("Arrêt des composants...")
    
    try:
        from hx365_system import get_engines
        engines = get_engines()
        
        # Arrêter chaque moteur
        await engines['power_user'].shutdown()
        await engines['hardware'].shutdown()
        await engines['core'].shutdown()
        
        logger.info("✅ Tous les composants ont été arrêtés avec succès")
        return True
    except Exception as e:
        logger.error(f"❌ Échec de l'arrêt des composants: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Fonction principale"""
    parser = argparse.ArgumentParser(
        description="HX365 Command Center - Plateforme d'Orchestration IA",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemples:
  %(prog)s --host 0.0.0.0 --port 8080
  %(prog)s --no-gui
  %(prog)s --demo-mode
        """
    )
    parser.add_argument("--host", default="127.0.0.1", help="Hôte pour le serveur API")
    parser.add_argument("--port", type=int, default=8080, help="Port pour le serveur API")
    parser.add_argument("--no-gui", action="store_true", help="Ne pas ouvrir l'interface graphique")
    parser.add_argument("--demo-mode", action="store_true", help="Exécuter en mode démo avec données d'exemple")
    
    args = parser.parse_args()
    
    logger.info("HX365 Command Center")
    logger.info("=" * 21)
    
    # Vérifier les dépendances
    if not check_dependencies():
        return 1
    
    # Initialiser les composants
    init_success = asyncio.run(initialize_components())
    if not init_success:
        logger.error("Échec de l'initialisation. Arrêt du programme.")
        return 1
    
    # Ajouter des données d'exemple en mode démo
    if args.demo_mode:
        logger.info("Chargement des données de démonstration...")
        try:
            from hx365_system import get_engines
            engines = get_engines()
            rag_engine = engines['rag']
            
            sample_docs = [
                ("Guide Python", "Python est un langage de programmation interprété, multi-paradigme et multiplateforme. Il favorise la productivité et la lisibilité du code."),
                ("Technologie Ryzen", "Les processeurs AMD Ryzen utilisent une architecture avancée avec des 'chiplets' pour des performances élevées. La série Ryzen 9 HX est optimisée pour les stations de travail mobiles."),
                ("Accélération NPU", "Les unités de traitement neuronal (NPU) fournissent une accélération matérielle dédiée pour les charges de travail IA. L'architecture XDNA d'AMD offre des capacités d'inférence efficaces.")
            ]
            
            for title, content in sample_docs:
                doc_id = rag_engine.ingest_document(content, doc_id=title)
                logger.info(f"Document chargé: {title} (ID: {doc_id})")
            
            logger.info(f"✅ {len(sample_docs)} documents d'exemple chargés dans le système RAG")
        except Exception as e:
            logger.error(f"Erreur lors du chargement des documents d'exemple: {e}")
    
    # Démarrer l'interface graphique si demandé
    if not args.no_gui:
        logger.info("Ouverture de l'interface graphique...")
        try:
            gui_opened = open_gui()
            if not gui_opened:
                logger.warning("Impossible d'ouvrir l'interface graphique. Vous pouvez l'ouvrir manuellement.")
        except Exception as e:
            logger.error(f"Impossible d'ouvrir l'interface graphique: {e}")
            logger.info("Vous pouvez ouvrir hx365_gui.html manuellement dans votre navigateur")
    
    logger.info(f"Démarrage du serveur sur http://{args.host}:{args.port}")
    logger.info("Appuyez sur Ctrl+C pour arrêter le serveur")
    
    try:
        start_api_server(args.host, args.port)
    except KeyboardInterrupt:
        logger.info("\nArrêt du serveur...")
        asyncio.run(shutdown_components())
        logger.info("Au revoir!")
        return 0
    except Exception as e:
        logger.error(f"Erreur lors de l'exécution du serveur: {e}")
        asyncio.run(shutdown_components())
        return 1

if __name__ == "__main__":
    # S'assurer que l'encodage est correctement configuré
    if sys.platform.startswith('win'):
        os.environ['PYTHONIOENCODING'] = 'utf-8'
    
    # Exécuter la fonction principale
    sys.exit(main())