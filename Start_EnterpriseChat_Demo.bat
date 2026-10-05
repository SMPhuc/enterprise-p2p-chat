@echo off
chcp 65001 >nul
title EnterpriseSecretChat - Simulation Demo
cls
echo ================================================================
echo   ENTERPRISE SECRET CHAT - SYSTEM DEMO INITIALIZER
echo ================================================================
echo.
echo [1/3] Starting Enterprise Relay Server on port 8888...
start "Enterprise Relay Server" cmd /k "python server_relay.py 8888"
timeout /t 2 /nobreak >nul

echo [2/3] Launching Client Instance: Alice...
start "Alice - Client" cmd /k "python app_client.py Alice 9001 127.0.0.1 8888 company_secret_2026"
timeout /t 1 /nobreak >nul

echo [3/3] Launching Client Instance: Bob...
start "Bob - Client" cmd /k "python app_client.py Bob 9002 127.0.0.1 8888 company_secret_2026"

echo.
echo ================================================================
echo [SUCCESS] Demo environment successfully initialized.
echo - Admin Governance Dashboard : http://127.0.0.1:8890
echo - Alice Interface            : http://127.0.0.1:9001
echo - Bob Interface              : http://127.0.0.1:9002
echo ================================================================
pause
