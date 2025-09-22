@echo off
REM ================================================================
REM Augment Account Creator - Windows Batch Script
REM ================================================================
REM This script provides easy access to the Augment registration
REM automation with email cleanup functionality.
REM ================================================================

title Augment Account Creator

REM Set the script directory as working directory
cd /d "%~dp0"

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python and try again.
    pause
    exit /b 1
)

REM Check if virtual environment exists
if not exist "venv" (
    echo Virtual environment not found. Creating one...
    python -m venv venv
    if errorlevel 1 (
        echo ERROR: Failed to create virtual environment
        pause
        exit /b 1
    )
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat
if errorlevel 1 (
    echo ERROR: Failed to activate virtual environment
    pause
    exit /b 1
)

REM Install/update requirements if requirements.txt exists
if exist "requirements.txt" (
    echo Installing/updating requirements...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo WARNING: Some packages may not have installed correctly
    )
)

:MENU
cls
echo ================================================================
echo                 AUGMENT ACCOUNT CREATOR
echo ================================================================
echo.
echo Current Configuration:
python -c "from config import CPANEL_CONFIG, get_current_email_username; print(f'Domain: {CPANEL_CONFIG[\"domain\"]}'); print(f'Current Email Number: {get_current_email_username()}'); print(f'Next Email: {get_current_email_username()}@{CPANEL_CONFIG[\"domain\"]}')" 2>nul
echo.
echo ================================================================
echo                        MAIN MENU
echo ================================================================
echo.
echo 1. Run Augment Registration (with email cleanup)
echo 2. Test Email Manager Functions
echo 3. Manual Email Cleanup
echo 4. View Current Configuration
echo 5. Batch Email Cleanup
echo 6. Process Token Only
echo 7. Exit
echo.
set /p choice="Enter your choice (1-7): "

if "%choice%"=="1" goto RUN_REGISTRATION
if "%choice%"=="2" goto TEST_EMAIL_MANAGER
if "%choice%"=="3" goto MANUAL_CLEANUP
if "%choice%"=="4" goto VIEW_CONFIG
if "%choice%"=="5" goto BATCH_CLEANUP
if "%choice%"=="6" goto PROCESS_TOKEN
if "%choice%"=="7" goto EXIT
goto INVALID_CHOICE

:PROCESS_TOKEN
cls
echo ================================================================
echo                   PROCESS TOKEN ONLY
echo ================================================================
echo.
echo This will process the token from augment_data.json file
echo (if it exists) without running the full registration.
echo.
pause
echo.
echo Processing token...
python augment_token_processor.py
if errorlevel 1 (
    echo.
    echo ERROR: Token processing failed
) else (
    echo.
    echo Token processing completed
)
echo.
pause
goto MENU

:RUN_REGISTRATION
cls
echo ================================================================
echo              RUNNING AUGMENT REGISTRATION
echo ================================================================
echo.
echo Starting Augment registration with email cleanup...
echo This will:
echo 1. Delete the current email account
echo 2. Increment to the next email number
echo 3. Create a new email account
echo 4. Run the registration process
echo.
pause
echo.
python augment_reg.py
if errorlevel 1 (
    echo.
    echo ERROR: Registration process failed
) else (
    echo.
    echo Registration process completed
)
echo.
pause
goto MENU

:TEST_EMAIL_MANAGER
cls
echo ================================================================
echo                 TESTING EMAIL MANAGER
echo ================================================================
echo.
echo Running email manager tests...
echo.
python test_email_manager.py
echo.
pause
goto MENU

:MANUAL_CLEANUP
cls
echo ================================================================
echo                  MANUAL EMAIL CLEANUP
echo ================================================================
echo.
echo This will delete the current email and increment the counter.
echo.
set /p confirm="Are you sure? (y/N): "
if /i not "%confirm%"=="y" goto MENU
echo.
echo Running manual cleanup...
python -c "from email_manager import EmailManager; em = EmailManager(); result = em.delete_and_increment(); print('Success:' if result['success'] else 'Failed:', result.get('message', result.get('error', 'Unknown')))"
echo.
pause
goto MENU

:VIEW_CONFIG
cls
echo ================================================================
echo                 CURRENT CONFIGURATION
echo ================================================================
echo.
python -c "
from config import CPANEL_CONFIG, EMAIL_SERVER_CONFIG, get_current_email_username
from email_manager import EmailManager
print('cPanel Configuration:')
print(f'  Domain: {CPANEL_CONFIG[\"domain\"]}')
print(f'  Host: {CPANEL_CONFIG[\"host\"]}')
print(f'  Current Email Number: {get_current_email_username()}')
print()
em = EmailManager()
current_email = em.get_current_email_address()
print(f'Current Email: {current_email}')
print()
print('Email Server Settings:')
print(f'  IMAP Server: {EMAIL_SERVER_CONFIG[\"imap_server\"]}:{EMAIL_SERVER_CONFIG[\"imap_port\"]}')
print(f'  SMTP Server: {EMAIL_SERVER_CONFIG[\"smtp_server\"]}:{EMAIL_SERVER_CONFIG[\"smtp_port\"]}')
"
echo.
pause
goto MENU

:BATCH_CLEANUP
cls
echo ================================================================
echo                   BATCH EMAIL CLEANUP
echo ================================================================
echo.
echo This will delete multiple email accounts in a range.
echo.
set /p start_num="Enter starting email number: "
set /p end_num="Enter ending email number: "
echo.
echo This will delete emails %start_num% through %end_num%
set /p confirm="Are you sure? (y/N): "
if /i not "%confirm%"=="y" goto MENU
echo.
echo Running batch cleanup...
python -c "
from email_integration_example import cleanup_old_emails_batch
result = cleanup_old_emails_batch(%start_num%, %end_num%)
print(f'Cleanup completed: {result[\"successful_deletions\"]}/{result[\"total_attempted\"]} emails deleted')
"
echo.
pause
goto MENU

:INVALID_CHOICE
echo.
echo Invalid choice. Please enter a number between 1 and 7.
echo.
pause
goto MENU

:EXIT
echo.
echo Deactivating virtual environment...
deactivate
echo.
echo Thank you for using Augment Account Creator!
echo.
pause
exit /b 0

REM ================================================================
REM Error Handling
REM ================================================================
:ERROR
echo.
echo An error occurred. Please check the error message above.
echo.
pause
goto MENU
