@echo off
REM ================================================================
REM Email Management Utilities - Windows Batch Script
REM ================================================================
REM Quick utilities for email management tasks
REM ================================================================

title Email Management Utilities

REM Set the script directory as working directory
cd /d "%~dp0"

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    pause
    exit /b 1
)

REM Activate virtual environment if it exists
if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
)

:MENU
cls
echo ================================================================
echo                EMAIL MANAGEMENT UTILITIES
echo ================================================================
echo.
echo Quick Email Operations:
echo.
echo 1. Show Current Email Status
echo 2. Delete Current Email Only
echo 3. Increment Counter Only
echo 4. Delete and Increment
echo 5. Create New Email
echo 6. Test Email Connection
echo 7. Reset Email Counter
echo 8. Process Token
echo 9. Exit
echo.
set /p choice="Enter your choice (1-9): "

if "%choice%"=="1" goto SHOW_STATUS
if "%choice%"=="2" goto DELETE_ONLY
if "%choice%"=="3" goto INCREMENT_ONLY
if "%choice%"=="4" goto DELETE_INCREMENT
if "%choice%"=="5" goto CREATE_EMAIL
if "%choice%"=="6" goto TEST_CONNECTION
if "%choice%"=="7" goto RESET_COUNTER
if "%choice%"=="8" goto PROCESS_TOKEN
if "%choice%"=="9" goto EXIT
goto INVALID_CHOICE

:PROCESS_TOKEN
cls
echo ================================================================
echo                     PROCESS TOKEN
echo ================================================================
echo.
echo This will process the authentication token from augment_data.json
echo.
if exist "augment_data.json" (
    echo Found augment_data.json file
    set /p confirm="Process the token? (y/N): "
    if /i not "%confirm%"=="y" goto MENU
    echo.
    python augment_token_processor.py
) else (
    echo augment_data.json file not found
    echo Please run the registration process first
)
echo.
pause
goto MENU

:SHOW_STATUS
cls
echo ================================================================
echo                    CURRENT EMAIL STATUS
echo ================================================================
echo.
python -c "
from config import get_current_email_username, CPANEL_CONFIG
from email_manager import EmailManager
import sys

try:
    current_num = get_current_email_username()
    em = EmailManager()
    current_email = em.get_current_email_address()
    
    print(f'Current Email Number: {current_num}')
    print(f'Current Email Address: {current_email}')
    print(f'Domain: {CPANEL_CONFIG[\"domain\"]}')
    print(f'Email Quota: {CPANEL_CONFIG[\"email_quota_mb\"]} MB')
    print()
    
    # Try to check if email exists (this might fail, that's ok)
    print('Checking email status...')
    deletion_result = em.delete_current_email()
    if 'does not exist' in str(deletion_result.get('error', '')).lower():
        print('Status: Email does not exist')
    elif deletion_result['success']:
        print('Status: Email exists (was just deleted for testing)')
        # Recreate it since we just deleted it for testing
        from email_creator import EmailCreator
        ec = EmailCreator(CPANEL_CONFIG['username'], CPANEL_CONFIG['password'], CPANEL_CONFIG['domain'])
        email_username = current_email.split('@')[0]
        create_result = ec.create_email_account(email_name=email_username, quota=CPANEL_CONFIG['email_quota_mb'])
        if create_result['success']:
            print('Status: Email recreated after test deletion')
    else:
        print('Status: Unknown (could not verify)')
        
except Exception as e:
    print(f'Error checking status: {e}')
    sys.exit(1)
"
echo.
pause
goto MENU

:DELETE_ONLY
cls
echo ================================================================
echo                    DELETE CURRENT EMAIL
echo ================================================================
echo.
python -c "
from email_manager import EmailManager
em = EmailManager()
current_email = em.get_current_email_address()
print(f'Current email: {current_email}')
"
echo.
set /p confirm="Delete this email? (y/N): "
if /i not "%confirm%"=="y" goto MENU
echo.
python -c "
from email_manager import EmailManager
em = EmailManager()
result = em.delete_current_email()
if result['success']:
    print(f'✓ Email deleted: {result[\"email\"]}')
else:
    print(f'✗ Failed to delete: {result[\"error\"]}')
"
echo.
pause
goto MENU

:INCREMENT_ONLY
cls
echo ================================================================
echo                   INCREMENT COUNTER ONLY
echo ================================================================
echo.
python -c "
from email_manager import EmailManager
em = EmailManager()
current_email = em.get_current_email_address()
print(f'Current email: {current_email}')
"
echo.
set /p confirm="Increment to next email number? (y/N): "
if /i not "%confirm%"=="y" goto MENU
echo.
python -c "
from email_manager import EmailManager
em = EmailManager()
result = em.increment_email_counter()
if result['success']:
    print(f'✓ Counter incremented: {result[\"previous_number\"]} → {result[\"new_number\"]}')
    print(f'New email will be: {result[\"new_email\"]}')
else:
    print(f'✗ Failed to increment: {result[\"error\"]}')
"
echo.
pause
goto MENU

:DELETE_INCREMENT
cls
echo ================================================================
echo                 DELETE AND INCREMENT
echo ================================================================
echo.
python -c "
from email_manager import EmailManager
em = EmailManager()
current_email = em.get_current_email_address()
print(f'Current email: {current_email}')
"
echo.
echo This will delete the current email and move to the next number.
set /p confirm="Continue? (y/N): "
if /i not "%confirm%"=="y" goto MENU
echo.
python -c "
from email_manager import EmailManager
em = EmailManager()
result = em.delete_and_increment()
if result['success']:
    print(f'✓ Process completed successfully')
    print(f'Previous email: {result[\"previous_email\"]}')
    print(f'New email: {result[\"new_email\"]}')
else:
    print(f'✗ Process failed: {result[\"error\"]}')
"
echo.
pause
goto MENU

:CREATE_EMAIL
cls
echo ================================================================
echo                     CREATE NEW EMAIL
echo ================================================================
echo.
python -c "
from email_manager import EmailManager
from email_creator import EmailCreator
from config import CPANEL_CONFIG

em = EmailManager()
current_email = em.get_current_email_address()
print(f'Will create email: {current_email}')
"
echo.
set /p confirm="Create this email? (y/N): "
if /i not "%confirm%"=="y" goto MENU
echo.
python -c "
from email_manager import EmailManager
from email_creator import EmailCreator
from config import CPANEL_CONFIG

try:
    em = EmailManager()
    current_email = em.get_current_email_address()
    email_username = current_email.split('@')[0]
    
    ec = EmailCreator(CPANEL_CONFIG['username'], CPANEL_CONFIG['password'], CPANEL_CONFIG['domain'])
    result = ec.create_email_account(email_name=email_username, quota=CPANEL_CONFIG['email_quota_mb'])
    
    if result['success']:
        print(f'✓ Email created: {result[\"email\"]}')
        print(f'Password: {result[\"password\"]}')
    else:
        error_msg = str(result['error'])
        if 'already exists' in error_msg.lower():
            print(f'✓ Email already exists: {current_email}')
            print(f'Password: {ec.get_fixed_password()}')
        else:
            print(f'✗ Failed to create: {result[\"error\"]}')
except Exception as e:
    print(f'Error: {e}')
"
echo.
pause
goto MENU

:TEST_CONNECTION
cls
echo ================================================================
echo                   TEST EMAIL CONNECTION
echo ================================================================
echo.
echo Running email connection tests...
echo.
python test_email_manager.py
echo.
pause
goto MENU

:RESET_COUNTER
cls
echo ================================================================
echo                    RESET EMAIL COUNTER
echo ================================================================
echo.
echo WARNING: This will reset the email counter to a specific number.
echo.
set /p new_number="Enter new email number: "
echo.
echo This will set the email counter to %new_number%
set /p confirm="Are you sure? (y/N): "
if /i not "%confirm%"=="y" goto MENU
echo.
python -c "
from config import update_email_username, get_current_email_username
try:
    old_number = get_current_email_username()
    update_email_username(%new_number%)
    print(f'✓ Email counter reset: {old_number} → %new_number%')
except Exception as e:
    print(f'✗ Failed to reset counter: {e}')
"
echo.
pause
goto MENU

:INVALID_CHOICE
echo.
echo Invalid choice. Please enter a number between 1 and 9.
echo.
pause
goto MENU

:EXIT
echo.
echo Goodbye!
pause
exit /b 0
