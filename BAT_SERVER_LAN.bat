@echo off
chcp 65001 >nul
title Enterprise Relay Server - Mạng LAN Nội Bộ
cls
echo ================================================================
echo   🛡️ ENTERPRISE P2P CHAT - MÁY CHỦ SERVER RELAY (MẠNG LAN)
echo ================================================================
echo.

REM Lấy địa chỉ IP mạng LAN hiện tại
for /f "tokens=2 delims=:" %%a in ('ipconfig ^| findstr /c:"IPv4" ^| findstr /r "[0-9]"') do (
    for /f "tokens=1" %%b in ("%%a") do (
        set MY_LAN_IP=%%b
        goto :found_ip
    )
)
:found_ip

echo [*] Địa chỉ IP máy của bạn trong mạng LAN: %MY_LAN_IP%
echo [*] Cổng kết nối Chat Relay: 8888
echo [*] Bảng điều khiển Quản trị (Admin Dashboard): http://127.0.0.1:8890
echo.
echo ================================================================
echo   HƯỚNG DẪN KẾT NỐI CHO ĐỒNG NGHIỆP:
echo   - Đồng nghiệp chung Wi-Fi/LAN chỉ cần mở thư mục "GOI_DONG_NGHIEP_LAN_1CLICK"
echo   - Bấm đúp vào "CHAY_CHAT_LAN.bat" là kết nối thẳng tới máy bạn!
echo ================================================================
echo.
echo Đang khởi động Server Relay và phát sóng tín hiệu dò tìm LAN...
echo.

python server_relay.py 8888
pause
