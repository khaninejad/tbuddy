import json
import os
import sys
import time
import requests
import warnings
from dotenv import load_dotenv
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support import expected_conditions as EC
from seleniumbase import SB
from seleniumbase import Driver

from authorization import get_access_token, validate_token
from twitch import accept_cookies, click_captions_button, click_start_watching, dismiss_subtember_callout, is_channel_offline, take_screenshots_and_describe, toggle_side_nav, twitch_login
from utils import print_error, countdown_timer

warnings.filterwarnings("ignore", category=DeprecationWarning)

# Load environment variables from .env file
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
            return user_data[0]['id']  # Return the user ID (broadcaster_id or sender_id)
        else:
            print(f"{RED_TEXT}No user found with username: {username}{RESET_TEXT}")
    else:
        print_error(f"Fetching user data. Status code: {response.status_code}. Response: {response.text}")
    return None



def clean_screenshot_folder(parent_folder, output_folder_name):
    """Remove all files in the specified output_folder within parent_folder."""
    
    # Check if parent_folder or output_folder_name is None
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
                print_error(f"Failed to delete {file_path}. Reason:")
    else:
        print_error(f"Folder {output_folder} does not exist.")


def load_all_credentials(json_file="credentials.json"):
    """Load all credentials from the JSON file."""
    try:
        with open(json_file, "r") as file:
            credentials = json.load(file)
        return credentials
    except FileNotFoundError:
        raise FileNotFoundError(f"Credentials file {json_file} not found.")
    except json.JSONDecodeError:
        raise ValueError(f"Error parsing {json_file}. Please ensure it contains valid JSON.")

def get_credentials_for_user(username, json_file="credentials.json"):
    """Load the username and password from the JSON file for a specific user."""
    credentials = load_all_credentials(json_file)
    
    if username in credentials:
        return credentials[username]["username"], credentials[username]["password"]
    else:
        raise ValueError(f"Username {username} not found in {json_file}")

def create_new_chrome_instance(sender_id):
    # Create a unique directory for this Chrome instance
    user_data_dir = os.path.join(sender_id, f"chrome_profile")

    # Ensure the directory exists
    if not os.path.exists(user_data_dir):
        os.makedirs(user_data_dir)
    
    # Create a new Chrome instance
    driver = Driver(uc=True, headless2=True, user_data_dir=user_data_dir, chromium_arg="--mute-audio")
    
    return driver

def get_chrome_instance(username, json_file="credentials.json"):
    """Return a Chrome instance for the given username, creating one if necessary."""
    # Load credentials to validate the username exists
    credentials = load_all_credentials(json_file)
    
    if username in credentials:
        # Check if a driver for this username already exists
        if username not in user_drivers:
            # Create a new Chrome instance for the user
            driver = create_new_chrome_instance(username)
            # Store the driver in the user_drivers dictionary
            user_drivers[username] = driver
        return user_drivers[username]
    else:
        raise ValueError(f"Username {username} not found in {json_file}")

def main():
    """Main function to start the bot."""
    # threading.Thread(target=monitor_usage, daemon=True).start()
    # Load environment variables

    if len(sys.argv) < 4:
        print("Usage: python bot.py <username> <strean_username> <game_name>")
        sys.exit(1)


    # Get the username from command line argument
    username_arg = sys.argv[1]
    strean_username = sys.argv[2]
    game_name = sys.argv[3]

    # Load the username and password from the JSON file
    try:
        username, password = get_credentials_for_user(username_arg)
    except ValueError as e:
        print(e)
        sys.exit(1)

    stream_url = f"https://www.twitch.tv/{strean_username}"
    stream_language = os.getenv("STREAM_LANGUAGE")
    
    # Convert to integers to avoid string comparison issues
    interval = os.getenv("SCREENSHOT_INTERVAL", "30,90")  # Convert to int
    run_duration = int(os.getenv("RUN_DURATION", 600))     # Convert to int (seconds)

    output_folder = os.getenv("OUTPUT_FOLDER", "screenshots")
    description_folder = os.getenv("DESCRIPTION_FOLDER", "output")
    comment_folder = os.getenv("COMMENTS_FOLDER", "comments")
    api_key = os.getenv("OPENAI_API_KEY")

    broadcaster_id = os.getenv("TWITCH_BROADCASTER_ID")
    sender_id = os.getenv("TWITCH_SENDER_ID")
    client_id = os.getenv("TWITCH_CLIENT_ID")
    client_secret = os.getenv("TWITCH_CLIENT_SECRET")
    redirect_uri = os.getenv("TWITCH_REDIRECT_URI")

    # clean_screenshot_folder(username_arg, userdata)
    driver = get_chrome_instance(username_arg)

  
    # Step 3: Exchange the authorization code for an access token
    access_token = get_access_token(driver, username, client_id, client_secret, redirect_uri, username, password)
    if not access_token or not validate_token(access_token, client_id):
        # Step 4: Validate the access token
        print_error("Invalid access token. Exiting.")
        return

    broadcaster_id = get_user_id(strean_username, client_id, access_token)
    sender_id = get_user_id(username, client_id, access_token)

    if broadcaster_id and sender_id:
        print("Successful login")
        clean_screenshot_folder(username_arg, output_folder)
        clean_screenshot_folder(username_arg, description_folder)
        clean_screenshot_folder(username_arg, comment_folder)
    else:
        print_error("Failed to retrieve broadcaster or sender IDs. Cannot send message.")


    twitch_login(driver, username, password)


    print("Navigating to stream URL")
    driver.get(stream_url)
    wait_stream_start = 5
    countdown_timer(wait_stream_start, "Waiting for {} to start watching...")
    time.sleep(wait_stream_start)  # Allow extra time for the page to load
    # if is_channel_offline(driver):
    #     driver.quit()
    #     sys.exit()

    click_start_watching(driver)
    toggle_side_nav(driver)
    accept_cookies(driver)
    click_captions_button(driver)
    # dismiss_subtember_callout(driver)


    # Ensure that `run_duration` is passed as an integer here
    take_screenshots_and_describe(driver, interval, run_duration, output_folder, description_folder, api_key, game_name, comment_folder, broadcaster_id, sender_id, client_id, access_token, stream_language, username_arg)

    driver.quit()

if __name__ == '__main__':
    main()
