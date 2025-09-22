import imaplib
import smtplib
import email
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import os
import re

# Import config
from config import EMAIL_SERVER_CONFIG, VERIFICATION_CONFIG

# Email server configuration - will be updated dynamically
EMAIL_CONFIG = {
    'imap_server': EMAIL_SERVER_CONFIG['imap_server'],
    'imap_port': EMAIL_SERVER_CONFIG['imap_port'],
    'pop3_port': EMAIL_SERVER_CONFIG['pop3_port'],
    'smtp_server': EMAIL_SERVER_CONFIG['smtp_server'],
    'smtp_port': EMAIL_SERVER_CONFIG['smtp_port'],
    'username': '1@safenetaibd.com',  # Default, will be updated
    'password': EMAIL_SERVER_CONFIG['email_password']
}

def update_email_config(email_address, password=None):
    """Update the email configuration for the current session"""
    global EMAIL_CONFIG
    EMAIL_CONFIG['username'] = email_address
    if password:
        EMAIL_CONFIG['password'] = password
    print(f"Updated email config to use: {email_address}")

def get_verification_code():
    """Get the verification code from the last email from support@augmentcode.com"""
    try:
        # Connect to IMAP server using configuration
        mail = imaplib.IMAP4_SSL(EMAIL_CONFIG['imap_server'], EMAIL_CONFIG['imap_port'])
        mail.login(EMAIL_CONFIG['username'], EMAIL_CONFIG['password'])
        mail.select("inbox")

        # Search for emails from support@augmentcode.com
        status, messages = mail.search(None, f'FROM "{VERIFICATION_CONFIG["sender_email"]}"')

        # Check if search was successful
        if status != "OK":
            return None

        # Check if there are any messages from this sender
        if not messages[0]:
            return None

        # Get the list of message numbers and find the last one (highest number)
        message_nums = messages[0].split()
        if not message_nums:
            return None

        # Get the last (most recent) email number
        last_email_num = message_nums[-1]

        # Fetch the last email data
        status, data = mail.fetch(last_email_num, "(RFC822)")

        # Check if fetch was successful
        if status != "OK" or not data:
            return None

        # Extract email content
        if data[0] and len(data[0]) > 1 and data[0][1]:
            raw_email = data[0][1]

            # Handle both bytes and string data
            if isinstance(raw_email, bytes):
                email_content = raw_email.decode('utf-8', errors='ignore')
            else:
                email_content = str(raw_email)

            # Parse email
            email_message = email.message_from_string(email_content)

            # Get email body
            body = ""
            if email_message.is_multipart():
                for part in email_message.walk():
                    if part.get_content_type() == "text/plain":
                        body = part.get_payload(decode=True)
                        if isinstance(body, bytes):
                            body = body.decode('utf-8', errors='ignore')
                        break
            else:
                body = email_message.get_payload(decode=True)
                if isinstance(body, bytes):
                    body = body.decode('utf-8', errors='ignore')

            # Extract verification code using regex
            if body:
                # Ensure body is a string for regex search
                if not isinstance(body, str):
                    body = str(body)
                # Look for verification code pattern from config
                match = re.search(VERIFICATION_CONFIG['code_pattern'], body)
                if match:
                    verification_code = match.group(1)
                    mail.close()
                    mail.logout()
                    return verification_code

        # Close connection
        mail.close()
        mail.logout()
        return None

    except Exception as e:
        return None

def send_email(to_email, subject, body, attachment_path=None):
    """Send an email using SMTP"""
    try:
        # Create message
        msg = MIMEMultipart()
        msg['From'] = EMAIL_CONFIG['username']
        msg['To'] = to_email
        msg['Subject'] = subject

        # Add body to email
        msg.attach(MIMEText(body, 'plain'))

        # Add attachment if provided
        if attachment_path and os.path.exists(attachment_path):
            with open(attachment_path, "rb") as attachment:
                part = MIMEBase('application', 'octet-stream')
                part.set_payload(attachment.read())

            encoders.encode_base64(part)
            part.add_header(
                'Content-Disposition',
                f'attachment; filename= {os.path.basename(attachment_path)}'
            )
            msg.attach(part)

        # Connect to SMTP server
        server = smtplib.SMTP_SSL(EMAIL_CONFIG['smtp_server'], EMAIL_CONFIG['smtp_port'])
        server.login(EMAIL_CONFIG['username'], EMAIL_CONFIG['password'])

        # Send email
        text = msg.as_string()
        server.sendmail(EMAIL_CONFIG['username'], to_email, text)
        server.quit()

        print(f"Email sent successfully to {to_email}")
        return True

    except Exception as e:
        print(f"Error sending email: {e}")
        return False


def test_email_connection():
    """Test both IMAP and SMTP connections"""
    print("Testing email connections...")

    # Test IMAP connection
    try:
        mail = imaplib.IMAP4_SSL(EMAIL_CONFIG['imap_server'], EMAIL_CONFIG['imap_port'])
        mail.login(EMAIL_CONFIG['username'], EMAIL_CONFIG['password'])
        mail.select("inbox")
        mail.close()
        mail.logout()
        print("✓ IMAP connection successful")
    except Exception as e:
        print(f"✗ IMAP connection failed: {e}")

    # Test SMTP connection
    try:
        server = smtplib.SMTP_SSL(EMAIL_CONFIG['smtp_server'], EMAIL_CONFIG['smtp_port'])
        server.login(EMAIL_CONFIG['username'], EMAIL_CONFIG['password'])
        server.quit()
        print("✓ SMTP connection successful")
    except Exception as e:
        print(f"✗ SMTP connection failed: {e}")


if __name__ == "__main__":
    # Get verification code
    code = get_verification_code()
    if code:
        print(code)
    else:
        print("No verification code found")
