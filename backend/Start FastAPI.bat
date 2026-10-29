@echo off
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  echo Could not find the backend virtual environment at .venv\Scripts\python.exe
  pause
  exit /b 1
)
".venv\Scripts\python.exe" -m uvicorn main:app --reload --host 127.0.0.1 --port 8000
echo.
echo FastAPI has stopped. Press any key to close this window.
pause >nul
