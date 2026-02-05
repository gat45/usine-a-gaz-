@echo off
chcp 65001 >nul
REM HX365 Command Center - Lancement du Système Complet
REM ===================================================

echo HX365 Command Center - Lancement du Système Complet
echo ===================================================
echo.

REM Vérifier si les fichiers critiques existent
echo Verification des fichiers critiques...
if not exist main_final.py (
    echo ERREUR : main_final.py non trouve
    pause
    exit /b 1
)
if not exist hx365_system.py (
    echo ERREUR : hx365_system.py non trouve
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

REM Lancer le systeme HX365 Command Center
echo Lancement du systeme HX365 Command Center...
echo.
echo Pour arreter le serveur, appuyez sur Ctrl+C
echo.
%PYTHON_CMD% main_final.py --demo-mode

echo.
echo Systeme HX365 Command Center arrete.
pause