import requests
import json
import os
import time
import re

def load_json_data_from_file(json_file_path="augment_data.json", max_wait_seconds=60):
    """
    Load JSON data from file created by augment_reg.py

    Args:
        json_file_path: Path to the JSON file
        max_wait_seconds: Maximum time to wait for the file to be created

    Returns:
        dict: JSON data or None if file not found/invalid
    """
    start_time = time.time()
    while time.time() - start_time < max_wait_seconds:
        if os.path.exists(json_file_path):
            try:
                with open(json_file_path, 'r') as f:
                    data = json.load(f)
                return data
            except (json.JSONDecodeError, Exception):
                return None
        else:
            time.sleep(1)

    return None

def extract_token_and_url(html_content):
    """
    Extract access token and tenant URL from HTML response

    Args:
        html_content: HTML string containing the token and URL

    Returns:
        tuple: (access_token, tenant_url) or (None, None) if not found
    """
    access_token = None
    tenant_url = None

    # Extract access token using regex
    token_match = re.search(r'<h3>Access Token:</h3><pre>([^<]+)</pre>', html_content)
    if token_match:
        access_token = token_match.group(1).strip()

    # Extract tenant URL using regex
    url_match = re.search(r'<h3>Tenant URL:</h3><pre>([^<]+)</pre>', html_content)
    if url_match:
        tenant_url = url_match.group(1).strip()

    return access_token, tenant_url

def make_augment_callback_request(json_data=None):
    """
    Send JSON data to https://augmenttoken.deno.dev/callback

    Args:
        json_data: Dictionary containing the JSON data to send
    """
    if json_data is None:
        # Try to load from file
        json_data = load_json_data_from_file()
        if json_data is None:
            return None

    url = 'https://augmenttoken.deno.dev/callback'

    # Headers for multipart form data request (let requests handle content-type with boundary)
    headers = {
        'accept': '*/*',
        'accept-language': 'en-US,en;q=0.9,bn;q=0.8',
        'dnt': '1',
        'origin': 'https://augmenttoken.deno.dev',
        'priority': 'u=1, i',
        'referer': 'https://augmenttoken.deno.dev/',
        'sec-ch-ua': '"Not;A=Brand";v="99", "Microsoft Edge";v="139", "Chromium";v="139"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-origin',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36 Edg/139.0.0.0'
    }

    # Prepare multipart form data matching the curl command
    # Based on the curl, we need: code, tenant_url, and verifier (not state)
    # The verifier corresponds to the code_challenge in the OAuth PKCE flow
    form_data = {
        'code': json_data.get('code', ''),
        'tenant_url': json_data.get('tenant_url', ''),
        'verifier': 'TnI8hzOl1DFYQyBqpaOBrAfDSu4PtfDCgqSFgh2zvKQ'  # PKCE code_verifier from the curl command
    }

    try:
        # Make the POST request with multipart form data
        # Using data parameter with tuple values to force multipart/form-data
        multipart_data = {key: (None, value) for key, value in form_data.items()}
        response = requests.post(url, headers=headers, files=multipart_data)

        # Extract access token and tenant URL from HTML response
        if response.status_code == 200:
            access_token, tenant_url = extract_token_and_url(response.text)
            if access_token and tenant_url:
                print(access_token)
                print(tenant_url)
                return response
        return None

    except requests.exceptions.RequestException:
        return None

if __name__ == "__main__":
    response = make_augment_callback_request()
