import asyncio
import time
import random
from browserforge.fingerprints import Screen
from camoufox.async_api import AsyncCamoufox

# Import our custom modules and configurations
from code_getter import get_verification_code, update_email_config
from config import (
    BROWSER_CONFIG,
    DEBUG_CONFIG,
    CURSOR_CONFIG,  # Import the new config for Cursor
    VERIFICATION_CONFIG,
    CURSOR_VERIFICATION_CONFIG,
    get_current_cursor_email_username,
    update_cursor_email_username,
    get_email_address
)
 
 
def random_delay(min_seconds=None, max_seconds=None):
    """Generate random delay to mimic human behavior"""
    if min_seconds is None or max_seconds is None:
        min_seconds, max_seconds = BROWSER_CONFIG['random_delay_range']
    delay = random.uniform(min_seconds, max_seconds)
    time.sleep(delay)


async def handle_cloudflare_bypass(page):
    """Handle Cloudflare verification using frame-based coordinate clicking"""
    print("Starting Cloudflare frame-based bypass...")
    
    try:
        # Wait and check for Cloudflare frames for up to 15 seconds
        for attempt in range(15):
            await asyncio.sleep(1)
            print(f"Checking for Cloudflare frames... attempt {attempt + 1}/15")
            
            for frame in page.frames:
                if frame.url.startswith('https://challenges.cloudflare.com'):
                    print(f"Found Cloudflare frame: {frame.url}")
                    
                    try:
                        frame_element = await frame.frame_element()
                        bounding_box = await frame_element.bounding_box()
                        
                        if bounding_box:
                            coord_x = bounding_box['x']
                            coord_y = bounding_box['y']
                            width = bounding_box['width']
                            height = bounding_box['height']
                            
                            # Calculate checkbox position (left side, middle height)
                            checkbox_x = coord_x + width / 9
                            checkbox_y = coord_y + height / 2
                            
                            print(f"Clicking Cloudflare checkbox at coordinates: ({checkbox_x}, {checkbox_y})")
                            await page.mouse.click(x=checkbox_x, y=checkbox_y)
                            
                            print("✓ Successfully clicked Cloudflare checkbox!")
                            # Wait for verification to complete
                            await asyncio.sleep(3)
                            return True
                            
                    except Exception as e:
                        print(f"Error handling Cloudflare frame: {e}")
                        continue
        
        print("⚠ No Cloudflare frames found within timeout")
        return False
        
    except Exception as e:
        print(f"Error in Cloudflare bypass: {e}")
        return False


async def get_cursor_verification_code():
    """Get the verification code from the last email from Cursor sender"""
    try:
        import imaplib
        import email
        import re
        from code_getter import EMAIL_CONFIG
        
        # Connect to IMAP server using configuration
        mail = imaplib.IMAP4_SSL(EMAIL_CONFIG['imap_server'], EMAIL_CONFIG['imap_port'])
        mail.login(EMAIL_CONFIG['username'], EMAIL_CONFIG['password'])
        mail.select("inbox")

        # Search for emails from Cursor sender
        status, messages = mail.search(None, f'FROM "{CURSOR_VERIFICATION_CONFIG["sender_email"]}"')

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
                # Look for verification code pattern from Cursor config
                match = re.search(CURSOR_VERIFICATION_CONFIG['code_pattern'], body, re.IGNORECASE)
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
        print(f"Error getting Cursor verification code: {e}")
        return None


async def wait_for_verification_code(email_address, max_wait_time=None):
    """Wait for and retrieve verification code from email for Cursor registration"""
    if max_wait_time is None:
        max_wait_time = CURSOR_VERIFICATION_CONFIG['max_wait_time']

    print(f"Waiting for verification code for {email_address}...")

    start_time = time.time()
    while time.time() - start_time < max_wait_time:
        try:
            # Use Cursor-specific verification code getter
            code = await get_cursor_verification_code()
            if code:
                print(f"✓ Verification code received: {code}")
                return code

            print("No verification code yet, waiting...")
            await asyncio.sleep(CURSOR_VERIFICATION_CONFIG['check_interval'])

        except Exception as e:
            print(f"Error checking for verification code: {e}")
            await asyncio.sleep(CURSOR_VERIFICATION_CONFIG['check_interval'])

    print("Timeout waiting for verification code")
    return None


def create_cursor_email():
    """
    Create a new email account specifically for Cursor registration.
    Uses cursor_email_username counter instead of augment_email_username.
    
    Returns:
        tuple: (email_address, password) if successful, (None, None) if failed
    """
    try:
        print("Creating new email account for Cursor registration...")
        
        # Import here to avoid circular imports
        from email_creator import EmailCreator
        from email_manager import EmailManager
        from config import CPANEL_CONFIG
        
        # Get current cursor email username
        current_username = get_current_cursor_email_username()
        print(f"Using cursor email username: {current_username}")
        
        # Generate email address
        email_address = get_email_address(current_username)
        print(f"Creating email: {email_address}")
        
        # Create email creator instance
        email_creator = EmailCreator(
            cpanel_user=CPANEL_CONFIG['username'],
            cpanel_pass=CPANEL_CONFIG['password'],
            domain=CPANEL_CONFIG['domain']
        )
        
        # Try to create the email account
        result = email_creator.create_email_account(
            email_name=str(current_username),
            quota=CPANEL_CONFIG['email_quota_mb']
        )
        
        if result['success']:
            print(f"✓ Email created successfully: {result['email']}")
            # Increment cursor email username for next time
            update_cursor_email_username(current_username + 1)
            return result['email'], result['password']
        else:
            error_msg = str(result['error'])
            print(f"✗ Failed to create email: {result['error']}")
            
            # Check if the error is because the email already exists
            if 'already exists' in error_msg.lower():
                # Reuse the email that already exists
                existing_password = email_creator.get_fixed_password()
                print(f"✓ Email already exists, reusing: {email_address}")
                print(f"Using existing email with standard password")
                
                # Still increment the counter for next time
                update_cursor_email_username(current_username + 1)
                return email_address, existing_password
            else:
                # If it's a different error, return None
                print(f"Non-recoverable error occurred: {error_msg}")
                return None, None
                
    except Exception as e:
        print(f"Error in Cursor email creation: {e}")
        return None, None

 
async def human_like_typing(page, selectors_to_try, text, typing_delay_range=None):
    """
    Type text with human-like delays between keystrokes.
    (Copied from augment_reg.py as it's a useful utility)
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
                if element.is_visible(timeout=5000):
                    print(f"Found input field with selector: {sel}")
                    successful_selector = sel
                    break
            except Exception as e:
                print(f"Selector '{sel}' not found or not visible: {e}")
                continue
 
        if not element:
            print(f"Could not find input field with any of these selectors: {selectors_to_try}")
            return False 

        # Scroll element into view
        await element.scroll_into_view_if_needed()
        await asyncio.sleep(random.uniform(0.3, 0.7))

        # Click to focus the element
        print(f"Clicking on element with selector: {successful_selector}")
        await element.click()
        await asyncio.sleep(random.uniform(0.5, 1.0))

        # Clear any existing text using keyboard shortcuts
        await page.keyboard.press("Control+a")  # Select all
        await asyncio.sleep(random.uniform(0.1, 0.2))
        await page.keyboard.press("Delete")  # Delete selected text
        await asyncio.sleep(random.uniform(0.2, 0.4))

        # Type each character with random delays
        print(f"Typing '{text}' character by character...")
        for char in text:
            await page.keyboard.type(char) 
            delay = random.uniform(*typing_delay_range)
            await asyncio.sleep(delay)

        # Verify the text was entered
        try:
            current_value = await element.input_value()
            print(f"Current field value: '{current_value}'")
            if current_value == text:
                return True
            else:
                print("Warning: Typed text does not match final value.") 
                return False
        except:
            print("Could not verify input value, but typing completed.")
            return True
 
    except Exception as e:
        print(f"Error in human_like_typing: {e}")
        return False


async def enter_verification_code_digits(page, selectors_to_try, code):
    """
    Enter verification code digits individually into separate input fields.
    
    Args:
        page: Playwright page object
        selectors_to_try: List of selectors for each digit input field
        code: Verification code to enter (should be 6 digits)
    """
    try:
        if len(code) != 6:
            print(f"⚠ Verification code should be 6 digits, got {len(code)} digits: {code}")
            return False

        print(f"Entering verification code digits: {code}")
        
        # Enter each digit into its corresponding input field
        for i, digit in enumerate(code):
            if i >= len(selectors_to_try):
                print(f"⚠ Not enough selectors for digit {i+1}, have {len(selectors_to_try)} selectors")
                break
                
            selector = selectors_to_try[i]
            print(f"Entering digit '{digit}' into field {i+1} with selector: {selector}")
            
            try:
                # Find the input field for this digit
                element = page.locator(selector).first
                
                # Wait for the element to be visible
                if not await element.is_visible(timeout=5000):
                    print(f"⚠ Input field {i+1} not visible with selector: {selector}")
                    continue
                
                # Scroll element into view
                await element.scroll_into_view_if_needed()
                await asyncio.sleep(random.uniform(0.2, 0.4))
                
                # Click to focus the element
                await element.click()
                await asyncio.sleep(random.uniform(0.3, 0.5))
                
                # Clear any existing content
                await page.keyboard.press("Control+a")
                await asyncio.sleep(random.uniform(0.1, 0.2))
                await page.keyboard.press("Delete")
                await asyncio.sleep(random.uniform(0.1, 0.2))
                
                # Type the digit
                await page.keyboard.type(digit)
                await asyncio.sleep(random.uniform(0.3, 0.6))
                
                # Verify the digit was entered
                try:
                    current_value = await element.input_value()
                    if current_value == digit:
                        print(f"✓ Digit '{digit}' entered successfully in field {i+1}")
                    else:
                        print(f"⚠ Digit mismatch in field {i+1}: expected '{digit}', got '{current_value}'")
                except:
                    print(f"Could not verify digit in field {i+1}, but typing completed")
                
            except Exception as e:
                print(f"Error entering digit '{digit}' in field {i+1}: {e}")
                continue
        
        print("✓ All verification code digits entered!")
        await asyncio.sleep(random.uniform(0.5, 1.0))
        return True

    except Exception as e:
        print(f"Error in enter_verification_code_digits: {e}")
        return False

 
async def navigate_to_cursor():
    """
    Automates the registration process for Cursor, creating a real email account
    and completing the full verification flow including email code verification.
    """
    # Step 1: Create a new email account using Cursor-specific logic
    print("Creating a new email account for Cursor registration...")
    email_address, email_password = create_cursor_email()
    if not email_address:
        print("✗ Failed to create an email account. Exiting.")
        return False

    print(f"✓ Successfully created email: {email_address}")

    # Update the email configuration for any subsequent steps (like code verification)
    update_email_config(email_address, email_password)

    # Launch AsyncCamoufox with enhanced stealth configuration
    try:
        async with AsyncCamoufox(
            headless=BROWSER_CONFIG['headless'],
            os=["macos"],
            screen=Screen(max_width=1920, max_height=1080),
            geoip=True,
            locale="en-US",
            disable_coop=False,
            block_webrtc=True,
            enable_cache=False,
            main_world_eval=True,
        ) as browser:
            page = await browser.new_page()

            # Set additional headers
            await page.set_extra_http_headers({
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.5",
                "DNT": "1",
                "Connection": "keep-alive",
                "Upgrade-Insecure-Requests": "1",
            })

            try:
                print("Starting stealth navigation...")
                await asyncio.sleep(random.uniform(1, 3))

                # Navigate to the website
                url = CURSOR_CONFIG['registration_url']
                print(f"Navigating to Cursor registration: {url}")
                await page.goto(url, wait_until="domcontentloaded")

                # Wait for page to fully load
                print("Waiting for page to reach networkidle state...")
                try:
                    await page.wait_for_load_state("networkidle", timeout=BROWSER_CONFIG.get('page_load_timeout', 60000))
                    print("✓ Page reached networkidle state")
                except Exception as e:
                    print(f"⚠ Page did not reach networkidle state within timeout: {e}")
                    print("Continuing anyway...")

                await asyncio.sleep(random.uniform(1, 3))

                # --- REGISTRATION LOGIC FOR CURSOR ---
                
                # Handle Cloudflare verification using frame-based bypass
                print("Checking for Cloudflare verification...")
                await asyncio.sleep(random.uniform(2, 4))
                
                cloudflare_success = await handle_cloudflare_bypass(page)
                
                if cloudflare_success:
                    print("✓ Cloudflare verification completed successfully!")
                    # Wait for page to stabilize after Cloudflare
                    await asyncio.sleep(random.uniform(3, 5))
                    
                    # Verify page is still responsive
                    try:
                        await page.wait_for_load_state("domcontentloaded", timeout=10000)
                        print("Page is responsive after Cloudflare verification")
                    except Exception as e:
                        print(f"Page responsiveness check failed: {e}")
                else:
                    print("⚠ Cloudflare verification was not successful, but proceeding anyway")
                    # Take a screenshot for debugging
                    try:
                        await page.screenshot(path="cloudflare_debug.png")
                        print("Debug screenshot saved as cloudflare_debug.png")
                    except:
                        pass
                
                random_delay(1, 2)

                email_selectors = CURSOR_CONFIG['selectors']['email_input']
                print(f"Attempting to type email: {email_address}")
                success = await human_like_typing(page, email_selectors, email_address)

                if not success:
                    print("Failed to type email.")
                    return False
     
                print("✓ Email typing completed successfully!")
                await asyncio.sleep(random.uniform(1, 2))

                # Click the submit button to proceed
                print("Looking for submit button...")
                submit_selectors = CURSOR_CONFIG['selectors']['submit_button']
                
                # Try to find submit button with any of the selectors
                submit_btn = None
                for selector in submit_selectors:
                    try:
                        submit_btn = page.locator(selector).first
                        if await submit_btn.is_visible(timeout=5000):
                            print(f"Found submit button with selector: {selector}")
                            break
                    except Exception as e:
                        print(f"Submit selector '{selector}' not found: {e}")
                        continue

                if submit_btn and await submit_btn.is_visible():
                    await submit_btn.click()
                    print("✓ Clicked submit button.")
                    
                    # Wait for page response after submitting email
                    await asyncio.sleep(random.uniform(2, 4))
                    try:
                        await page.wait_for_load_state("networkidle", timeout=BROWSER_CONFIG.get('network_idle_timeout', 20000))
                        print("✓ Page loaded after email submission")
                    except Exception as e:
                        print(f"⚠ Page load timeout after email submission: {e}")
                        print("Continuing anyway...")
                    
                    # Step 2.5: Click magic-code button to trigger email sending
                    print("Looking for magic-code button to trigger email...")
                    magic_code_selectors = CURSOR_CONFIG['selectors']['magic_code_button']
                    
                    magic_code_clicked = False
                    for selector in magic_code_selectors:
                        try:
                            magic_btn = page.locator(selector).first
                            if await magic_btn.is_visible(timeout=5000):
                                print(f"Found magic-code button with selector: {selector}")
                                
                                await magic_btn.scroll_into_view_if_needed()
                                await asyncio.sleep(random.uniform(0.5, 1))
                                await magic_btn.click()
                                print("✓ Successfully clicked magic-code button!")
                                magic_code_clicked = True
                                break
                        except Exception as e:
                            print(f"Magic-code button selector '{selector}' failed: {e}")
                            continue
                    
                    if not magic_code_clicked:
                        print("⚠ Could not find or click magic-code button, proceeding anyway...")
                    
                    # Wait a moment after clicking magic-code button
                    await asyncio.sleep(random.uniform(1, 2))
                    
                    # Step 2.6: Check for second Cloudflare verification after magic-code click
                    print("Checking for additional Cloudflare verification after magic-code...")
                    await asyncio.sleep(random.uniform(2, 3))
                    
                    second_cloudflare_success = await handle_cloudflare_bypass(page)
                    
                    if second_cloudflare_success:
                        print("✓ Second Cloudflare verification completed successfully!")
                        # Wait for page to stabilize after second Cloudflare
                        await asyncio.sleep(random.uniform(3, 5))
                        
                        # Verify page is still responsive
                        try:
                            await page.wait_for_load_state("domcontentloaded", timeout=10000)
                            print("Page is responsive after second Cloudflare verification")
                        except Exception as e:
                            print(f"Page responsiveness check failed after second Cloudflare: {e}")
                    else:
                        print("⚠ Second Cloudflare verification was not needed or failed, proceeding anyway")
                    
                    # Step 3: Wait for verification code email
                    print("Waiting for verification code email...")
                    verification_code = await wait_for_verification_code(email_address)
                    
                    if not verification_code:
                        print("✗ Failed to receive verification code")
                        return False
                    
                    # Step 4: Enter verification code digits
                    print(f"Entering verification code: {verification_code}")
                    code_input_selectors = CURSOR_CONFIG['selectors']['verification_code_input']
                    
                    code_success = await enter_verification_code_digits(page, code_input_selectors, verification_code)
                    
                    if code_success:
                        print("✓ Verification code entered successfully!")
                        
                        # Step 5: Look for and click final submit button
                        await asyncio.sleep(random.uniform(1, 2))
                        print("Looking for final submit button...")
                        
                        final_submit_clicked = False
                        for selector in submit_selectors:
                            try:
                                final_submit_btn = page.locator(selector).first
                                if await final_submit_btn.is_visible(timeout=5000):
                                    print(f"Found final submit button with selector: {selector}")
                                    
                                    await final_submit_btn.scroll_into_view_if_needed()
                                    await asyncio.sleep(random.uniform(0.5, 1))
                                    await final_submit_btn.click()
                                    print("✓ Successfully clicked final submit button!")
                                    final_submit_clicked = True
                                    break
                            except Exception as e:
                                print(f"Final submit button selector '{selector}' failed: {e}")
                                continue
                        
                        if final_submit_clicked:
                            print("✓ Registration process completed successfully!")
                            await asyncio.sleep(random.uniform(2, 4))
                            try:
                                await page.wait_for_load_state("networkidle", timeout=BROWSER_CONFIG.get('network_idle_timeout', 20000))
                                print("✓ Final page loaded successfully")
                            except:
                                print("⚠ Final page did not reach networkidle state")
                            
                            # Give some time to observe the final result
                            print("Registration completed! Keeping browser open for 5 seconds to observe.")
                            await asyncio.sleep(5)
                            return True
                        else:
                            print("⚠ Could not find or click final submit button")
                            return False
                    else:
                        print("✗ Failed to enter verification code")
                        return False
                        
                else:
                    print(f"✗ Submit button not found with any of these selectors: {submit_selectors}")
                    print("⚠ Continuing without clicking submit button - may need manual interaction")
                    
                    # For debugging, keep browser open longer
                    print("Keeping browser open for 15 seconds to observe.")
                    await asyncio.sleep(15)

                return True

            except Exception as e:
                print(f"\nAn error occurred during navigation: {e}")
                if DEBUG_CONFIG.get('save_error_screenshots', True):
                    try:
                        screenshot_path = "cursor_error_screenshot.png"
                        await page.screenshot(path=screenshot_path)
                        print(f"Screenshot saved to {screenshot_path}")
                    except Exception as se:
                        print(f"Failed to save screenshot: {se}")
                return False

    except Exception as outer_e:
        print(f"\nAn error occurred during browser initialization: {outer_e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Main function to run the Cursor registration script"""
    print("--- Starting Cursor Registration Script ---")
    try:
        is_successful = await navigate_to_cursor()
        if is_successful:
            print("\n--- ✓ Script finished successfully. ---")
        else:
            print("\n--- ✗ Script failed. ---")
    except Exception as e:
        print(f"\n--- ✗ Script failed with exception: {e} ---")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())