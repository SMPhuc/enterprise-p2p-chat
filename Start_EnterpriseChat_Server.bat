@echo off
chcp 65001 >nul
title EnterpriseSecretChat - Server Relay
cls
echo ================================================================
echo   ENTERPRISE SECRET CHAT - SERVER RELAY CONTROLLER
echo ================================================================
echo.

for /f "tokens=2 delims=:" %%a in ('ipconfig ^| findstr /c:"IPv4" ^| findstr /r "[0-9]"') do (
    for /f "tokens=1" %%b in ("%%a") do (
        set MY_LAN_IP=%%b
        goto :found_ip
    )
)
:found_ip

echo [*] Server Relay LAN IP: %MY_LAN_IP%
echo [*] Relay Traffic Port : 8888
echo [*] Admin Dashboard    : http://127.0.0.1:8890
echo.
echo ================================================================
echo   CONNECTIVITY READY:
echo   - Colleague Package : EnterpriseChat_Client_Package
echo   - Launcher Script   : Launch_EnterpriseChat.bat
echo ================================================================
echo.
echo Starting Enterprise Relay Server and broadcasting LAN Beacon...
echo.

python server_relay.py 8888
pause
