import requests
import json
import asyncio
import aiohttp
from concurrent.futures import ThreadPoolExecutor

class EmailCreator:


    def __init__(self, cpanel_user, cpanel_pass, domain, cpanel_url=None):
        """
        Initialize EmailCreator with cPanel credentials

        Args:
            cpanel_user (str): cPanel username
            cpanel_pass (str): cPanel password
            domain (str): Domain name for email accounts
            cpanel_url (str): cPanel URL (optional, will be constructed if not provided)
        """
        self.cpanel_user = cpanel_user
        self.cpanel_pass = cpanel_pass
        self.domain = domain

        # Extract domain from your webmail URL if cpanel_url not provided
        if cpanel_url:
            self.cpanel_url = cpanel_url
        else:
            # Extract from your webmail URL: s691.lon1.mysecurecloudhost.com:2096
            # Assuming cPanel is on port 2083 (standard SSL port)
            host = "s691.lon1.mysecurecloudhost.com"
            self.cpanel_url = f"https://{host}:2083"

    def generate_email_name(self):
        """Generate sequential email username based on config"""
        from config import get_current_email_username, update_email_username

        current_number = get_current_email_username()
        next_number = current_number + 1

        # Update the config with the next number
        update_email_username(next_number)

        return str(current_number)

    def get_fixed_password(self):
        """Return the fixed password"""
        return "808080aA."

    def create_email_account(self, email_name=None, password=None, quota=1):
        """
        Create a new email account using cPanel API (synchronous version)

        Args:
            email_name (str): Email username (before @domain.com). If None, generates random
            password (str): Email password. If None, generates random
            quota (int): Email quota in MB (default: 1 MB)

        Returns:
            dict: Result containing email details and creation status
        """
        try:
            # Generate credentials if not provided
            if email_name is None:
                email_name = self.generate_email_name()

            if password is None:
                password = self.get_fixed_password()

            # Construct the API endpoint
            api_endpoint = f"{self.cpanel_url}/execute/Email/add_pop"

            # Parameters for the API call
            params = {
                'email': email_name,
                'password': password,
                'quota': quota,
                'domain': self.domain
            }

            # Make the API request with reduced timeout for faster response
            response = requests.get(
                api_endpoint,
                params=params,
                auth=(self.cpanel_user, self.cpanel_pass),
                verify=True,
                timeout=10  # Reduced from 30 to 10 seconds
            )

            # Check if request was successful
            if response.status_code == 200:
                try:
                    result_data = response.json()

                    # Check if the email was created successfully
                    if result_data.get('status') == 1:
                        full_email = f"{email_name}@{self.domain}"

                        return {
                            'success': True,
                            'email': full_email,
                            'username': email_name,
                            'password': password,
                            'quota': quota,
                            'message': 'Email account created successfully',
                            'api_response': result_data
                        }
                    else:
                        return {
                            'success': False,
                            'error': result_data.get('errors', ['Unknown error occurred']),
                            'api_response': result_data
                        }

                except json.JSONDecodeError:
                    return {
                        'success': False,
                        'error': f'Invalid JSON response: {response.text}',
                        'status_code': response.status_code
                    }
            else:
                return {
                    'success': False,
                    'error': f'HTTP Error {response.status_code}: {response.text}',
                    'status_code': response.status_code
                }

        except requests.exceptions.RequestException as e:
            return {
                'success': False,
                'error': f'Request failed: {str(e)}'
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'Unexpected error: {str(e)}'
            }

    async def create_email_account_async(self, email_name=None, password=None, quota=1):
        """
        Create a new email account using cPanel API (asynchronous version)

        Args:
            email_name (str): Email username (before @domain.com). If None, generates random
            password (str): Email password. If None, generates random
            quota (int): Email quota in MB (default: 1 MB)

        Returns:
            dict: Result containing email details and creation status
        """
        try:
            # Generate credentials if not provided
            if email_name is None:
                email_name = self.generate_email_name()

            if password is None:
                password = self.get_fixed_password()

            # Construct the API endpoint
            api_endpoint = f"{self.cpanel_url}/execute/Email/add_pop"

            # Parameters for the API call
            params = {
                'email': email_name,
                'password': password,
                'quota': quota,
                'domain': self.domain
            }

            # Create auth object
            auth = aiohttp.BasicAuth(self.cpanel_user, self.cpanel_pass)

            # Make the async API request
            timeout = aiohttp.ClientTimeout(total=10)  # Fast timeout
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(api_endpoint, params=params, auth=auth) as response:
                    if response.status == 200:
                        try:
                            result_data = await response.json()

                            # Check if the email was created successfully
                            if result_data.get('status') == 1:
                                full_email = f"{email_name}@{self.domain}"

                                return {
                                    'success': True,
                                    'email': full_email,
                                    'username': email_name,
                                    'password': password,
                                    'quota': quota,
                                    'message': 'Email account created successfully',
                                    'api_response': result_data
                                }
                            else:
                                return {
                                    'success': False,
                                    'error': result_data.get('errors', ['Unknown error occurred']),
                                    'api_response': result_data
                                }

                        except json.JSONDecodeError:
                            response_text = await response.text()
                            return {
                                'success': False,
                                'error': f'Invalid JSON response: {response_text}',
                                'status_code': response.status
                            }
                    else:
                        response_text = await response.text()
                        return {
                            'success': False,
                            'error': f'HTTP Error {response.status}: {response_text}',
                            'status_code': response.status
                        }

        except asyncio.TimeoutError:
            return {
                'success': False,
                'error': 'Request timed out'
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'Unexpected error: {str(e)}'
            }

    def create_multiple_emails(self, count=1, quota=1):
        """
        Create multiple email accounts (synchronous version)

        Args:
            count (int): Number of email accounts to create
            quota (int): Email quota in MB for each account

        Returns:
            list: List of results for each email creation attempt
        """
        results = []

        for i in range(count):
            print(f"Creating email account {i+1}/{count}...")
            result = self.create_email_account(quota=quota)
            results.append(result)

            if result['success']:
                print(f"✓ Created: {result['email']}")
            else:
                print(f"✗ Failed: {result['error']}")

        return results

    async def create_multiple_emails_async(self, count=1, quota=1):
        """
        Create multiple email accounts asynchronously (much faster)

        Args:
            count (int): Number of email accounts to create
            quota (int): Email quota in MB for each account

        Returns:
            list: List of results for each email creation attempt
        """
        print(f"Creating {count} email accounts asynchronously...")

        # Create all tasks at once
        tasks = []
        for i in range(count):
            task = self.create_email_account_async(quota=quota)
            tasks.append(task)

        # Execute all tasks concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Process results and handle any exceptions
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                processed_results.append({
                    'success': False,
                    'error': f'Exception occurred: {str(result)}'
                })
                print(f"✗ Email {i+1} failed with exception: {result}")
            else:
                processed_results.append(result)
                if result['success']:
                    print(f"✓ Created: {result['email']}")
                else:
                    print(f"✗ Failed: {result['error']}")

        return processed_results

    async def delete_multiple_emails_async(self, email_addresses):
        """
        Delete multiple email accounts asynchronously (much faster)

        Args:
            email_addresses (list): List of email addresses to delete

        Returns:
            list: List of results for each email deletion attempt
        """
        print(f"Deleting {len(email_addresses)} email accounts asynchronously...")

        # Create all tasks at once
        tasks = []
        for email_address in email_addresses:
            task = self.delete_email_account_async(email_address)
            tasks.append(task)

        # Execute all tasks concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Process results and handle any exceptions
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                processed_results.append({
                    'success': False,
                    'error': f'Exception occurred: {str(result)}',
                    'email': email_addresses[i]
                })
                print(f"✗ Email {email_addresses[i]} deletion failed with exception: {result}")
            else:
                processed_results.append(result)
                if result['success']:
                    print(f"✓ Deleted: {result['email']}")
                else:
                    print(f"✗ Failed to delete: {result['email']} - {result['error']}")

        return processed_results

    def delete_email_account(self, email_address):
        """
        Delete an email account using cPanel API (synchronous version)

        Args:
            email_address (str): Full email address to delete (e.g., "user@domain.com")

        Returns:
            dict: Result containing deletion status
        """
        try:
            # Extract username from email address
            if '@' in email_address:
                email_name = email_address.split('@')[0]
            else:
                email_name = email_address

            # Construct the API endpoint for deleting email
            api_endpoint = f"{self.cpanel_url}/execute/Email/delete_pop"

            # Parameters for the API call
            params = {
                'email': email_name,
                'domain': self.domain
            }

            # Make the API request with reduced timeout
            response = requests.get(
                api_endpoint,
                params=params,
                auth=(self.cpanel_user, self.cpanel_pass),
                verify=True,
                timeout=10  # Reduced from 30 to 10 seconds
            )

            # Check if request was successful
            if response.status_code == 200:
                try:
                    result_data = response.json()

                    # Check if the email was deleted successfully
                    if result_data.get('status') == 1:
                        return {
                            'success': True,
                            'email': email_address,
                            'message': 'Email account deleted successfully',
                            'api_response': result_data
                        }
                    else:
                        return {
                            'success': False,
                            'error': result_data.get('errors', ['Unknown error occurred']),
                            'api_response': result_data
                        }

                except json.JSONDecodeError:
                    return {
                        'success': False,
                        'error': f'Invalid JSON response: {response.text}',
                        'status_code': response.status_code
                    }
            else:
                return {
                    'success': False,
                    'error': f'HTTP Error {response.status_code}: {response.text}',
                    'status_code': response.status_code
                }

        except requests.exceptions.RequestException as e:
            return {
                'success': False,
                'error': f'Request failed: {str(e)}'
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'Unexpected error: {str(e)}'
            }

    async def delete_email_account_async(self, email_address):
        """
        Delete an email account using cPanel API (asynchronous version)

        Args:
            email_address (str): Full email address to delete (e.g., "user@domain.com")

        Returns:
            dict: Result containing deletion status
        """
        try:
            # Extract username from email address
            if '@' in email_address:
                email_name = email_address.split('@')[0]
            else:
                email_name = email_address

            # Construct the API endpoint for deleting email
            api_endpoint = f"{self.cpanel_url}/execute/Email/delete_pop"

            # Parameters for the API call
            params = {
                'email': email_name,
                'domain': self.domain
            }

            # Create auth object
            auth = aiohttp.BasicAuth(self.cpanel_user, self.cpanel_pass)

            # Make the async API request
            timeout = aiohttp.ClientTimeout(total=10)  # Fast timeout
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(api_endpoint, params=params, auth=auth) as response:
                    if response.status == 200:
                        try:
                            result_data = await response.json()

                            # Check if the email was deleted successfully
                            if result_data.get('status') == 1:
                                return {
                                    'success': True,
                                    'email': email_address,
                                    'message': 'Email account deleted successfully',
                                    'api_response': result_data
                                }
                            else:
                                return {
                                    'success': False,
                                    'error': result_data.get('errors', ['Unknown error occurred']),
                                    'api_response': result_data
                                }

                        except json.JSONDecodeError:
                            response_text = await response.text()
                            return {
                                'success': False,
                                'error': f'Invalid JSON response: {response_text}',
                                'status_code': response.status
                            }
                    else:
                        response_text = await response.text()
                        return {
                            'success': False,
                            'error': f'HTTP Error {response.status}: {response_text}',
                            'status_code': response.status
                        }

        except asyncio.TimeoutError:
            return {
                'success': False,
                'error': 'Request timed out'
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'Unexpected error: {str(e)}'
            }

    def get_email_settings(self, email_address):
        """
        Get email settings for connecting to the email account

        Args:
            email_address (str): Full email address

        Returns:
            dict: Email server settings
        """
        # Extract domain from your setup
        host = "s691.lon1.mysecurecloudhost.com"

        return {
            'email': email_address,
            'imap_server': host,
            'imap_port': 993,
            'imap_ssl': True,
            'pop3_server': host,
            'pop3_port': 995,
            'pop3_ssl': True,
            'smtp_server': host,
            'smtp_port': 465,
            'smtp_ssl': True,
            'webmail_url': f"https://{host}:2096/3rdparty/roundcube/"
        }


def main():
    """Example usage of EmailCreator"""

    # Your cPanel credentials (you should store these securely)
    CPANEL_USER = "safeneta"
    CPANEL_PASS = "0PMk-!JzpY97v7"
    DOMAIN = "safenetaibd.com"  # Replace with your actual domain

    # Create EmailCreator instance
    email_creator = EmailCreator(CPANEL_USER, CPANEL_PASS, DOMAIN)

    # Create a single email account
    print("Creating email account...")
    result = email_creator.create_email_account()

    if result['success']:
        print(f"✓ Email created successfully!")
        print(f"Email: {result['email']}")
        print(f"Password: {result['password']}")

        # Get email settings
        settings = email_creator.get_email_settings(result['email'])
        print(f"IMAP Server: {settings['imap_server']}:{settings['imap_port']}")
        print(f"Webmail: {settings['webmail_url']}")

    else:
        print(f"✗ Failed to create email: {result['error']}")

    # Example: Create multiple email accounts
    # results = email_creator.create_multiple_emails(count=3)


if __name__ == "__main__":
    main()
