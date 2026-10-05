@echo off
chcp 65001 >nul
cd /d "%~dp0"
title EnterpriseSecretChat - Thanh Quang
cls
echo ================================================================
echo   ENTERPRISE SECRET CHAT - SECURE CLIENT LAUNCHER
echo   Nguoi dung: Thanh Quang
echo ================================================================
echo.
echo [*] Dang tu dong ket noi Server Relay trong mang LAN...
echo.

if exist "EnterpriseSecretChat.exe" (
    EnterpriseSecretChat.exe "Thanh Quang"
) else if exist "EnterpriseChat_Client_Package\EnterpriseSecretChat.exe" (
    cd /d "%~dp0EnterpriseChat_Client_Package"
    EnterpriseSecretChat.exe "Thanh Quang"
) else (
    python app_client.py "Thanh Quang" 127.0.0.1 8888 company_secret_2026
)

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ERROR] Ung dung gap su co. Ma loi: %ERRORLEVEL%
    pause
)
