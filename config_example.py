# Configuration file for trial account creator (Example Configuration)
# This is an example configuration file with placeholder values for sensitive information

# cPanel Email Creation Settings
CPANEL_CONFIG = {
    'username': '',  # Your cPanel username
    'password': '',  # Your cPanel password
    'domain': '',    # Your domain name
    'host': '',      # Your cPanel host
    'cpanel_port': 2083,
    'webmail_port': 2096,
    'email_quota_mb': 1,  # 1MB quota for each email
    'augment_email_username': 1,  # Current email number to use for Augment registration
    'cursor_email_username': 1    # Current email number to use for Cursor registration
}

# Email Server Settings
EMAIL_SERVER_CONFIG = {
    'imap_server': '',     # Your IMAP server (e.g., 'mail.yourdomain.com')
    'imap_port': 993,
    'pop3_port': 995,
    'smtp_server': '',     # Your SMTP server (e.g., 'mail.yourdomain.com')
    'smtp_port': 465,
    'email_password': '',   # Fixed password for all emails
    'webmail_url_template': ''  # Webmail URL template
}

# Browser Automation Settings
BROWSER_CONFIG = {
    'headless': False,
    'humanize_delay': 2.0,
    'typing_delay_range': (0.05, 0.15),
    'random_delay_range': (1.0, 3.0),
    'page_load_timeout': 60000,
    'network_idle_timeout': 20000
}

# Website URLs and Selectors
WEBSITE_CONFIG = {
    'augment_auth_url': 'https://auth.augmentcode.com/authorize?response_type=code&code_challenge=9xw9rcMT5TTQ7w6Fq3GyCaNkzz6GBKqwLTQiO9JC_4A&client_id=v&state=9ef52362-2002-4057-9a28-a13e9605e10b&prompt=login',

    # Selectors for form elements
    'selectors': {
        'username_input': "//input[@id='username']",
        'code_input': "//input[@id='code']",
        'continue_button': "//button[normalize-space()='Continue']",
        'cloudflare_checkbox': [
            "//div[contains(@class, 'cf-turnstile')]"
        ]
    }
}

# Cursor Website Config
CURSOR_CONFIG = {
    'registration_url': 'https://cursor.com/api/auth/login',  # Main registration/login page for Cursor
    'selectors': {
        'email_input': [
            "input[type='email']",
            "input[name='email']",
            "#email"
        ],
        'submit_button': [
            "button[type='submit']",
            "button:has-text('Continue')",
            "button:has-text('Sign up')"
        ],
        'verification_code_input': [
            "(//input[@class='rt-reset rt-TextFieldInput'])[1]",
            "(//input[@class='rt-reset rt-TextFieldInput'])[2]",
            "(//input[@class='rt-reset rt-TextFieldInput'])[3]",
            "(//input[@class='rt-reset rt-TextFieldInput'])[4]",
            "(//input[@class='rt-reset rt-TextFieldInput'])[5]",
            "(//input[@class='rt-reset rt-TextFieldInput'])[6]"
        ],
        'magic_code_button': [
            "//button[@value='magic-code']"
        ],
    }
}

# Email Verification Settings
VERIFICATION_CONFIG = {
    'sender_email': 'support@augmentcode.com',
    'code_pattern': r'Your verification code is:\s*(\d+)',
    'max_wait_time': 60,  # Maximum time to wait for verification email (seconds)
    'check_interval': 5   # How often to check for new emails (seconds)
}

# Cursor-specific Email Verification Settings
CURSOR_VERIFICATION_CONFIG = {
    'sender_email': 'no-reply@cursor.sh',  # Update with actual Cursor sender email
    'code_pattern': r'Your one-time code is:\s*\n?\s*(\d{6})',  # Pattern for Cursor verification codes
    'max_wait_time': 120,  # Maximum time to wait for verification email (seconds)
    'check_interval': 15    # How often to check for new emails (seconds)
}

# Logging and Debug Settings
DEBUG_CONFIG = {
    'enable_screenshots': True,
    'screenshot_dir': 'screenshots',
    'log_level': 'INFO',
    'save_error_screenshots': True
}
