@echo off
setlocal
echo ==========================================
echo    Web UI Agent Backend Starter
echo ==========================================

REM 检查虚拟环境是否存在
if not exist "venv_new\Scripts\python.exe" (
    echo [ERROR] Virtual environment 'venv_new' not found.
    echo Please ensure you have followed the setup instructions.
    pause
    exit /b 1
)

echo [INFO] Starting Flask server using Python 3.12...
echo [INFO] API will be available at http://127.0.0.1:5000
echo.

.\venv_new\Scripts\python.exe server.py

pause
