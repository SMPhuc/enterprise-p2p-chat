@echo off
chcp 65001 >nul
cd /d "%~dp0"
title EnterpriseSecretChat - SMPhuc
cls
echo ================================================================
echo   ENTERPRISE SECRET CHAT - LOCAL CLIENT CONTROLLER
echo   Nguoi dung: SMPhuc
echo ================================================================
echo.
echo Starting EnterpriseSecretChat Client for SMPhuc...
python app_client.py SMPhuc
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ERROR] Ung dung gap su co. Ma loi: %ERRORLEVEL%
    pause
)
