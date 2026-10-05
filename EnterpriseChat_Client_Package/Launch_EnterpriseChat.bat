@echo off
chcp 65001 >nul
title EnterpriseSecretChat - Client
cls
echo =======================================================
echo   🛡️ ENTERPRISE SECRET CHAT - SECURE CLIENT LAUNCHER
echo =======================================================
echo.
echo [*] Auto-discovering Enterprise Server on local network...
echo.
set /p ENG_NAME=">> Enter your Engineer Name (or press Enter for default): "
if "%ENG_NAME%"=="" (
    EnterpriseSecretChat.exe
) else (
    EnterpriseSecretChat.exe "%ENG_NAME%"
)
