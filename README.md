# HX365 Command Center - Projet Final

Orchestrateur IA hybride (NPU/GPU) optimisé pour Ryzen 9 HX & XDNA NPU. Fournit orchestration, interface chat, et un système RAG basé sur USearch.

[![CI](https://img.shields.io/badge/ci-pending-lightgrey)]() [![License](https://img.shields.io/badge/license-MIT-blue)]()

## Statut
Prototype — développement actif

## Quick start (3 étapes)
1. Clonez le dépôt :
```bash
git clone https://github.com/gat45/usine-a-gaz-.git
cd usine-a-gaz-
```

2. Créez un environnement Python et installez les dépendances :
```bash
python -m venv .venv
# Windows PowerShell
.\.venv\Scripts\Activate.ps1
# macOS / Linux
# source .venv/bin/activate
pip install -r requirements.txt
```

3. Lancer une instance minimale (API ou demo) :
```bash
# Si main_final.py prépare et démarre le service
python main_final.py

# Ou si vous avez une app FastAPI exportée dans hx365_api.py :
uvicorn hx365_api:app --host 0.0.0.0 --port 8080 --reload
```

## Arborescence recommandée (extrait)
- hx365_core_fixed.py — moteur d'orchestration
- hx365_hardware.py — détection/optimisation matériel (GPU/NPU)
- hx365_rag.py — ingestion & indexation (USearch)
- hx365_api.py — API FastAPI
- main_final.py — point d'entrée
- configs/ — exemples de configuration (configs/example.yaml)
- requirements.txt — dépendances
- README.md, LICENSE, CONTRIBUTING.md, CODE_OF_CONDUCT.md, .github/

## Prérequis matériels et drivers (GPU / NPU)
- CPU : AMD Ryzen 9 HX recommandé
- GPU (optionnel) : NVIDIA — installer drivers NVIDIA + CUDA Toolkit (compatible avec la version de torch utilisée)
- NPU XDNA : installer drivers/SDK fournis par le fabricant (documenter la version requise ici)
- Variables d'environnement utiles :
```bash
# Linux / macOS
export GPU_ENABLE=true
export NPU_BACKEND=xdna
export RAG_INDEX_PATH=./data/us_search.index

# Windows (PowerShell)
setx GPU_ENABLE true
setx NPU_BACKEND xdna
```

## Configuration
1. Copier l'exemple :
```bash
cp configs/example.yaml configs/local.yaml
# ou sur Windows PowerShell:
Copy-Item .\configs\example.yaml .\configs\local.yaml
```
2. Modifier `configs/local.yaml` pour indiquer ton matériel et chemins.

## Endpoints API (exemples)
- GET /health — vérifie l'état
- POST /chat — body: { "prompt": "Bonjour" }

Exemple curl :
```bash
curl -X POST http://localhost:8080/chat \
  -H "Content-Type: application/json" \
  -d '{"prompt":"Bonjour"}'
```

## Tests & Qualité
- Formatage / lint :
```bash
pip install black flake8 isort
black .
flake8
```
- Tests unitaires :
```bash
pip install pytest
pytest tests/
```
- Typage statique (optionnel) :
```bash
pip install mypy
mypy .
```

## CI (GitHub Actions)
Un workflow de base est fourni dans `.github/workflows/ci.yml` pour exécuter lint & tests sur les PRs.

## Sécurité & Confidentialité
- Ne commitez jamais de secrets (tokens, clés privées). Utilisez `.env` (gitignored) localement et GitHub Secrets pour CI.
- Scanner le repo avant publication : `gitleaks detect --source .`
- Pour la RAG : obtenez le consentement pour les données sensibles ingérées et évitez de mettre des documents privés dans l'index public.

## Contribution
Merci de contribuer ! Workflow recommandé :
1. Ouvrir une issue → discuter
2. Créer une branche `feature/xxx`
3. Ouvrir une PR avec description et tests  
Voir `CONTRIBUTING.md` pour les détails.

## Fichiers à ajouter si absent
- LICENSE (MIT)
- CONTRIBUTING.md
- CODE_OF_CONDUCT.md
- .github/workflows/ci.yml
- configs/example.yaml
- requirements.txt

## Licence
MIT — voir le fichier LICENSE.

## Contact
Auteur : gat45 — https://github.com/gat45