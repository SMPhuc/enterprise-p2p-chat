@echo off
chcp 65001 >nul
title EnterpriseSecretChat - Local Client
cls
echo ================================================================
echo   🛡️ ENTERPRISE SECRET CHAT - LOCAL CLIENT CONTROLLER
echo ================================================================
echo.
echo Starting EnterpriseSecretChat Client for SMPhuc...
python app_client.py SMPhuc 127.0.0.1 8888 company_secret_2026
pause
