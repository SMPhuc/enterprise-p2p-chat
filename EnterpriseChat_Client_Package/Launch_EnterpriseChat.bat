@echo off
chcp 65001 >nul
cd /d "%~dp0"
title EnterpriseSecretChat - Client Launcher
cls
echo ================================================================
echo   ENTERPRISE SECRET CHAT - SECURE CLIENT LAUNCHER
echo ================================================================
echo.
echo [*] Auto-discovering Enterprise Server on local Wi-Fi/LAN...
echo.
set /p ENG_NAME=">> Enter your Engineer Name (or press Enter for default): "
if "%ENG_NAME%"=="" (
    set ENG_NAME=Engineer_%RANDOM%
)

echo.
echo [OK] Starting secure chat interface for: %ENG_NAME% ...
EnterpriseSecretChat.exe "%ENG_NAME%"

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ERROR] Application exited with error code: %ERRORLEVEL%
    pause
)
