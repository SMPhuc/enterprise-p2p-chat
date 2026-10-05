@echo off
chcp 65001 >nul
cd /d "%~dp0"
title EnterpriseSecretChat - Thanh Quang
cls
echo ================================================================
echo   ENTERPRISE SECRET CHAT - PHONG CHAT BAO MAT
echo   Nguoi dung: Thanh Quang
echo ================================================================
echo.
echo [*] Dang tu dong ket noi Server Relay trong mang LAN...
echo.

EnterpriseSecretChat.exe "Thanh Quang"

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ERROR] Ung dung gap su co. Ma loi: %ERRORLEVEL%
    pause
)
