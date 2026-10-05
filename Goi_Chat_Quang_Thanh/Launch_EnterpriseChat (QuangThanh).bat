@echo off
chcp 65001 >nul
cd /d "%~dp0"
title EnterpriseSecretChat - Quang Thanh
cls
echo ================================================================
echo   ENTERPRISE SECRET CHAT - PHONG CHAT BAO MAT
echo   Nguoi dung: Quang Thanh
echo ================================================================
echo.
echo [*] Dang tu dong ket noi Server Relay trong mang LAN...
echo.

EnterpriseSecretChat.exe "Quang Thanh"

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ERROR] Ung dung gap su co. Ma loi: %ERRORLEVEL%
    pause
)
