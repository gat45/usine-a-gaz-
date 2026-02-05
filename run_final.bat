@echo off
chcp 65001 >nul
REM HX365 Command Center - Script de Vérification Finale
REM ====================================================

echo HX365 Command Center - Vérification Finale
echo ============================================
echo.

REM Vérifier si les fichiers critiques existent
echo Verification des fichiers critiques...
if not exist verify_final_only.py (
    echo ERREUR : verify_final_only.py non trouve
    pause
    exit /b 1
)
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

REM Verifier si Python est disponible
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

REM Executer le script de verification finale
echo Execution du script de verification finale...
%PYTHON_CMD% verify_final_only.py
set VERIFY_EXIT_CODE=%ERRORLEVEL%

echo.
if %VERIFY_EXIT_CODE% EQU 0 (
    echo La verification s'est terminee avec succes
) else (
    echo La verification s'est terminee avec des erreurs (code: %VERIFY_EXIT_CODE%)
)

REM Proposer d'executer le systeme final
echo.
set /p RUN_SYSTEM="Voulez-vous executer le systeme HX365 Command Center final? (y/N): "
if /i "%RUN_SYSTEM%"=="y" (
    echo.
    echo Lancement du systeme HX365 Command Center final...
    %PYTHON_CMD% main_final.py --demo-mode
)

echo.
echo Verification et lancement termines.
pause