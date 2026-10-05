@echo off
chcp 65001 >nul
title Enterprise Secret Chat - 1-Click
cls
echo =======================================================
echo   🛡️ ENTERPRISE P2P SECRET CHAT - KHỞI CHẠY 1-CLICK
echo =======================================================
echo.
set /p ENG_NAME=">> Nhập tên kỹ sư của bạn (hoặc nhấn Enter để tự tạo tên): "
if "%ENG_NAME%"=="" (
    EnterpriseSecretChat.exe
) else (
    EnterpriseSecretChat.exe "%ENG_NAME%"
)
