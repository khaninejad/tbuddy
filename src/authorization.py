import platform
import subprocess
import threading
import time
import json
import os
import uuid
import requests
from urllib.parse import urlparse, parse_qs
from http.server import BaseHTTPRequestHandler, HTTPServer

import urllib

from twitch import authorize_client, twitch_login
from utils import print_error, print_info


def load_token(user_id):
    """Load access token and its expiration time from the file specific to the user."""
    token_file = get_token_file(user_id)
    if os.path.exists(token_file):
        with open(token_file, "r") as f:
            return json.load(f)
    return None

def run_server(username):
    """Function to run server.py in a separate thread."""
    try:
        subprocess.run(["python", "server.py", username])
    except Exception as e:
        print_error(f"Failed to start server.py: {e}")
        

def get_access_token(driver, user_id, client_id, redirect_uri, scopes, username):
    """Get a new access token using the Implicit Grant Flow."""
    token_data = load_token(user_id)

    if token_data and not is_token_expired(token_data):
        print_info(f"Using stored access token for user {user_id}.")
        return token_data["access_token"]

    print_info(f"Token expired or not found for user {user_id}, requesting new authorization...")
    
    server_thread = threading.Thread(target=run_server, args=(username,))
    server_thread.start()
    print_info(f"Started server.py with username: {username} in a separate thread.")

    open_auth_url(driver, client_id, redirect_uri, scopes)
    
    token_data = load_token(user_id)
    return token_data['access_token']


def kill_port(port):
    """Kill the process using the specified port."""
    system_platform = platform.system()

    if system_platform == "Windows":
        command = f"netstat -ano | findstr :{port}"
        result = os.popen(command).read()
        if result:
            pid = result.strip().split()[-1]
            os.system(f"taskkill /PID {pid} /F")
            print_info(f"Process on port {port} killed (PID: {pid}).")
        else:
            print_info(f"No process found on port {port}.")
    else:
        command = f"lsof -ti :{port} | xargs kill -9"
        os.system(command)
        print_info(f"Killed process on port {port}.")


def validate_token(access_token, client_id):
    """Validate the access token to confirm its authenticity."""
    headers = {"Authorization": f"Bearer {access_token}", "Client-Id": client_id}
    response = requests.get("https://id.twitch.tv/oauth2/validate", headers=headers)
    
    if response.status_code == 200:
        print_info("Token is valid.")
        return True
    else:
        print_error(f"Invalid token. Status code: {response.status_code}.")
        return False

    
def open_auth_url(driver, client_id, redirect_uri, scopes):
    auth_url = generate_auth_url(client_id, redirect_uri, scopes)
    print(auth_url)
    driver.open(auth_url)
    print("Opening authorization URL:", auth_url)
    final_url = driver.current_url
    print_info(f"Final URL after auth: {final_url}")
    authorize_client(driver, final_url)

def get_token_file(user_id, base_folder="users"):
    """Get the token file path for a specific user."""
    return os.path.join(base_folder, user_id, "token.json")


def save_token(user_id, token_data, base_folder="users"):
    """Save access token and its expiration time to a file specific to the user."""
    token_file = get_token_file(user_id, base_folder)
    token_folder = os.path.dirname(token_file)

    # Create the user folder if it doesn't exist
    if not os.path.exists(token_folder):
        os.makedirs(token_folder)

    with open(token_file, "w") as f:
        json.dump(token_data, f)


def is_token_expired(token_data):
    """Check if the access token is expired."""
    return time.time() > token_data["expires_at"]


def generate_auth_url(client_id, redirect_uri, scopes):
    """Generate Twitch OAuth authorization URL for Implicit Grant Flow."""
    # Join scopes with a space and encode the entire list as one parameter
    scopes_encoded = urllib.parse.quote(" ".join(scopes))  
    # URL-encode the redirect URI
    redirect_uri_encoded = urllib.parse.quote(redirect_uri)
    # Generate a random state parameter for security
    state = str(uuid.uuid4()).replace('-', '')
    
    auth_url = (
        f"https://id.twitch.tv/oauth2/authorize?"
        f"response_type=token&client_id={client_id}&redirect_uri={redirect_uri_encoded}&scope={scopes_encoded}&state={state}"
    )
    return auth_url