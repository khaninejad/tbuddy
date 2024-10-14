import json
import os
import sys
import time
import requests
import warnings
from dotenv import load_dotenv
from seleniumbase import Driver

from authorization import get_access_token, validate_token
from twitch import accept_cookies, click_captions_button, click_start_watching, take_screenshots_and_describe, toggle_side_nav, twitch_login
from utils import print_error, countdown_timer

warnings.filterwarnings("ignore", category=DeprecationWarning)

load_dotenv(override=True)
user_drivers = {}


def get_user_id(username, client_id, access_token):
    """Fetch user ID (broadcaster or sender) based on username"""
    url = f"https://api.twitch.tv/helix/users?login={username}"
    
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Client-Id': client_id
    }
    
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        user_data = response.json().get('data', [])
        if user_data:
            return user_data[0]['id']  
        else:
            print(f"No user found with username: {username}")
    else:
        print_error(f"Fetching user data. Status code: {response.status_code}. Response: {response.text}")
    return None


def clean_screenshot_folder(parent_folder, output_folder_name):
    """Remove all files in the specified output_folder within parent_folder."""
    if parent_folder is None or output_folder_name is None:
        print_error("parent_folder or output_folder_name is None.")
        return
    
    output_folder = os.path.join(parent_folder, output_folder_name)
    
    if os.path.exists(output_folder):
        for filename in os.listdir(output_folder):
            file_path = os.path.join(output_folder, filename)
            try:
                if os.path.isfile(file_path):
                    os.remove(file_path)
                    print(f"Deleted {file_path}")
            except Exception as e:
                print_error(f"Failed to delete {file_path}. Reason: {e}")
    else:
        print_error(f"Folder {output_folder} does not exist.")


def load_all_credentials(json_file="config.json"):
    """Load all credentials from the JSON file."""
    try:
        with open(json_file, "r") as file:
            credentials = json.load(file)
        return credentials
    except FileNotFoundError:
        raise FileNotFoundError(f"Credentials file {json_file} not found.")
    except json.JSONDecodeError:
        raise ValueError(f"Error parsing {json_file}. Please ensure it contains valid JSON.")


def get_credentials_for_user(username, json_file="config.json"):
    """Load the username and password from the JSON file for a specific user."""
    credentials = load_all_credentials(json_file)
    
    if username in credentials:
        return credentials[username]["username"], credentials[username]["password"]
    else:
        raise ValueError(f"Username {username} not found in {json_file}")


def create_new_chrome_instance(sender_id):
    user_data_dir = os.path.join(f"users", sender_id, "chrome_profile")

    if not os.path.exists(user_data_dir):
        os.makedirs(user_data_dir)
    
    driver = Driver(uc=True, headless2=True, user_data_dir=user_data_dir, chromium_arg="--mute-audio")
    
    return driver


def get_chrome_instance(username, json_file="config.json"):
    """Return a Chrome instance for the given username, creating one if necessary."""
    credentials = load_all_credentials(json_file)
    
    # Extract a list of usernames from the credentials
    usernames = [user["username"] for user in credentials["users"]]
    
    if username in usernames:
        # Only create a new Chrome instance if one doesn’t already exist for the user
        if username not in user_drivers:
            driver = create_new_chrome_instance(username)
            user_drivers[username] = driver
        return user_drivers[username]
    else:
        raise ValueError(f"Username {username} not found in {json_file}")


def ensure_folders_exist(username):
    """Ensure the comments, output, and screenshots folders exist under the user folder."""
    base_user_folder = os.path.join("users", username)
    
    comments_folder = os.path.join(base_user_folder, "comments")
    output_folder = os.path.join(base_user_folder, "output")
    screenshots_folder = os.path.join(base_user_folder, "screenshots")
    
    # Create the directories if they don't exist
    os.makedirs(comments_folder, exist_ok=True)
    os.makedirs(output_folder, exist_ok=True)
    os.makedirs(screenshots_folder, exist_ok=True)

    return comments_folder, output_folder, screenshots_folder


def main():
    """Main function to start the bot."""
    print("Starting the bot...")
    
    if len(sys.argv) < 4:
        print("Usage: python bot.py <username> <strean_username> <game_name>")
        sys.exit(1)

    username = sys.argv[1]
    password = sys.argv[2]
    stream_username = sys.argv[3]
    game_name = sys.argv[4]
    api_key = sys.argv[5]
    stream_language = sys.argv[5]

    stream_url = f"https://www.twitch.tv/{stream_username}"

    interval = os.getenv("SCREENSHOT_INTERVAL", "30,90")
    run_duration = int(os.getenv("RUN_DURATION", 600))     

    broadcaster_id = os.getenv("TWITCH_BROADCASTER_ID")
    sender_id = os.getenv("TWITCH_SENDER_ID")
    client_id = os.getenv("TWITCH_CLIENT_ID")
    client_secret = os.getenv("TWITCH_CLIENT_SECRET")
    redirect_uri = os.getenv("TWITCH_REDIRECT_URI")

    # Get the Chrome instance
    driver = get_chrome_instance(username)

    # Get access token
    access_token = get_access_token(driver, username, client_id, client_secret, redirect_uri, username, password)
    if not access_token or not validate_token(access_token, client_id):
        print_error("Invalid access token. Exiting.")
        return

    # Fetch broadcaster and sender IDs
    broadcaster_id = get_user_id(stream_username, client_id, access_token)
    sender_id = get_user_id(username, client_id, access_token)

    if broadcaster_id and sender_id:
        print("Successful login")
        
        # Ensure the necessary folders exist
        comments_folder, output_folder, screenshots_folder = ensure_folders_exist(username)
        
        # Clean up the folders
        clean_screenshot_folder(username, "screenshots")
        clean_screenshot_folder(username, "output")
        clean_screenshot_folder(username, "comments")
    else:
        print_error("Failed to retrieve broadcaster or sender IDs. Cannot send message.")
        return

    # Log into Twitch and start automation
    twitch_login(driver, username, password)

    print("Navigating to stream URL")
    driver.get(stream_url)
    wait_stream_start = 5
    countdown_timer(wait_stream_start, "Waiting for stream to start watching...")
    time.sleep(wait_stream_start)
    
    click_start_watching(driver)
    toggle_side_nav(driver)
    accept_cookies(driver)
    click_captions_button(driver)

    # Take screenshots and descriptions
    take_screenshots_and_describe(driver, interval, run_duration, screenshots_folder, output_folder, api_key, game_name, comments_folder, broadcaster_id, sender_id, client_id, access_token, stream_language, username)

    driver.quit()

if __name__ == '__main__':
    main()