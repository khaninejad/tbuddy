import json
import os
import sys
import time
import requests
import warnings
from config import CLIENT_ID
from dotenv import load_dotenv
from seleniumbase import Driver

from authorization import get_access_token, validate_token
from twitch import (
    accept_cookies,
    click_captions_button,
    click_start_watching,
    take_screenshots_and_describe,
    toggle_side_nav,
    twitch_login,
)
from utils import print_error, countdown_timer, print_info

warnings.filterwarnings("ignore", category=DeprecationWarning)

load_dotenv(override=True)
user_drivers = {}


def get_user_id(username, client_id, access_token):
    """Fetch user ID (broadcaster or sender) based on username"""
    url = f"https://api.twitch.tv/helix/users?login={username}"

    headers = {"Authorization": f"Bearer {access_token}", "Client-Id": client_id}

    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        user_data = response.json().get("data", [])
        if user_data:
            return user_data[0]["id"]
        else:
            print_error(f"No user found with username: {username}")
    else:
        print_error(
            f"Fetching user data. Status code: {response.status_code}. Response: {response.text}"
        )
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
                    print_info(f"Deleted {file_path}")
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
        raise ValueError(
            f"Error parsing {json_file}. Please ensure it contains valid JSON."
        )


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

    driver = Driver(
        uc=True,
        headless2=True,
        user_data_dir=user_data_dir,
        chromium_arg="--mute-audio",
    )

    return driver


def get_chrome_instance(username, json_file="config.json"):
    """Return a Chrome instance for the given username, creating one if necessary."""
    credentials = load_all_credentials(json_file)

    usernames = [user["username"] for user in credentials["users"]]

    if username in usernames:

        if username not in user_drivers:
            driver = create_new_chrome_instance(username)
            user_drivers[username] = driver
        return user_drivers[username]
    else:
        raise ValueError(f"Username {username} not found in {json_file}")


def ensure_folders_exist(username):
    """Ensure the required folders exist under the user folder."""
    base_user_folder = os.path.join("users", username)
    os.makedirs(
        base_user_folder, exist_ok=True
    )  # Create user folder if it doesn't exist

    # Create subfolders for the user
    comments_folder = os.path.join(base_user_folder, "comments")
    screenshots_folder = os.path.join(base_user_folder, "screenshots")
    game_analysis_folder = os.path.join(base_user_folder, "game_analysis")
    user_profile_folder = os.path.join(base_user_folder, "user_profile")

    os.makedirs(comments_folder, exist_ok=True)
    os.makedirs(screenshots_folder, exist_ok=True)
    os.makedirs(game_analysis_folder, exist_ok=True)
    os.makedirs(user_profile_folder, exist_ok=True)

    return {
        "comments": comments_folder,
        "screenshots": screenshots_folder,
        "game_analysis": game_analysis_folder,
        "user_profile": user_profile_folder,
    }



def main():
    """Main function to start the bot."""
    print_info("Starting the tbuddy...")

    if len(sys.argv) < 7:
        print_info("Usage: python bot.py invalid")
        sys.exit(1)

    username = sys.argv[1]
    password = sys.argv[2]
    stream_username = sys.argv[3]
    game_name = sys.argv[4]
    api_key = sys.argv[5]
    stream_language = sys.argv[6]
    interval = sys.argv[7]
    assistant_type = sys.argv[8]

    stream_url = f"https://www.twitch.tv/{stream_username}"

    run_duration = int(os.getenv("RUN_DURATION", 600))

    broadcaster_id = os.getenv("TWITCH_BROADCASTER_ID")
    sender_id = os.getenv("TWITCH_SENDER_ID")

    driver = get_chrome_instance(username)
    
    twitch_login(driver, username, password)

    access_token = get_access_token(
        driver, username, username
    )
    
    if not access_token or not validate_token(access_token, CLIENT_ID):
        print_error("Invalid access token. Exiting.")
        return

    broadcaster_id = get_user_id(stream_username, CLIENT_ID, access_token)
    sender_id = get_user_id(username, CLIENT_ID, access_token)

    user_folders = ensure_folders_exist(username)
    print_info(f"Folder structure created for user: {username}")

    comments_folder = user_folders["comments"]
    screenshots_folder = user_folders["screenshots"]
    output_folder = user_folders["game_analysis"]

    

    print_info("Navigating to stream URL")
    driver.get(stream_url)
    wait_stream_start = 5
    countdown_timer(wait_stream_start, "Waiting for stream to start watching...")
    time.sleep(wait_stream_start)

    click_start_watching(driver)
    toggle_side_nav(driver)
    accept_cookies(driver)
    click_captions_button(driver)

    take_screenshots_and_describe(
        driver,
        interval,
        run_duration,
        screenshots_folder,
        output_folder,
        api_key,
        game_name,
        comments_folder,
        broadcaster_id,
        sender_id,
        CLIENT_ID,
        access_token,
        stream_language,
        username,
        assistant_type
    )

    driver.quit()


if __name__ == "__main__":
    main()
