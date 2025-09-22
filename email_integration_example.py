"""
Email Integration Example

This file demonstrates how to integrate the new EmailManager into augment_reg.py
to replace the existing +1 email configuration logic.

The new approach ensures emails are properly cleaned up before incrementing 
to the next email configuration.
"""

from email_manager import EmailManager
from email_creator import EmailCreator
from config import CPANEL_CONFIG


def create_new_email_with_cleanup():
    """
    Enhanced version of create_new_email() that includes cleanup logic.
    
    This function replaces the existing create_new_email() function in augment_reg.py.
    It first deletes the current email (if it exists), then increments the counter,
    and finally creates the new email account.
    
    Returns:
        tuple: (email_address, password) if successful, (None, None) if failed
    """
    try:
        print("Starting enhanced email creation with cleanup...")
        
        # Step 1: Initialize EmailManager for cleanup operations
        email_manager = EmailManager()
        
        # Step 2: Delete current email and increment counter
        print("Performing email cleanup and counter increment...")
        cleanup_result = email_manager.delete_and_increment()
        
        if not cleanup_result['success']:
            print(f"Warning: Cleanup process had issues: {cleanup_result.get('error', 'Unknown error')}")
            # Continue anyway, as the increment might have succeeded
        
        # Step 3: Create the new email account
        print("Creating new email account...")
        
        # Create email creator instance
        email_creator = EmailCreator(
            cpanel_user=CPANEL_CONFIG['username'],
            cpanel_pass=CPANEL_CONFIG['password'],
            domain=CPANEL_CONFIG['domain']
        )
        
        # Get the current email address (should be the new one after increment)
        current_email = email_manager.get_current_email_address()
        print(f"Attempting to create: {current_email}")
        
        # Extract username from email for creation
        email_username = current_email.split('@')[0]
        
        # Try to create the email account
        result = email_creator.create_email_account(
            email_name=email_username,
            quota=CPANEL_CONFIG['email_quota_mb']
        )
        
        if result['success']:
            print(f"✓ Email created successfully: {result['email']}")
            return result['email'], result['password']
        else:
            error_msg = str(result['error'])
            print(f"✗ Failed to create email: {result['error']}")
            
            # Check if the error is because the email already exists
            if 'already exists' in error_msg.lower():
                # Reuse the email that already exists
                existing_password = email_creator.get_fixed_password()
                
                print(f"✓ Email already exists, reusing: {current_email}")
                print(f"Using existing email with standard password")
                
                return current_email, existing_password
            else:
                # If it's a different error, return None
                print(f"Non-recoverable error occurred: {error_msg}")
                return None, None
                
    except Exception as e:
        print(f"Error in enhanced email creation: {e}")
        return None, None


def cleanup_old_emails_batch(start_number, end_number):
    """
    Cleanup a batch of old email accounts
    
    Args:
        start_number (int): Starting email number to delete
        end_number (int): Ending email number to delete (inclusive)
        
    Returns:
        dict: Summary of cleanup results
    """
    try:
        print(f"Starting batch cleanup of emails {start_number} to {end_number}...")
        
        email_manager = EmailManager()
        email_numbers = list(range(start_number, end_number + 1))
        
        results = email_manager.cleanup_multiple_emails(email_numbers)
        
        # Summarize results
        successful = sum(1 for r in results if r['success'])
        failed = len(results) - successful
        
        summary = {
            'total_attempted': len(results),
            'successful_deletions': successful,
            'failed_deletions': failed,
            'results': results
        }
        
        print(f"Batch cleanup completed:")
        print(f"  Total attempted: {summary['total_attempted']}")
        print(f"  Successful: {summary['successful_deletions']}")
        print(f"  Failed: {summary['failed_deletions']}")
        
        return summary
        
    except Exception as e:
        print(f"Error in batch cleanup: {e}")
        return {
            'total_attempted': 0,
            'successful_deletions': 0,
            'failed_deletions': 0,
            'error': str(e)
        }


def demonstrate_new_workflow():
    """
    Demonstrate the new email management workflow
    """
    print("=== Email Management Workflow Demonstration ===\n")
    
    # Show current state
    email_manager = EmailManager()
    current_email = email_manager.get_current_email_address()
    print(f"Current email in config: {current_email}\n")
    
    # Option 1: Just delete and increment (without creating new email)
    print("Option 1: Delete current email and increment counter")
    result = email_manager.delete_and_increment()
    if result['success']:
        print(f"✓ Moved from {result['previous_email']} to {result['new_email']}\n")
    else:
        print(f"✗ Failed: {result['error']}\n")
    
    # Option 2: Full workflow with email creation
    print("Option 2: Full workflow with email creation")
    email_address, password = create_new_email_with_cleanup()
    if email_address:
        print(f"✓ New email ready: {email_address} with password: {password}\n")
    else:
        print("✗ Failed to create new email\n")


def integration_instructions():
    """
    Print instructions for integrating into augment_reg.py
    """
    print("=== Integration Instructions ===\n")
    
    print("To integrate the new EmailManager into augment_reg.py:")
    print("1. Add import at the top of augment_reg.py:")
    print("   from email_manager import EmailManager")
    print()
    print("2. Replace the existing create_new_email() function with:")
    print("   create_new_email_with_cleanup() from this file")
    print()
    print("3. The new function will:")
    print("   - Delete the current email account")
    print("   - Increment the email counter")
    print("   - Create a new email account")
    print("   - Return the email and password as before")
    print()
    print("4. Optional: Use cleanup_old_emails_batch() to clean up")
    print("   any existing old email accounts")
    print()
    print("Benefits of the new approach:")
    print("- Proper cleanup of old emails")
    print("- Prevents accumulation of unused email accounts")
    print("- Maintains the same interface as the original function")
    print("- Adds error handling for deletion operations")


def main():
    """Main function to demonstrate the new email management system"""
    
    # Show integration instructions
    integration_instructions()
    print("\n" + "="*50 + "\n")
    
    # Demonstrate the workflow
    demonstrate_new_workflow()
    
    print("=== End of Demonstration ===")


if __name__ == "__main__":
    main()
