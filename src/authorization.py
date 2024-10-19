import platform
import time
import json
import os
import requests
from urllib.parse import urlparse, parse_qs
from http.server import BaseHTTPRequestHandler, HTTPServer

from twitch import twitch_login

def get_token_file(user_id):
    """Get the token file path for a specific user."""
    return f"twitch_token_{user_id}.json"

def save_token(user_id, token_data):
    """Save access token and its expiration time to a file specific to the user."""
    token_file = get_token_file(user_id)
    with open(token_file, "w") as f:
        json.dump(token_data, f)

def load_token(user_id):
    """Load access token and its expiration time from the file specific to the user."""
    token_file = get_token_file(user_id)
    if os.path.exists(token_file):
        with open(token_file, "r") as f:
            return json.load(f)
    return None

def is_token_expired(token_data):
    """Check if the access token is expired."""
    return time.time() > token_data['expires_at']

def generate_auth_url(client_id, redirect_uri, scopes):
    """Generate Twitch OAuth authorization URL."""
    auth_url = (
        f"https://id.twitch.tv/oauth2/authorize?"
        f"response_type=code&client_id={client_id}&redirect_uri={redirect_uri}&scope={scopes}"
    )
    return auth_url

def get_access_token_with_code(client_id, client_secret, redirect_uri, code):
    """Exchange authorization code for access token."""
    url = "https://id.twitch.tv/oauth2/token"
    payload = {
        'client_id': client_id,
        'client_secret': client_secret,
        'code': code,
        'grant_type': 'authorization_code',
        'redirect_uri': redirect_uri
    }
    
    response = requests.post(url, data=payload)
    
    if response.status_code == 200:
        data = response.json()
        return data
    else:
        print(f"Failed to get access token. Status code: {response.status_code}. Response: {response.text}")
        return None

class TwitchOAuthHandler(BaseHTTPRequestHandler):
    """HTTP handler to process the OAuth callback and capture the authorization code."""
    authorization_code = None

    def do_GET(self):
        """Handle GET requests, extract authorization code."""
        parsed_url = urlparse(self.path)
        query_params = parse_qs(parsed_url.query)
        
        if 'code' in query_params:
            TwitchOAuthHandler.authorization_code = query_params['code'][0]
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(b"Authorization successful! You can close this window.")
        else:
            self.send_response(400)
            self.end_headers()
            self.wfile.write(b"Authorization failed. No code found.")

def get_authorization_code(driver, client_id, redirect_uri, scopes, username, password):
    """Open the Twitch OAuth authorization URL and start a local server to get the authorization code."""
    auth_url = generate_auth_url(client_id, redirect_uri, scopes)
    print(password)

    # Open the URL in the default web browser
    # driver.uc_open(auth_url)
    twitch_login(driver, username, password, auth_url)

    # Start a simple HTTP server to listen for the Twitch callback with the authorization code
    server_address = ('', 8080)  # Listen on port 8080
    httpd = HTTPServer(server_address, TwitchOAuthHandler)

    print("Waiting for authorization code...")

    # Handle a single request (this will block until Twitch redirects back with the authorization code)
    httpd.handle_request()

    # httpd.shutdown()

    # Retrieve the authorization code from the handler
    return TwitchOAuthHandler.authorization_code

def kill_port(port):
    """Kill the process using the specified port."""
    system_platform = platform.system()
    
    if system_platform == "Windows":
        # Windows command to kill the process occupying the specified port
        command = f"netstat -ano | findstr :{port}"
        result = os.popen(command).read()
        if result:
            pid = result.strip().split()[-1]
            os.system(f"taskkill /PID {pid} /F")
            print(f"Process on port {port} killed (PID: {pid}).")
        else:
            print(f"No process found on port {port}.")
    else:
        # For Linux/macOS
        command = f"lsof -ti :{port} | xargs kill -9"
        os.system(command)
        print(f"Killed process on port {port}.")

def get_access_token(driver, user_id, client_id, client_secret, redirect_uri, username, password):
    """Get a new access token via the authorization code flow."""
    kill_port(8080)  # Kill any existing process using port 8080
    token_data = load_token(user_id)
    
    if token_data and not is_token_expired(token_data):
        print(f"Using stored access token for user {user_id}.")
        return token_data['access_token']
    
    print(f"Token expired or not found for user {user_id}, requesting new authorization...")

    # Get the authorization code by running the local server to handle the redirect
    authorization_code = get_authorization_code(driver, client_id, redirect_uri, "user:write:chat user:bot", username, password)
    
    if authorization_code:
        # Exchange the authorization code for an access token
        token_response = get_access_token_with_code(client_id, client_secret, redirect_uri, authorization_code)
        
        if token_response:
            # Get the user ID from token response (which is important for saving unique tokens per user)
            access_token = token_response['access_token']
            expires_in = token_response['expires_in']
            user_id = token_response.get('user_id', user_id)  # Assuming user_id is returned

            # Store token and expiration time
            token_data = {
                'access_token': access_token,
                'expires_at': time.time() + expires_in,
                'user_id': user_id
            }
            save_token(user_id, token_data)
            print(f"New access token saved for user {user_id}: {token_data}")
            return access_token
        else:
            print("Failed to obtain access token.")
    else:
        print("Failed to retrieve authorization code.")
    
    return None

def validate_token(access_token, client_id):
    """Validate access token to check scopes."""
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Client-Id': client_id
    }
    response = requests.get("https://id.twitch.tv/oauth2/validate", headers=headers)
    
    if response.status_code == 200:
        print(f"Token is valid. Scopes: {response.json()['scopes']}")
        return True
    else:
        print(f"Invalid token. Status code: {response.status_code}. Response: {response.text}")
        return False
