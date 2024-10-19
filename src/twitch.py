import base64
import random
import time
import requests
import os
from utils import GREEN_TEXT, RED_TEXT, RESET_TEXT, countdown_timer, print_error
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC

def is_channel_offline(driver):
    """Check if the Twitch channel is offline by checking for the presence of the chatbox."""
    try:
        # Wait until the chatbox appears in the DOM (class name of the chat container on Twitch)
        chatbox = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div.chat-line__message"))
        )
        
        # If the chatbox is found, the channel is online
        print("Channel is online.")
        return False
    except Exception as e:
        # If the chatbox is not found, it means the channel is likely offline
        print("Channel is offline or an error occurred.")
        return True
    
def twitch_login(driver, username, password, auth_url="https://twitch.tv/login"):
    """Login to Twitch using the provided username and password."""
    try:
        # Navigate to the Twitch login page
        print("Navigating to the Twitch login page...")
        driver.uc_open(auth_url)
        login_wait_interval =5
        countdown_timer(login_wait_interval, "Waiting for {} seconds before login...")
        time.sleep(login_wait_interval)  # Allow the page to load
        
        # Wait for the username input to be present and enter the username
        username_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, 'login-username'))
        )
        username_input.send_keys(username)

        # Wait for the password input to be present and enter the password
        password_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, 'password-input'))
        )
        password_input.send_keys(password)
        
        # Click the 'Login' button
        login_button = driver.find_element(By.CSS_SELECTOR, 'button[data-a-target="passport-login-button"]')
        login_button.click()

        # Wait for a short while to ensure login is successful
        login_success_interval = 5
        countdown_timer(login_success_interval, "Wait {} for a short while to ensure login is successful")
        time.sleep(login_success_interval)
        try:
            # Wait for the 2FA code input field
            modal_header = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, '//h2[@id="modal-root-header" and contains(text(), "Verify login code")]'))
            )
            print("2FA modal detected")

            # Prompt the user for the verification code
            verification_code = input(f"{RED_TEXT}Enter the 6-digit verification code sent to your device: {RESET_TEXT}")

            # Ensure the code is 6 digits
            if len(verification_code) != 6:
                raise ValueError("Verification code must be 6 digits")

            # Find each input field for the 6 digits
            for i, digit in enumerate(verification_code, start=1):
                digit_input = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, f'input[aria-label="Digit {i}"]'))
                )
                digit_input.send_keys(digit)
                print(f"Entered digit {digit}")

            # Click the 'Submit' button to verify the code
            wait_submit_button = 10
            countdown_timer(wait_submit_button, "Wait {} for submit buttton")
            time.sleep(wait_submit_button)
            submit_button = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'div[data-a-target="tw-core-button-label-text"]'))
            )
            submit_button.click()
            print("Submit button clicked")
            # Wait for login completion
            wait_login_compleation = 10
            countdown_timer(wait_login_compleation, "Wait {} for login compleation")
            time.sleep(wait_login_compleation)
            print(f"{GREEN_TEXT}Successfully logged in as {username}{RESET_TEXT}")
        
        except Exception as e:
            print(f"No 2FA required or error occurred during 2FA process")
            pass  # Continue if no 2FA is required or an error occurred during 2FA
        
    except Exception as e:
        print_error(f"Failed to log in or already logged in")
        # driver.quit()
        # sys.exit(1)

def post_twitch_message(broadcaster_id, sender_id, message, client_id, access_token):
    """Send a message to the Twitch chat."""
    url = 'https://api.twitch.tv/helix/chat/messages'
    
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Client-Id': client_id,
        'Content-Type': 'application/json'
    }
    
    payload = {
        'broadcaster_id': broadcaster_id,
        'sender_id': sender_id,
        'message': message
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload)
        
        if response.status_code == 204:
            print(f"{GREEN_TEXT}Successfully posted message: {message}{RESET_TEXT}")
        else:
            print_error(f"Failed to post message. Status code: {response.status_code}. Response: {response.text}")
    except Exception as e:
        print_error(f"Error while sending message: {e}")


def get_last_5_chat_messages(driver):
    """Get the last 5 messages from the Twitch chat."""
    try:
        chat_messages = driver.find_elements(By.CSS_SELECTOR, 'div.chat-line__message')  # Adjust selector if necessary
        last_5_messages = [msg.text for msg in chat_messages[-10:]]  # Get the last 5 messages
        return last_5_messages
    except Exception as e:
        print_error(f"Error fetching chat messages: {e}")
        return []

def click_start_watching(driver):
    """Click the 'Start Watching' button if it exists."""
    try:
        WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable(
                (By.XPATH, '//button[@data-a-target="content-classification-gate-overlay-start-watching-button"]')
            )
        ).click()
        print("Clicked 'Start Watching' button.")
    except Exception as e:
        print_error(f"No 'Start Watching' button found")

def dismiss_subtember_callout(driver):
    """Click the 'Dismiss Subtember Callout' button if it exists."""
    try:
        # Wait for the button to be clickable, then click it
        WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable(
                (By.XPATH, '//button[@aria-label="Dismiss Subtember Callout"]')
            )
        ).click()
        print("Dismissed 'Subtember Callout' ad.")
    except Exception as e:
        print_error(f"No 'Subtember Callout' button found or error occurred: {e}")

def accept_cookies(driver):
    """Click the 'Accept' button on the cookies consent banner if it exists."""
    try:
        # Wait for the 'Accept' button on the consent banner to be clickable, then click it
        WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable(
                (By.XPATH, '//button[@data-a-target="consent-banner-accept"]')
            )
        ).click()
        print("Clicked 'Accept' on the cookies consent banner.")
    except Exception as e:
        print_error(f"No 'Accept' button for cookies consent found or error occurred")

from selenium.webdriver import ActionChains

def click_captions_button(driver):
    """Hover over the video player and click the 'Captions (CC)' button if it exists."""
    try:
        # First, hover over the video player to reveal the controls (including the captions button)
        video_player = driver.find_element(By.XPATH, '//div[contains(@class, "video-player")]')
        actions = ActionChains(driver)
        actions.move_to_element(video_player).perform()
        print("Hovered over video player.")

        # Now wait for the Captions button to become clickable and click it
        WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable(
                (By.XPATH, '//button[@aria-label="Captions (c)"]')
            )
        ).click()
        print("Clicked 'Captions (CC)' button.")
    except Exception as e:
        print_error(f"No 'Captions (CC)' button found or error occurred:")



def take_screenshots_and_describe(driver, interval_range, run_duration, output_folder, description_folder, api_key, game_name, comment_folder, broadcaster_id, sender_id, client_id, access_token, stream_language, username_arg):
    """Take screenshots and describe them immediately, skipping the first screenshot."""
    start_time = time.time()
    screenshot_count = 0
    output_folder = os.path.join(username_arg, output_folder)
    description_folder = os.path.join(username_arg, description_folder)
    comment_folder = os.path.join(username_arg, comment_folder)

    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    if not os.path.exists(description_folder):
        os.makedirs(description_folder)

    if not os.path.exists(comment_folder):
        os.makedirs(comment_folder)

    while (time.time() - start_time) < run_duration:
        # Wait for the content to be visible
        wait_for_content(driver)
        
        # Skip the first screenshot
        if screenshot_count == 0:
            # Take screenshot and ignore it
            screenshot_filename = os.path.join(output_folder, f'screenshot_{screenshot_count}.png')
            driver.save_screenshot(screenshot_filename)
            print(f"Screenshot {screenshot_count} saved as {screenshot_filename} (ignored)")
        else:
            # Take screenshot
            screenshot_filename = os.path.join(output_folder, f'screenshot_{screenshot_count}.png')
            driver.save_screenshot(screenshot_filename)
            print(f"Screenshot {screenshot_count} saved as {screenshot_filename}")

            # Describe the screenshot immediately
            description = describe_image(screenshot_filename, api_key, game_name)
            if description:
                description_filename = os.path.join(description_folder, f'screenshot_{screenshot_count}.txt')
                with open(description_filename, 'w') as desc_file:
                    desc_file.write(description)
                print(f"Description saved as {description_filename}")
            else:
                print(f"{RED_TEXT}No description returned for screenshot {screenshot_count}{RESET_TEXT}")

            # Fetch the last 5 chat messages
            chat_messages = get_last_5_chat_messages(driver)
            
            # Generate comments based on the description and real chat messages
            comments = generate_comments(api_key, game_name, description, chat_messages, stream_language)
            if comments:
                # Post the first generated comment to Twitch before saving
                comment_list = comments.split('\n')
                # Select a random comment from the list
                random_comment = random.choice(comment_list)
                post_twitch_message(broadcaster_id, sender_id, random_comment, client_id, access_token)  
                print(f"{GREEN_TEXT}Posted comment: {random_comment}{RESET_TEXT}")

                # Save all the generated comments to a file
                comment_filename = os.path.join(comment_folder, f'screenshot_{screenshot_count}.txt')
                with open(comment_filename, 'w') as comment_file:
                    comment_file.write(comments)
                print(f"Comments saved as {comment_filename}")
            else:
                print(f"{RED_TEXT}No comments generated for screenshot {screenshot_count}{RESET_TEXT}")

        screenshot_count += 1
        min_interval, max_interval = map(int, interval_range.split(','))
        interval = random.randint(min_interval, max_interval)
        countdown_timer(interval, "Waiting for {} seconds before the next analysis...")

def wait_for_content(driver, timeout=20):
    """Wait for specific content to be visible on the page."""
    try:
        WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'video'))  # Adjust CSS selector based on the content
        )
        print("Content is visible")
    except Exception as e:
        print_error(f"Error while waiting for content")


def encode_image(image_path):
    """Encode the image to base64."""
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

def describe_image(image_path, api_key, game_name):
    """Describe the image using OpenAI API."""
    try:
        base64_image = encode_image(image_path)

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }

        payload = {
            "model": "gpt-4o-mini",  # Change the model if needed
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
                                "Describe What streamer or presenter talking in details by reading CC on video"
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{base64_image}"  # Using PNG format
                            }
                        }
                    ]
                }
            ],
            "max_tokens": 500
        }

        response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)

        if response.status_code == 200:
            description = response.json()['choices'][0]['message']['content']
            return description
        else:
            print_error(f"API error for {image_path}. Status code: {response.status_code}. Response: {response.text}")
            return None

    except Exception as e:
        print_error(f"Error while describing {image_path}: {e}")
        return None

def toggle_side_nav(driver):
    try:
        # Wait for the toggle button to be clickable and click it
        toggle_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, 'button[data-a-target="side-nav-arrow"]'))
        )
        toggle_button.click()
        print("Toggled the side navigation.")
    except Exception as e:
        print_error(f"Error while toggling side navigation")

def generate_comments(api_key, game_name, description, chat_messages_text, stream_language):
    """Generate Twitch-style comments without usernames for the current game context."""
    comment_styles = [
    "Casual banter: 'I have no idea how to use this character!'",
    "Humorous observations: 'Oh no, they are maxing their resources again!'",
    "Engaging responses: 'Is this a tournament or just a regular match?'",
    "Light-hearted jests: 'Hindsight is always 20/20!'",
    "Excited reactions: 'What a crazy play!'",
    "Casual questions: 'How does this mechanic work?'"
    "Strategic Analysis: “That unit combo could really turn the tide!”"
    "Empathetic Support: “We’ve all been there; keep trying!”"
	"Meme References: “This play is giving me serious ‘bruh’ vibes.”"
	"Cheeky Remarks: “That was a bold move; let’s see if it pays off!”"
	"Hypothetical Scenarios: “Imagine if they had gone for a different strategy!”"
	"Nostalgic References: “This reminds me of the good old days of gaming!”"
	"Encouraging Comments: “You got this! Just keep pushing!”"
	"Playful Jabs: “Looks like someone’s been practicing in secret!"
	"Observational Humor: “That reaction was priceless; we all felt that!”"
	"Confused Reactions: “Wait, what just happened there?”"
    ]

    selected_style = random.choice(comment_styles)

    prompt = f"""
    Generate a ONE SHORT ({random.randint(2, 30)} words) casual comment for a Twitch stream in '{stream_language}'. The comments should reflect the lively and chaotic nature of Twitch chat while maintaining a casual tone.

    Incorporate gamer slang and emotes where appropriate, but AVOID excessive use of smiley faces or other emoticons. Each comment should be concise, engaging, and playful, adding to the fun atmosphere of the stream.

    The comment style is: {selected_style}

    The following is a description of the game's scene: {description}
    The following are recent chat messages from the stream: {chat_messages_text}.
    - Do not include any quotes, numbers, bullet points, or hyphens before any of the comments. The comments should appear as plain text without any formatting symbols.
    """

    try:
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }

        payload = {
            "model": "gpt-4o-mini",  # Adjust model if necessary
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "max_tokens": 300
        }

        response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)

        if response.status_code == 200:
            comments = response.json()['choices'][0]['message']['content']
            
            # Clean up the comments by removing unwanted symbols
            # Remove any leading numbers, bullet points, hyphens, and quotes
            plain_comments = comments.replace('•', '').replace('-', '').replace('\"', '').strip()
            
            # Split the comments by newlines and clean up any excess spaces or unwanted formatting
            plain_comments_list = plain_comments.split("\n")
            filtered_comments = []

            for comment in plain_comments_list:
                # Remove leading/trailing whitespace from each comment and ensure it's not empty
                clean_comment = comment.strip()
                if clean_comment and not clean_comment.startswith(('- ', '•', '"', "'", '*')):
                    filtered_comments.append(clean_comment)

            # Join the cleaned comments with a single newline to ensure no extra spaces
            final_comments = "\n".join(filtered_comments)

            return final_comments
        else:
            print_error(f"Error generating comments. Status code: {response.status_code}. Response: {response.text}")
            return None

    except Exception as e:
        print_error(f"Error while generating comments: {e}")
        return None

