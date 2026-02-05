@echo off
chcp 65001 >nul
REM FastFlowLM Chatbot - Lancement Complet
REM ======================================

echo FastFlowLM Chatbot - Lancement Complet
echo ======================================
echo.

REM Vérifier si les fichiers critiques existent
echo Verification des fichiers critiques...
if not exist main_final.py (
    echo ERREUR : main_final.py non trouve
    pause
    exit /b 1
)
if not exist hx365_api.py (
    echo ERREUR : hx365_api.py non trouve
    pause
    exit /b 1
)
if not exist hx365_gui.html (
    echo ERREUR : hx365_gui.html non trouve
    pause
    exit /b 1
)
if not exist hx365_core_fixed.py (
    echo ERREUR : hx365_core_fixed.py non trouve
    pause
    exit /b 1
)
if not exist hx365_hardware.py (
    echo ERREUR : hx365_hardware.py non trouve
    pause
    exit /b 1
)
if not exist hx365_rag.py (
    echo ERREUR : hx365_rag.py non trouve
    pause
    exit /b 1
)
if not exist hx365_power_user.py (
    echo ERREUR : hx365_power_user.py non trouve
    pause
    exit /b 1
)

echo Tous les fichiers critiques sont presents
echo.

REM Vérifier si Python est disponible
echo Verification de la disponibilite de Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo AVERTISSEMENT : Python n'est pas disponible dans le PATH
    echo Essayez d'utiliser python3 a la place...
    python3 --version >nul 2>&1
    if errorlevel 1 (
        echo ERREUR : Ni python ni python3 n'ont ete trouves
        echo Installez Python et assurez-vous qu'il est dans le PATH
        pause
        exit /b 1
    ) else (
        set PYTHON_CMD=python3
    )
) else (
    set PYTHON_CMD=python
)

echo Python trouve : %PYTHON_CMD%
echo.

REM Vérifier si FastFlowLM est en cours d'execution
echo Verification de l'etat de FastFlowLM (port 52625)...
ping -n 1 -w 1000 127.0.0.1 >nul 2>&1
if errorlevel 1 (
    echo AVERTISSEMENT : Impossible de verifier l'etat de FastFlowLM
) else (
    echo FastFlowLM : Verification du port 52625 en cours...
)

echo.

REM Lancer le serveur backend
echo Lancement du serveur backend (API)...
start "FastFlowLM Backend" cmd /c "%PYTHON_CMD% main_final.py --host 127.0.0.1 --port 8080 --demo-mode"

REM Attendre un peu pour que le serveur demarre
echo Attente du demarrage du serveur (5 secondes)...
timeout /t 5 /nobreak >nul

REM Lancer le frontend dans le navigateur
echo Lancement de l'interface frontend dans le navigateur...
start "" "hx365_gui.html"

echo.
echo ======================================
echo FastFlowLM Chatbot est maintenant lance !
echo ======================================
echo.
echo Serveur backend disponible sur : http://127.0.0.1:8080
echo Interface frontend ouverte dans votre navigateur
echo.
echo Pour arreter le serveur backend, fermez la fenetre du serveur
echo ou appuyez sur Ctrl+C dans la fenetre du serveur
echo.
pause