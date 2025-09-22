from camoufox.sync_api import Camoufox
import time
import random
import json
import pyperclip

# Import our custom modules
from email_creator import EmailCreator
from email_manager import EmailManager
from code_getter import get_verification_code, update_email_config
from augment_token_processor import make_augment_callback_request
from config import (
    CPANEL_CONFIG, EMAIL_SERVER_CONFIG, BROWSER_CONFIG,
    WEBSITE_CONFIG, VERIFICATION_CONFIG, DEBUG_CONFIG,
    get_email_address
)

def random_delay(min_seconds=None, max_seconds=None):
    """Generate random delay to mimic human behavior"""
    if min_seconds is None or max_seconds is None:
        min_seconds, max_seconds = BROWSER_CONFIG['random_delay_range']
    delay = random.uniform(min_seconds, max_seconds)
    time.sleep(delay)

def save_clipboard_to_json(filename="augment_data.json"):
    """
    Save clipboard content to JSON file

    Args:
        filename: Name of the file to save the JSON data

    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Get clipboard content
        clipboard_content = pyperclip.paste()

        # Try to parse as JSON
        try:
            json_data = json.loads(clipboard_content)

            # Save to file
            with open(filename, 'w') as f:
                json.dump(json_data, f, indent=2)

            print(f"✓ JSON data saved to {filename}")
            return True

        except json.JSONDecodeError as e:
            print(f"✗ Invalid JSON in clipboard: {e}")
            return False

    except Exception as e:
        print(f"✗ Error saving clipboard: {e}")
        return False

def create_new_email():
    """
    Enhanced email creation with cleanup logic.

    This function deletes the current email (if it exists), increments the counter,
    and creates a new email account. This ensures proper cleanup before moving
    to the next email configuration.

    Returns:
        tuple: (email_address, password) if successful, (None, None) if failed
    """
    try:
        print("Creating new email account...")

        # Step 1: Initialize EmailManager for cleanup operations
        email_manager = EmailManager()

        # Step 2: Delete current email and increment counter
        cleanup_result = email_manager.delete_and_increment()

        if not cleanup_result['success']:
            print(f"⚠ Cleanup warning: {cleanup_result.get('error', 'Unknown error')}")
        else:
            print(f"✓ Email cleanup: {cleanup_result['previous_email']} → {cleanup_result['new_email']}")

        # Step 3: Create the new email account
        email_creator = EmailCreator(
            cpanel_user=CPANEL_CONFIG['username'],
            cpanel_pass=CPANEL_CONFIG['password'],
            domain=CPANEL_CONFIG['domain']
        )

        # Get the current email address (should be the new one after increment)
        current_email = email_manager.get_current_email_address()

        # Extract username from email for creation
        email_username = current_email.split('@')[0]

        # Try to create the email account
        result = email_creator.create_email_account(
            email_name=email_username,
            quota=CPANEL_CONFIG['email_quota_mb']
        )

        if result['success']:
            print(f"✓ Email created: {result['email']}")
            return result['email'], result['password']
        else:
            error_msg = str(result['error'])

            # Check if the error is because the email already exists
            if 'already exists' in error_msg.lower():
                # Reuse the email that already exists
                existing_password = email_creator.get_fixed_password()
                print(f"✓ Email exists, reusing: {current_email}")
                return current_email, existing_password
            else:
                # If it's a different error, return None
                print(f"✗ Email creation failed: {error_msg}")
                return None, None

    except Exception as e:
        print(f"✗ Email creation error: {e}")
        return None, None

def extract_portal_url(page):
    """
    Navigate to subscription page and extract the 'View usage' portal URL

    Args:
        page: Playwright page object

    Returns:
        str: Portal URL or None if not found
    """
    try:
        # Navigate to the subscription page
        subscription_url = "https://app.augmentcode.com/account/subscription"
        page.goto(subscription_url)

        # Wait for page to load
        page.wait_for_load_state("networkidle", timeout=BROWSER_CONFIG['network_idle_timeout'])

        # Wait for user to complete card details entry
        print("⚠ Please enter your card details on the subscription page.")
        print("⚠ Once you have completed entering your card details, press ENTER to continue...")
        input("Press ENTER when card details are entered and you're ready to continue: ")

        # Find the 'View usage' link
        try:
            # Try to find the link using the XPath selector
            view_usage_link = page.locator("//a[normalize-space()='View usage']").first

            if view_usage_link.is_visible():
                # Get the href attribute
                portal_url = view_usage_link.get_attribute('href')
                if portal_url:
                    print(f"✓ Portal URL extracted: {portal_url}")
                    return portal_url

            return None

        except Exception as e:
            print(f"⚠ Portal URL extraction failed: {e}")
            return None

    except Exception as e:
        print(f"✗ Portal URL error: {e}")
        return None

def wait_for_verification_code(email_address, max_wait_time=None):
    """Wait for and retrieve verification code from email"""
    if max_wait_time is None:
        max_wait_time = VERIFICATION_CONFIG['max_wait_time']

    print(f"Waiting for verification code...")

    start_time = time.time()
    while time.time() - start_time < max_wait_time:
        try:
            # Update the code_getter to use the current email
            code = get_verification_code()
            if code:
                print(f"✓ Verification code received: {code}")
                return code

            time.sleep(VERIFICATION_CONFIG['check_interval'])

        except Exception as e:
            print(f"⚠ Code check error: {e}")
            time.sleep(VERIFICATION_CONFIG['check_interval'])

    print("✗ Verification code timeout")
    return None

def human_like_typing(page, selectors_to_try, text, typing_delay_range=None):
    """
    Type text with human-like delays between keystrokes

    Args:
        page: Playwright page object
        selectors_to_try: List of selectors to try (or single selector string)
        text: Text to type
        typing_delay_range: Tuple of (min, max) delay between keystrokes
    """
    try:
        if typing_delay_range is None:
            typing_delay_range = BROWSER_CONFIG['typing_delay_range']

        if isinstance(selectors_to_try, str):
            selectors_to_try = [selectors_to_try]

        element = None
        successful_selector = None

        # Try each selector until one works
        for sel in selectors_to_try:
            try:
                element = page.locator(sel).first
                if element.is_visible():
                    successful_selector = sel
                    break
            except Exception:
                continue

        if not element:
            print(f"✗ Input field not found")
            return False

        # Scroll element into view
        element.scroll_into_view_if_needed()
        random_delay(0.3, 0.7)

        # Click to focus the element
        element.click()
        random_delay(0.5, 1.0)

        # Clear any existing text using keyboard shortcuts
        page.keyboard.press("Control+a")  # Select all
        random_delay(0.1, 0.2)
        page.keyboard.press("Delete")  # Delete selected text
        random_delay(0.2, 0.4)

        # Type each character with random delays
        for i, char in enumerate(text):
            page.keyboard.type(char)
            delay = random.uniform(*typing_delay_range)
            time.sleep(delay)

        # Verify the text was entered
        try:
            current_value = element.input_value()
            return current_value == text
        except:
            # Some elements might not have input_value method
            return True

    except Exception as e:
        print(f"✗ Typing error: {e}")
        return False

def navigate_to_fooe():
    """
    Complete registration flow: create email, navigate to website, enter email, get verification code, submit
    """
    # Step 1: Create a new email account
    email_address, email_password = create_new_email()
    if not email_address:
        print("✗ Email creation failed. Exiting.")
        return False

    print(f"✓ Using email: {email_address}")

    # Update the code_getter to use this email
    update_email_config(email_address, email_password)

    # Step 2: Navigate to website and enter email
    # Launch Camoufox with advanced stealth configuration
    with Camoufox(
        headless=BROWSER_CONFIG['headless'],
        humanize=BROWSER_CONFIG['humanize_delay'],
        geoip=True,              # Auto-detect geolocation based on IP
        os=["windows", "macos"],  # Randomly choose between Windows/macOS
        locale="en-US",          # Set locale to US English
        disable_coop=False,       # Allows clicking elements in cross-origin iframes
        block_webrtc=True,       # Block WebRTC to prevent IP leaks
        enable_cache=False,      # Disable cache for better stealth
        main_world_eval=True,    # Allow main world script injection
    ) as browser:
        # Create a new page with additional stealth settings
        page = browser.new_page()

        # Set realistic viewport if not using fixed window size
        # page.set_viewport_size({"width": 1366, "height": 768})

        # Set additional headers to appear more human-like
        page.set_extra_http_headers({
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate, br",
            "DNT": "1",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
        })

        try:
            print("✓ Starting registration process...")

            # Random delay before starting
            random_delay(1, 3)

            # Navigate to the website
            print("✓ Navigating to Augment...")
            page.goto(WEBSITE_CONFIG['augment_auth_url'], wait_until="domcontentloaded")

            # Wait for page to fully load with random delay
            try:
                page.wait_for_load_state("networkidle", timeout=BROWSER_CONFIG['page_load_timeout'])
            except Exception as e:
                print(f"⚠ Page load timeout: {e}")

            random_delay(1, 3)

            # Simulate human-like behavior: scroll a bit to "look around"
            page.mouse.wheel(0, random.randint(100, 300))
            random_delay(1, 2)
            page.mouse.wheel(0, random.randint(-150, -50))
            random_delay(1, 2)

            # Move mouse around randomly before interacting
            viewport_size = page.viewport_size
            if viewport_size is not None:
                for _ in range(2):
                    x = random.randint(100, viewport_size["width"] - 100)
                    y = random.randint(100, viewport_size["height"] - 100)
                    page.mouse.move(x, y)
                    random_delay(0.5, 1.5)
            else:
                # Fallback to default viewport size if viewport_size is None
                for _ in range(2):
                    x = random.randint(100, 1200)  # Default width assumption
                    y = random.randint(100, 700)   # Default height assumption
                    page.mouse.move(x, y)
                    random_delay(0.5, 1.5)

            # Wait for page to be fully interactive
            try:
                page.wait_for_load_state("domcontentloaded", timeout=30000)
            except Exception as e:
                print(f"⚠ DOM load timeout: {e}")

            random_delay(2, 3)

            # Define selectors to try for the username field
            username_selectors = WEBSITE_CONFIG['selectors']['username_input']

            # Try to type in username field
            print("✓ Entering email address...")
            success = human_like_typing(page, username_selectors, email_address)

            if success:
                print("✓ Email entered successfully")

                # Random delay before clicking Continue
                random_delay(1, 2)

                # Click the Cloudflare checkbox first
                print("✓ Handling Cloudflare verification...")
                cloudflare_selectors = WEBSITE_CONFIG['selectors']['cloudflare_checkbox']

                cloudflare_clicked = False
                for selector in cloudflare_selectors:
                    try:
                        cf_element = page.locator(selector).first
                        if cf_element.is_visible():
                            # Scroll into view and click
                            cf_element.scroll_into_view_if_needed()
                            random_delay(1, 2)

                            # Human-like click on the checkbox
                            cf_element.click()
                            print("✓ Cloudflare checkbox clicked")
                            cloudflare_clicked = True

                            # Wait for Cloudflare verification
                            random_delay(3, 5)
                            break
                    except Exception:
                        continue

                if not cloudflare_clicked:
                    print("⚠ Cloudflare checkbox not found")

                # Now click the Continue button
                print("✓ Clicking Continue...")
                continue_selectors = [
                    WEBSITE_CONFIG['selectors']['continue_button'],
                    "button:has-text('Continue')",
                    "input[value='Continue']",
                    "button[type='submit']"
                ]

                continue_clicked = False
                for selector in continue_selectors:
                    try:
                        continue_btn = page.locator(selector).first
                        if continue_btn.is_visible():
                            # Scroll into view and click
                            continue_btn.scroll_into_view_if_needed()
                            random_delay(0.5, 1)

                            # Human-like click
                            continue_btn.click()
                            print("✓ Continue button clicked")
                            continue_clicked = True
                            break
                    except Exception:
                        continue

                if not continue_clicked:
                    print("✗ Continue button not found")
                    return False
                else:
                    # Wait for any navigation or loading after clicking Continue
                    random_delay(2, 4)
                    try:
                        page.wait_for_load_state("networkidle", timeout=BROWSER_CONFIG['network_idle_timeout'])
                    except:
                        pass

                    # Step 3: Wait for verification code
                    verification_code = wait_for_verification_code(email_address)

                    if not verification_code:
                        print("✗ Verification code not received")
                        return False

                    # Step 4: Enter verification code
                    print("✓ Entering verification code...")
                    code_input_selector = WEBSITE_CONFIG['selectors']['code_input']

                    code_success = human_like_typing(page, code_input_selector, verification_code)

                    if code_success:
                        print("✓ Verification code entered")

                        # Step 5: Click Continue again to submit the code
                        random_delay(1, 2)
                        print("✓ Submitting verification code...")

                        final_continue_clicked = False
                        for selector in continue_selectors:
                            try:
                                final_continue_btn = page.locator(selector).first
                                if final_continue_btn.is_visible():
                                    final_continue_btn.scroll_into_view_if_needed()
                                    random_delay(0.5, 1)
                                    final_continue_btn.click()
                                    print("✓ Final Continue clicked")
                                    final_continue_clicked = True
                                    break
                            except Exception:
                                continue

                        if final_continue_clicked:
                            print("✓ Registration completed!")
                            random_delay(2, 4)
                            try:
                                page.wait_for_load_state("networkidle", timeout=BROWSER_CONFIG['network_idle_timeout'])
                            except:
                                pass

                            # Step 6: Wait for and click the copy button
                            print("✓ Waiting for copy button...")
                            copy_button_clicked = False
                            max_wait_attempts = 30  # Wait up to 30 attempts (about 30 seconds)

                            for attempt in range(max_wait_attempts):
                                try:
                                    copy_button = page.locator("//*[@id='copyButton']").first
                                    if copy_button.is_visible():
                                        # Scroll into view and click
                                        copy_button.scroll_into_view_if_needed()
                                        random_delay(0.5, 1)
                                        copy_button.click()
                                        print("✓ Copy button clicked")
                                        copy_button_clicked = True
                                        break

                                except Exception:
                                    pass

                                # Wait 1 second before next attempt
                                time.sleep(1)

                            if copy_button_clicked:
                                print("✓ Registration fully completed!")

                                # Wait a moment for clipboard to be populated
                                random_delay(1, 2)

                                # Save clipboard content to JSON file
                                print("✓ Saving clipboard data...")
                                if save_clipboard_to_json():
                                    # Extract portal URL from subscription page
                                    portal_url = extract_portal_url(page)

                                    # Process the token using the saved JSON data
                                    print("✓ Processing token...")
                                    try:
                                        response = make_augment_callback_request()
                                        if response:
                                            print("✓ Token processed successfully!")
                                        else:
                                            print("⚠ Token processing failed")
                                    except Exception as e:
                                        print(f"⚠ Token processing error: {e}")

                                return True
                            else:
                                print("⚠ Copy button timeout")
                                return True  # Still consider it successful since registration worked
                        else:
                            print("✗ Final Continue button not found")
                            return False
                    else:
                        print("✗ Failed to enter verification code")
                        return False

            else:
                print("✗ Could not enter email address")
                return False

        except Exception as e:
            print(f"✗ Registration error: {e}")
            # Take a screenshot for debugging if needed
            if DEBUG_CONFIG['save_error_screenshots']:
                try:
                    page.screenshot(path="error_screenshot.png")
                    print("✓ Error screenshot saved")
                except:
                    pass
            return False

        finally:
            # Random delay before closing (human-like)
            random_delay(1, 2)
            browser.close()

if __name__ == "__main__":
    success = navigate_to_fooe()
    if success:
        print("✓ Registration completed successfully!")
    else:
        print("✗ Registration failed!")
