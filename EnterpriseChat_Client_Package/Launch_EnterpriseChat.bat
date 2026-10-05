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
set /p USER_NAME=">> Nhap ten nguoi dung (Enter de lay mac dinh): "
if "%USER_NAME%"=="" (
    set USER_NAME=User_%RANDOM%
)

echo.
echo [OK] Dang khoi dong giao dien chat cho: %USER_NAME% ...
EnterpriseSecretChat.exe "%USER_NAME%"

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ERROR] Ung dung da thoat voi ma loi: %ERRORLEVEL%
    pause
)
