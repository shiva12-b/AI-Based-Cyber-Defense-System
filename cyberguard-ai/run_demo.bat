@echo off
setlocal
if not exist .venv py -3.13 -m venv .venv
call .venv\Scripts\activate
python -m pip install -r requirements.txt
if not exist .env copy .env.example .env
start "CyberBank Server" cmd /k "call .venv\Scripts\activate && uvicorn bank_server.main:app --host 0.0.0.0 --port 9000"
timeout /t 2 >nul
start "CyberGuard Gateway" cmd /k "call .venv\Scripts\activate && uvicorn gateway.main:app --host 0.0.0.0 --port 8000"
timeout /t 3 >nul
start http://127.0.0.1:8000
