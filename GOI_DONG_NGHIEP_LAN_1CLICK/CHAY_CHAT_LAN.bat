@echo off
chcp 65001 >nul
title Enterprise P2P Secret Chat - Mạng LAN Nội Bộ
cls
echo =======================================================
echo   🛡️ ENTERPRISE P2P CHAT - MẠNG LAN NỘI BỘ (1-CLICK)
echo =======================================================
echo.
echo [*] Đang tự động kết nối tới Server trong mạng Wi-Fi công ty...
echo.
set /p ENG_NAME=">> Nhập tên của bạn (hoặc nhấn Enter để tự tạo tên): "
if "%ENG_NAME%"=="" (
    EnterpriseSecretChat.exe
) else (
    EnterpriseSecretChat.exe "%ENG_NAME%"
)
