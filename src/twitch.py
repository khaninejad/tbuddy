import base64
import random
import time
import requests
import os
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC

from load_assistant_type import load_assistant_type
from utils import (
    GREEN_TEXT,
    RED_TEXT,
    RESET_TEXT,
    countdown_timer,
    print_error,
    print_info,
)



def is_channel_offline(driver):
    """Check if the Twitch channel is offline by checking for the presence of the chatbox."""
    try:

        chatbox = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div.chat-line__message"))
        )

        print_info("Channel is online.")
        return False
    except Exception as e:

        print_info("Channel is offline or an error occurred.")
        return True


def twitch_login(driver, username, password, auth_url="https://twitch.tv/login"):
    """Login to Twitch using the provided username and password."""
    try:

        print_info("Navigating to the Twitch login page...")
        driver.uc_open(auth_url)
        login_wait_interval = 5
        countdown_timer(login_wait_interval, "Waiting for {} seconds before login...")
        time.sleep(login_wait_interval)

        username_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "login-username"))
        )
        username_input.send_keys(username)

        password_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "password-input"))
        )
        password_input.send_keys(password)

        login_button = driver.find_element(
            By.CSS_SELECTOR, 'button[data-a-target="passport-login-button"]'
        )
        login_button.click()

        login_success_interval = 5
        countdown_timer(
            login_success_interval,
            "Wait {} for a short while to ensure login is successful",
        )
        time.sleep(login_success_interval)
        try:

            modal_header = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located(
                    (
                        By.XPATH,
                        '//h2[@id="modal-root-header" and contains(text(), "Verify login code")]',
                    )
                )
            )
            print_info("2FA modal detected, Please enter the 2FA code and click Send")

            verification_code = input(
                f"{RED_TEXT}Enter the 6-digit verification code sent to your device: {RESET_TEXT}"
            )

            if len(verification_code) != 6:
                raise ValueError("Verification code must be 6 digits")

            for i, digit in enumerate(verification_code, start=1):
                digit_input = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located(
                        (By.CSS_SELECTOR, f'input[aria-label="Digit {i}"]')
                    )
                )
                digit_input.send_keys(digit)
                print_info(f"Entered digit {digit}")

            wait_submit_button = 10
            countdown_timer(wait_submit_button, "Wait {} for submit buttton")
            time.sleep(wait_submit_button)
            submit_button = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, 'div[data-a-target="tw-core-button-label-text"]')
                )
            )
            submit_button.click()
            print_info("Submit button clicked")

            wait_login_compleation = 10
            countdown_timer(wait_login_compleation, "Wait {} for login compleation")
            time.sleep(wait_login_compleation)
            print_info(f"{GREEN_TEXT}Successfully logged in as {username}{RESET_TEXT}")

        except Exception as e:
            print_error("No 2FA required during 2FA process", e)
            pass

    except Exception as e:
        print_error("Failed to log in or already logged in", e)


def post_twitch_message(broadcaster_id, sender_id, message, client_id, access_token):
    """Send a message to the Twitch chat."""
    url = "https://api.twitch.tv/helix/chat/messages"

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Client-Id": client_id,
        "Content-Type": "application/json",
    }

    payload = {
        "broadcaster_id": broadcaster_id,
        "sender_id": sender_id,
        "message": message,
    }

    try:
        response = requests.post(url, headers=headers, json=payload)

        if response.status_code == 204:
            print_info(
                f"{GREEN_TEXT}Successfully posted message: {message}{RESET_TEXT}"
            )
        else:
            print_error(
                f"Failed to post message. Status code: {response.status_code}. Response: {response.text}"
            )
    except Exception as e:
        print_error("Error while sending message", e)


def get_last_5_chat_messages(driver):
    """Get the last 5 messages from the Twitch chat."""
    try:
        chat_messages = driver.find_elements(By.CSS_SELECTOR, "div.chat-line__message")
        last_5_messages = [msg.text for msg in chat_messages[-10:]]
        return last_5_messages
    except Exception as e:
        print_error("Error fetching chat messages", e)
        return []


def click_start_watching(driver):
    """Click the 'Start Watching' button if it exists."""
    try:
        WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable(
                (
                    By.XPATH,
                    '//button[@data-a-target="content-classification-gate-overlay-start-watching-button"]',
                )
            )
        ).click()
        print_info("Clicked 'Start Watching' button.")
    except Exception as e:
        print_error("No 'Start Watching' button found", e)


def dismiss_subtember_callout(driver):
    """Click the 'Dismiss Subtember Callout' button if it exists."""
    try:

        WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable(
                (By.XPATH, '//button[@aria-label="Dismiss Subtember Callout"]')
            )
        ).click()
        print_info("Dismissed 'Subtember Callout' ad.")
    except Exception as e:
        print_error("No 'Subtember Callout' button found", e)


def accept_cookies(driver):
    """Click the 'Accept' button on the cookies consent banner if it exists."""
    try:

        WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable(
                (By.XPATH, '//button[@data-a-target="consent-banner-accept"]')
            )
        ).click()
        print_info("Clicked 'Accept' on the cookies consent banner.")
    except Exception as e:
        print_error("No 'Accept' button for cookies consent found", e)


from selenium.webdriver import ActionChains


def click_captions_button(driver):
    """Hover over the video player and click the 'Captions (CC)' button if it exists."""
    try:

        video_player = driver.find_element(
            By.XPATH, '//div[contains(@class, "video-player")]'
        )
        actions = ActionChains(driver)
        actions.move_to_element(video_player).perform()
        print_info("Hovered over video player.")

        WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable(
                (By.XPATH, '//button[@aria-label="Captions (c)"]')
            )
        ).click()
        print_info("Clicked 'Captions (CC)' button.")
    except Exception as e:
        print_error("No 'Captions (CC)' button found", e)


def take_screenshots_and_describe(
    driver,
    interval_range,
    run_duration,
    output_folder,
    description_folder,
    api_key,
    game_name,
    comment_folder,
    broadcaster_id,
    sender_id,
    client_id,
    access_token,
    stream_language,
    username_arg,
):
    """Take screenshots and describe them immediately, skipping the first screenshot."""
    start_time = time.time()
    screenshot_count = 0

    while (time.time() - start_time) < run_duration:

        wait_for_content(driver)

        if screenshot_count == 0:

            screenshot_filename = os.path.join(
                output_folder, f"screenshot_{screenshot_count}.png"
            )
            driver.save_screenshot(screenshot_filename)
            print_info(
                f"Screenshot {screenshot_count} saved as {screenshot_filename} (ignored)"
            )
        else:

            screenshot_filename = os.path.join(
                output_folder, f"screenshot_{screenshot_count}.png"
            )
            driver.save_screenshot(screenshot_filename)
            print_info(f"Screenshot {screenshot_count} saved as {screenshot_filename}")

            description = describe_image(screenshot_filename, api_key, game_name)
            if description:
                description_filename = os.path.join(
                    description_folder, f"screenshot_{screenshot_count}.txt"
                )
                with open(description_filename, "w") as desc_file:
                    desc_file.write(description)
                print_info(f"Description saved as {description_filename}")
            else:
                print_info(
                    f"{RED_TEXT}No description returned for screenshot {screenshot_count}{RESET_TEXT}"
                )

            chat_messages = get_last_5_chat_messages(driver)

            comments = generate_comments(
                api_key, game_name, description, chat_messages, stream_language
            )
            if comments:

                comment_list = comments.split("\n")

                random_comment = random.choice(comment_list)
                post_twitch_message(
                    broadcaster_id, sender_id, random_comment, client_id, access_token
                )
                print_info(f"{GREEN_TEXT}Posted comment: {random_comment}{RESET_TEXT}")

                comment_filename = os.path.join(comment_folder, f"comments.txt")
                with open(comment_filename, "a") as comment_file:
                    comment_file.write(comments + "\n")
                print_info(f"Comments saved as {comment_filename}")
            else:
                print_error(
                    f"{RED_TEXT}No comments generated for screenshot {screenshot_count}{RESET_TEXT}"
                )

        screenshot_count += 1
        min_interval, max_interval = map(int, interval_range.split(","))
        interval = random.randint(min_interval, max_interval)
        countdown_timer(interval, "Waiting for {} seconds before the next analysis...")


def wait_for_content(driver, timeout=20):
    """Wait for specific content to be visible on the page."""
    try:
        WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "video"))
        )
        print_info("Content is visible")
    except Exception as e:
        print_error("Error while waiting for content", e)


def encode_image(image_path):
    """Encode the image to base64."""
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")


def describe_image(image_path, api_key, game_name):
    """Describe the image using OpenAI API."""
    try:
        base64_image = encode_image(image_path)

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        }

        payload = {
            "model": "gpt-4o-mini",
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": f"Analyze the following screenshot from the game '{game_name}'. "
                            "Provide a detailed description of the scene, characters, and any relevant elements visible in the image. "
                            "Describe the setting, actions, and notable details as if explaining to someone who cannot see the image. "
                            "Describe quest objective and summarize what needs to be completed on the quest"
                            "Describe interesting things that you find from this screenshot or comments and IGNORE advertisements"
                            "Describe What streamer or presenter talking in details by reading CC on video",
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{base64_image}"
                            },
                        },
                    ],
                }
            ],
            "max_tokens": 500,
        }

        response = requests.post(
            "https://api.openai.com/v1/chat/completions", headers=headers, json=payload
        )

        if response.status_code == 200:
            description = response.json()["choices"][0]["message"]["content"]
            return description
        else:
            print_error(
                f"API error for {image_path}. Status code: {response.status_code}. Response: {response.text}"
            )
            return None

    except Exception as e:
        print_error("Error while describing {image_path}:", e)
        return None


def toggle_side_nav(driver):
    try:

        toggle_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable(
                (By.CSS_SELECTOR, 'button[data-a-target="side-nav-arrow"]')
            )
        )
        toggle_button.click()
        print_info("Toggled the side navigation.")
    except Exception as e:
        print_error("Error while toggling side navigation")


def generate_comments(
    api_key,
    game_name,
    description,
    chat_messages_text,
    stream_language,
    assistant_name="IShowSpeed",
):
    """Generate Twitch-style comments without usernames for the current game context."""

    prompt = f"""
    Generate a ONE SHORT ({random.randint(2, 30)} words) comment for a Twitch stream in '{stream_language}'.

    Incorporate gamer slang and emotes where appropriate, but AVOID excessive use of smiley faces or other emoticons. Avoid using hashtags and motivational phrase at the end.

    The following is a description of the game's scene: {description}
    The following are recent chat messages from the stream: {chat_messages_text}.
    - Do not include any quotes, numbers, bullet points, or hyphens before any of the comments. The comments should appear as plain text without any formatting symbols.
    """

    try:
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        }

        assistant_type = load_assistant_type(assistant_name)
        if assistant_type:
            payload = {
                "model": "gpt-4o-mini",
                "messages": [
                    {"role": "system", "content": assistant_type},
                    {"role": "user", "content": prompt},
                ],
                "max_tokens": 300,
            }
        else:

            payload = {
                "model": "gpt-4o-mini",
                "messages": [
                    {
                        "role": "system",
                        "content": "Act as a generic virtual assistant, enhancing audience engagement, assisting during livestreams, and supporting task management.",
                    },
                    {"role": "user", "content": prompt},
                ],
                "max_tokens": 300,
            }

        response = requests.post(
            "https://api.openai.com/v1/chat/completions", headers=headers, json=payload
        )

        if response.status_code == 200:
            comments = response.json()["choices"][0]["message"]["content"]

            plain_comments = (
                comments.replace("•", "").replace("-", "").replace('"', "").strip()
            )

            plain_comments_list = plain_comments.split("\n")
            filtered_comments = []

            for comment in plain_comments_list:

                clean_comment = comment.strip()
                if clean_comment and not clean_comment.startswith(
                    ("- ", "•", '"', "'", "*")
                ):
                    filtered_comments.append(clean_comment)

            final_comments = "\n".join(filtered_comments)

            return final_comments
        else:
            print_error(
                f"Error generating comments. Status code: {response.status_code}. Response: {response.text}"
            )
            return None

    except Exception as e:
        print_error("Error while generating comments", e)
        return None
