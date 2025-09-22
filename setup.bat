@echo off
REM ================================================================
REM Setup Script for Augment Account Creator
REM ================================================================
REM This script sets up the environment for the first time
REM ================================================================

title Augment Account Creator - Setup

echo ================================================================
echo           AUGMENT ACCOUNT CREATOR - SETUP
echo ================================================================
echo.
echo This script will set up your environment for the first time.
echo.

REM Set the script directory as working directory
cd /d "%~dp0"

REM Check if Python is installed
echo Checking Python installation...
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo.
    echo Please install Python 3.8 or later from https://python.org
    echo Make sure to check "Add Python to PATH" during installation.
    echo.
    pause
    exit /b 1
)

python --version
echo ✓ Python is installed
echo.

REM Create virtual environment
if exist "venv" (
    echo Virtual environment already exists.
    set /p recreate="Recreate virtual environment? (y/N): "
    if /i "%recreate%"=="y" (
        echo Removing existing virtual environment...
        rmdir /s /q venv
    ) else (
        goto ACTIVATE_VENV
    )
)

echo Creating virtual environment...
python -m venv venv
if errorlevel 1 (
    echo ERROR: Failed to create virtual environment
    echo.
    pause
    exit /b 1
)
echo ✓ Virtual environment created
echo.

:ACTIVATE_VENV
echo Activating virtual environment...
call venv\Scripts\activate.bat
if errorlevel 1 (
    echo ERROR: Failed to activate virtual environment
    pause
    exit /b 1
)
echo ✓ Virtual environment activated
echo.

REM Upgrade pip
echo Upgrading pip...
python -m pip install --upgrade pip
echo.

REM Install requirements
echo Installing required packages...
if exist "requirements.txt" (
    pip install -r requirements.txt
    if errorlevel 1 (
        echo WARNING: Some packages may not have installed correctly
        echo You may need to install them manually.
    ) else (
        echo ✓ All packages installed successfully
    )
) else (
    echo Installing core packages manually...
    pip install requests camoufox pyperclip colorama
)
echo.

REM Check configuration
echo Checking configuration...
python -c "
try:
    from config import CPANEL_CONFIG, EMAIL_SERVER_CONFIG
    print('✓ Configuration file loaded successfully')
    print(f'Domain: {CPANEL_CONFIG[\"domain\"]}')
    print(f'Current email number: {CPANEL_CONFIG[\"augment_email_username\"]}')
except Exception as e:
    print(f'✗ Configuration error: {e}')
    print('Please check your config.py file')
" 2>nul
echo.

REM Test email manager
echo Testing email manager...
python -c "
try:
    from email_manager import EmailManager
    em = EmailManager()
    current_email = em.get_current_email_address()
    print(f'✓ Email manager working. Current email: {current_email}')
except Exception as e:
    print(f'✗ Email manager error: {e}')
" 2>nul
echo.

echo ================================================================
echo                        SETUP COMPLETE
echo ================================================================
echo.
echo Your Augment Account Creator is now set up and ready to use!
echo.
echo Available scripts:
echo   run_augment_registration.bat - Main registration script with menu
echo   email_utils.bat             - Quick email management utilities
echo   test_email_manager.py       - Test email functionality
echo   augment_token_processor.py  - Process authentication tokens
echo.
echo To get started, run: run_augment_registration.bat
echo.
echo Configuration:
python -c "
from config import CPANEL_CONFIG, get_current_email_username
print(f'  Domain: {CPANEL_CONFIG[\"domain\"]}')
print(f'  Current Email: {get_current_email_username()}@{CPANEL_CONFIG[\"domain\"]}')
print(f'  cPanel Host: {CPANEL_CONFIG[\"host\"]}')
" 2>nul
echo.
echo ================================================================
echo.
pause

REM Deactivate virtual environment
deactivate
