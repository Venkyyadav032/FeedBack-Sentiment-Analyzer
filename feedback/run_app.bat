@echo off
title Sentima v1.0 - Feedback Sentiment Analyzer
echo ===================================================
echo   Starting Sentima v1.0 Server & UI
echo ===================================================
cd /d "%~dp0backend"
echo [1/2] Launching FastAPI Backend on http://localhost:8000 ...
start "" http://localhost:8000/
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
pause
