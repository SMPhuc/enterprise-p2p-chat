@echo off
chcp 65001 >nul
title Enterprise Secret Chat - Client 1-Click
cls
echo =======================================================
echo   🛡️ ENTERPRISE P2P SECRET CHAT - CLIENT 1-CLICK
echo =======================================================
echo.
set /p ENG_NAME=">> Nhập tên kỹ sư của bạn (hoặc nhấn Enter để tự tạo tên): "
if "%ENG_NAME%"=="" (
    set ENG_NAME=KySu_%RANDOM%
)
echo.
echo [OK] Đang mở giao diện Chat cho: %ENG_NAME%...
python app_client.py %ENG_NAME%
pause
