@echo off
REM Sentinel-V Quick Setup Script for Windows
REM This script automates the initial setup of Sentinel-V

setlocal enabledelayedexpansion

echo.
echo ╔════════════════════════════════════════╗
echo ║  SENTINEL-V SETUP WIZARD               ║
echo ║  Enterprise Security Suite             ║
echo ╚════════════════════════════════════════╝
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python is not installed. Please install Python 3.9 or higher.
    echo    Download from: https://www.python.org/downloads/
    pause
    exit /b 1
)

for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo ✅ Python %PYTHON_VERSION% detected

REM Create virtual environment
if not exist "venv" (
    echo 📦 Creating Python virtual environment...
    python -m venv venv
    if errorlevel 1 (
        echo ❌ Failed to create virtual environment
        pause
        exit /b 1
    )
    echo ✅ Virtual environment created
) else (
    echo ✅ Virtual environment already exists
)

REM Activate virtual environment
echo 🔄 Activating virtual environment...
call venv\Scripts\activate.bat
if errorlevel 1 (
    echo ❌ Failed to activate virtual environment
    pause
    exit /b 1
)

REM Upgrade pip
echo 📦 Upgrading pip...
python -m pip install --upgrade pip setuptools wheel >nul 2>&1
if errorlevel 1 (
    echo ⚠️  Warning: Could not upgrade pip
)

REM Install requirements
echo 📦 Installing dependencies...
pip install -r requirements.txt
if errorlevel 1 (
    echo ❌ Failed to install dependencies
    pause
    exit /b 1
)
echo ✅ Dependencies installed

REM Create data directory
if not exist "data" (
    echo 📁 Creating data directory...
    mkdir data
    echo ✅ Data directory created
)

REM Create .env file if it doesn't exist
if not exist ".env" (
    echo 📝 Creating .env file...
    copy .env.example .env >nul
    echo ✅ .env file created - EDIT WITH YOUR DISCORD WEBHOOK URL
) else (
    echo ✅ .env file already exists
)

REM Create templates directory
if not exist "templates" (
    echo 📁 Creating templates directory...
    mkdir templates
    echo ✅ Templates directory created
)

echo.
echo ╔════════════════════════════════════════╗
echo ║  SETUP COMPLETE!                       ║
echo ╚════════════════════════════════════════╝
echo.
echo 📋 Next steps:
echo    1. Edit .env file with Discord webhook URL (optional):
echo       notepad .env
echo.
echo    2. To use with Docker (recommended):
echo       docker-compose up -d
echo.
echo    3. Start Sentinel-V (Direct):
echo       python main.py
echo.
echo    4. Access the dashboard:
echo       http://localhost:5000
echo.
echo 📖 For more information, see README.md
echo.

REM Ask if user wants to start the system
echo.
set /p start="Do you want to start Sentinel-V now? (y/n): "
if /i "%start%"=="y" (
    python main.py
) else (
    echo.
    echo 👋 To start later, run:
    echo    python main.py
    echo.
)

pause
