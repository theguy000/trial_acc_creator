"""
Email Management Module

This module handles email deletion and counter increment logic as an alternative
to the current +1 email configuration approach in augment_reg.py.

It ensures emails are properly cleaned up before incrementing to the next email
configuration, rather than just incrementing the counter without cleanup.

Updated with async support for faster operations without delays.
"""

import asyncio
from email_creator import EmailCreator
from config import (
    CPANEL_CONFIG,
    get_current_email_username,
    update_email_username,
    get_email_address
)


class EmailManager:
    """
    Manages email lifecycle including deletion and counter increment logic
    """
    
    def __init__(self):
        """Initialize EmailManager with cPanel configuration"""
        self.email_creator = EmailCreator(
            cpanel_user=CPANEL_CONFIG['username'],
            cpanel_pass=CPANEL_CONFIG['password'],
            domain=CPANEL_CONFIG['domain']
        )
        
    def get_current_email_address(self):
        """Get the current email address based on config counter"""
        current_number = get_current_email_username()
        return get_email_address(current_number)
    
    def delete_current_email(self):
        """
        Delete the current email account based on the config counter (synchronous)

        Returns:
            dict: Result containing deletion status and details
        """
        try:
            current_email = self.get_current_email_address()
            print(f"Attempting to delete current email: {current_email}")

            # Attempt to delete the email account
            result = self.email_creator.delete_email_account(current_email)

            if result['success']:
                print(f"✓ Email deleted successfully: {current_email}")
                return {
                    'success': True,
                    'email': current_email,
                    'message': 'Email deleted successfully'
                }
            else:
                error_msg = str(result['error'])
                print(f"✗ Failed to delete email: {error_msg}")

                # Check if the error is because the email doesn't exist
                if 'does not exist' in error_msg.lower() or 'not found' in error_msg.lower():
                    print(f"Email {current_email} doesn't exist, treating as successful deletion")
                    return {
                        'success': True,
                        'email': current_email,
                        'message': 'Email did not exist (already deleted or never created)'
                    }
                else:
                    return {
                        'success': False,
                        'email': current_email,
                        'error': error_msg
                    }

        except Exception as e:
            print(f"Error deleting current email: {e}")
            return {
                'success': False,
                'error': f'Unexpected error: {str(e)}'
            }

    async def delete_current_email_async(self):
        """
        Delete the current email account based on the config counter (asynchronous - FAST)

        Returns:
            dict: Result containing deletion status and details
        """
        try:
            current_email = self.get_current_email_address()
            print(f"Attempting to delete current email asynchronously: {current_email}")

            # Attempt to delete the email account asynchronously
            result = await self.email_creator.delete_email_account_async(current_email)

            if result['success']:
                print(f"✓ Email deleted successfully: {current_email}")
                return {
                    'success': True,
                    'email': current_email,
                    'message': 'Email deleted successfully'
                }
            else:
                error_msg = str(result['error'])
                print(f"✗ Failed to delete email: {error_msg}")

                # Check if the error is because the email doesn't exist
                if 'does not exist' in error_msg.lower() or 'not found' in error_msg.lower():
                    print(f"Email {current_email} doesn't exist, treating as successful deletion")
                    return {
                        'success': True,
                        'email': current_email,
                        'message': 'Email did not exist (already deleted or never created)'
                    }
                else:
                    return {
                        'success': False,
                        'email': current_email,
                        'error': error_msg
                    }

        except Exception as e:
            print(f"Error deleting current email asynchronously: {e}")
            return {
                'success': False,
                'error': f'Unexpected error: {str(e)}'
            }
    
    def increment_email_counter(self):
        """
        Increment the email counter to move to the next email configuration
        
        Returns:
            dict: Result containing the new email details
        """
        try:
            current_number = get_current_email_username()
            next_number = current_number + 1
            
            # Update the config with the next number
            update_email_username(next_number)
            
            new_email = get_email_address(next_number)
            
            print(f"✓ Email counter incremented from {current_number} to {next_number}")
            print(f"Next email will be: {new_email}")
            
            return {
                'success': True,
                'previous_number': current_number,
                'new_number': next_number,
                'new_email': new_email,
                'message': f'Counter incremented to {next_number}'
            }
            
        except Exception as e:
            print(f"Error incrementing email counter: {e}")
            return {
                'success': False,
                'error': f'Failed to increment counter: {str(e)}'
            }
    
    def delete_and_increment(self, delay_seconds=0):
        """
        Delete the current email account and increment to the next email configuration (synchronous)

        This is the main method that replaces the existing +1 email configuration logic.
        It ensures proper cleanup before moving to the next email.

        Args:
            delay_seconds (int): Delay between deletion and increment operations (default: 0 for speed)

        Returns:
            dict: Combined result of deletion and increment operations
        """
        try:
            print("Starting email deletion and increment process...")

            # Step 1: Delete the current email
            deletion_result = self.delete_current_email()

            if not deletion_result['success']:
                print(f"Warning: Email deletion failed, but continuing with increment...")
                print(f"Deletion error: {deletion_result.get('error', 'Unknown error')}")

            # Optional delay (removed by default for speed)
            if delay_seconds > 0:
                print(f"Waiting {delay_seconds} seconds before incrementing...")
                import time
                time.sleep(delay_seconds)

            # Step 2: Increment the counter
            increment_result = self.increment_email_counter()

            if increment_result['success']:
                return {
                    'success': True,
                    'deletion_result': deletion_result,
                    'increment_result': increment_result,
                    'previous_email': deletion_result.get('email'),
                    'new_email': increment_result.get('new_email'),
                    'message': 'Email deletion and increment completed successfully'
                }
            else:
                return {
                    'success': False,
                    'deletion_result': deletion_result,
                    'increment_result': increment_result,
                    'error': 'Failed to increment email counter after deletion'
                }

        except Exception as e:
            print(f"Error in delete_and_increment: {e}")
            return {
                'success': False,
                'error': f'Unexpected error in delete_and_increment: {str(e)}'
            }

    async def delete_and_increment_async(self):
        """
        Delete the current email account and increment to the next email configuration (asynchronous - FAST)

        This is the async version that performs operations without any delays for maximum speed.

        Returns:
            dict: Combined result of deletion and increment operations
        """
        try:
            print("Starting async email deletion and increment process...")

            # Step 1: Delete the current email asynchronously
            deletion_result = await self.delete_current_email_async()

            if not deletion_result['success']:
                print(f"Warning: Email deletion failed, but continuing with increment...")
                print(f"Deletion error: {deletion_result.get('error', 'Unknown error')}")

            # Step 2: Increment the counter (this is fast, no need to make it async)
            increment_result = self.increment_email_counter()

            if increment_result['success']:
                return {
                    'success': True,
                    'deletion_result': deletion_result,
                    'increment_result': increment_result,
                    'previous_email': deletion_result.get('email'),
                    'new_email': increment_result.get('new_email'),
                    'message': 'Async email deletion and increment completed successfully'
                }
            else:
                return {
                    'success': False,
                    'deletion_result': deletion_result,
                    'increment_result': increment_result,
                    'error': 'Failed to increment email counter after deletion'
                }

        except Exception as e:
            print(f"Error in async delete_and_increment: {e}")
            return {
                'success': False,
                'error': f'Unexpected error in async delete_and_increment: {str(e)}'
            }
    
    def cleanup_multiple_emails(self, email_numbers):
        """
        Delete multiple email accounts by their numbers (synchronous)

        Args:
            email_numbers (list): List of email numbers to delete

        Returns:
            list: List of deletion results for each email
        """
        results = []

        for number in email_numbers:
            email_address = get_email_address(number)
            print(f"Deleting email: {email_address}")

            result = self.email_creator.delete_email_account(email_address)
            result['email_number'] = number
            results.append(result)

            if result['success']:
                print(f"✓ Deleted: {email_address}")
            else:
                print(f"✗ Failed to delete: {email_address} - {result['error']}")

            # No delay for faster operation

        return results

    async def cleanup_multiple_emails_async(self, email_numbers):
        """
        Delete multiple email accounts by their numbers (asynchronous - MUCH FASTER)

        Args:
            email_numbers (list): List of email numbers to delete

        Returns:
            list: List of deletion results for each email
        """
        print(f"Deleting {len(email_numbers)} emails asynchronously...")

        # Convert email numbers to email addresses
        email_addresses = [get_email_address(number) for number in email_numbers]

        # Use the async bulk deletion method from EmailCreator
        results = await self.email_creator.delete_multiple_emails_async(email_addresses)

        # Add email numbers to results
        for i, result in enumerate(results):
            result['email_number'] = email_numbers[i]

        return results


def main():
    """Example usage of EmailManager"""
    
    # Create EmailManager instance
    email_manager = EmailManager()
    
    # Show current email
    current_email = email_manager.get_current_email_address()
    print(f"Current email: {current_email}")
    
    # Perform deletion and increment
    result = email_manager.delete_and_increment()
    
    if result['success']:
        print(f"✓ Process completed successfully!")
        print(f"Previous email: {result['previous_email']}")
        print(f"New email: {result['new_email']}")
    else:
        print(f"✗ Process failed: {result['error']}")


if __name__ == "__main__":
    main()
