# HX365 Command Center - Projet Final

## Vue d'Ensemble

HX365 Command Center est une plateforme d'orchestration IA avancée qui intègre FastFlowLM et son Companion. Le logiciel sert d'interface de pilotage matériel autant qu'une interface de chat, spécialement optimisé pour les processeurs AMD Ryzen 9 HX et les unités de traitement neuronal XDNA.

## Architecture du Système

### Modules Principaux
1. **hx365_core_fixed.py** - Moteur central avec orchestration
2. **hx365_hardware.py** - Optimiseur matériel pour Ryzen 9 HX et NPU XDNA
3. **hx365_rag.py** - Système RAG avec indexation vectorielle USearch
4. **hx365_power_user.py** - Fonctions avancées pour utilisateurs expérimentés
5. **hx365_api.py** - Serveur API compatible OpenAI
6. **hx365_system.py** - Coordination des composants
7. **main_final.py** - Point d'entrée principal
8. **hx365_tkinter_gui.py** - Interface Tkinter complète

### Interfaces
- **hx365_gui.html** - Interface graphique moderne avec LemonadeJS et TailwindCSS
- **hx365_test_gui.html** - Interface graphique pour les tests
- **hx365_gui_improved.html** - Interface graphique améliorée

### Scripts d'Exécution
- **lancer_systeme.bat** - Script de lancement du système
- **lancer_chatbot.bat** - Script de lancement du chatbot
- **run_final.bat** - Script de vérification finale

## Fonctionnalités

### Backend Orchestration
- Communication bidirectionnelle entre utilisateur, FastFlowLM et Companion
- Gestion d'état en temps réel des services (Ready/Busy/Error)
- Optimisation performance Ryzen 9 avec affinité CPU

### Système RAG
- Ingestion de documents massifs avec chunking intelligent
- Indexation vectorielle via USearch pour une latence minimale
- Gestionnaire de contexte avec "fenêtre glissante"

### Interface Graphique
- Design Glassmorphism Dark, ergonomique, orienté "Tableau de bord de contrôle"
- Panneau de configuration, moniteur de ressources et zone d'entrée pour copier-coller massif
- Support du mode hybride avec Companion pour enrichissement

### Fonctionnalités Avancées
- Mode hybride avec Companion pour enrichissement
- Journal terminal pour le débogage et l'ingénierie inverse
- Commandes slash (/reset, /config, /npu-reboot, etc.)
- Liste blanche des agents CLI pour éviter les injections

## Installation

### Prérequis
- Python 3.8 ou supérieur
- Pip (gestionnaire de paquets Python)

### Étapes d'Installation
1. Clonez ou téléchargez le projet
2. Installez les dépendances requises :
   ```bash
   pip install -r requirements_fixed.txt
   ```

### Dépendances Requises
- fastapi>=0.104.1
- uvicorn>=0.24.0
- httpx>=0.25.2
- pydantic>=2.5.0
- psutil>=5.9.6
- usearch>=2.0.0
- transformers>=4.21.0
- torch>=1.13.0
- numpy>=1.21.0
- nltk>=3.8.1

## Configuration

Le système utilise plusieurs variables d'environnement :
- `FASTFLOWLM_BASE` : URL de base de l'API FastFlowLM (par défaut: "http://127.0.0.1:52625/v1")
- `COMPANION_BASE` : URL de base de l'API FastFlow Companion (par défaut: "http://127.0.0.1:52626/v1")
- `EMBEDDING_DIM` : Dimension des embeddings (par défaut: 384)
- `CHUNK_SIZE` : Taille des chunks pour le RAG (par défaut: 512)
- `MAX_CONTEXT_TOKENS` : Nombre maximal de tokens de contexte (par défaut: 4096)
- `INDEX_FILE` : Fichier d'index vectoriel (par défaut: "hx365_vector_index.us")

## Utilisation

### Lancement du Serveur
Pour démarrer le centre de commande HX365 :
```bash
python main_final.py
```

Options disponibles :
- `--host HOST` : Hôte pour le serveur API (par défaut: 127.0.0.1)
- `--port PORT` : Port pour le serveur API (par défaut: 8080)
- `--no-gui` : Ne pas ouvrir l'interface graphique
- `--check-services` : Vérifier l'état des services et quitter
- `--demo-mode` : Exécuter en mode démo avec des données d'exemple

### Interfaces Disponibles
1. **Interface Web** : Ouvrez `hx365_gui.html` dans votre navigateur
2. **Interface Tkinter** : Exécutez `python hx365_tkinter_gui.py`
3. **Interface de Tests** : Ouvrez `hx365_test_gui.html` dans votre navigateur

## Structure du Projet

```
final/
├── hx365_core_fixed.py          # Moteur central
├── hx365_hardware.py            # Optimisation matérielle
├── hx365_rag.py                 # Système RAG
├── hx365_power_user.py          # Fonctions avancées
├── hx365_api.py                 # Serveur API
├── hx365_system.py              # Coordination des composants
├── main_final.py                # Point d'entrée principal
├── hx365_tkinter_gui.py         # Interface Tkinter
├── hx365_gui.html               # Interface graphique principale
├── hx365_test_gui.html          # Interface de tests
├── hx365_gui_improved.html      # Interface améliorée
├── lancer_systeme.bat           # Script de lancement système
├── lancer_chatbot.bat           # Script de lancement chatbot
├── run_final.bat                # Script de vérification
├── requirements_fixed.txt       # Dépendances
├── README.md                    # Documentation principale
├── SYSTEME_COMPLET.md           # Documentation système
├── VALIDATION_CHATBOT_FASTFLOWLM.md  # Validation
├── CORRECTIONS_FINALES.md       # Corrections appliquées
└── TESTING.md                   # Documentation des tests
```

## Sécurité

- Liste blanche des agents CLI pour éviter les injections de commandes
- Validation des entrées utilisateur
- Ressources limitées (CPU, mémoire, temps)
- Isolation du réseau pour les outils Companion

## Performance

- Optimisation pour AMD Ryzen 9 HX avec affinité CPU
- Surveillance de l'activité du NPU via les compteurs MCDM
- Gestion de la mémoire pour éviter les fuites
- Faible latence grâce à l'indexation vectorielle USearch

## Dépannage

### Problèmes Courants
- **FastFlowLM non détecté** : Vérifiez que FastFlowLM est en cours d'exécution sur le port 52625
- **Problèmes d'optimisation Ryzen 9** : Vérifiez que les pilotes AMD sont à jour
- **Problèmes de performance** : Surveillez l'utilisation CPU et RAM

### Journaux Système
Consultez les fichiers de journalisation pour des informations de débogage détaillées :
- `hx365_main.log` - Journaux du point d'entrée principal
- `hx365_core.log` - Journaux du moteur central

## Licence

Ce projet est distribué sous la licence MIT.