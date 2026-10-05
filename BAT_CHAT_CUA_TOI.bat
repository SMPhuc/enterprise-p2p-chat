@echo off
chcp 65001 >nul
title Enterprise Chat - Client Của Tôi
cls
echo Đang mở giao diện Chat cho SMPhuc...
python app_client.py SMPhuc 127.0.0.1 8888 company_secret_2026
pause
