@echo off
echo ========================================================
echo   KHOI CHAY MO PHONG 2 KY SU (ALICE VA BOB)
echo ========================================================
start "Relay Server" cmd /k "python server_relay.py 8888"
timeout /t 2 /nobreak >nul
start "Client Alice" cmd /k "python app_client.py Alice 9001"
timeout /t 2 /nobreak >nul
start "Client Bob" cmd /k "python app_client.py Bob 9002"
echo He thong da khoi chay! Trinh duyet cua 2 ky su se tu dong mo len.
pause
