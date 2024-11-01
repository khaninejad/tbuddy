import logging
from logging.handlers import RotatingFileHandler
import os
import shutil
import sys
import time
from datetime import datetime


WHITE_TEXT = "\033[97m"
RED_TEXT = "\033[91m"
RESET_TEXT = "\033[0m"
GREEN_TEXT = "\033[92m"


log_filename = "bot_errors.log"
max_log_size = 5 * 1024 * 1024
backup_count = 5

log_handler = RotatingFileHandler(
    log_filename,
    mode="a",
    maxBytes=max_log_size,
    backupCount=backup_count,
    encoding="utf-8",
    delay=0,
)


logging.basicConfig(
    handlers=[log_handler],
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)


def print_error(message, e=None):
    """Print an error message in red and log it."""
    print(f"{RED_TEXT}Error: {message}{RESET_TEXT}")
    if e:
        logging.error(f"{message} Exception: {str(e)}", exc_info=True)
    else:
        logging.error(message)


def print_info(message):
    """Print an info message in white."""
    print(f"{WHITE_TEXT}{message}{RESET_TEXT}")
    logging.info(message)


def countdown_timer(seconds, message_template="Waiting for {} seconds before login..."):
    """Print a countdown timer that updates every second."""

    for remaining in range(seconds, 0, -1):
        message = message_template.format(remaining)
        sys.stdout.write("\r" + message)
        logging.info(message)
        sys.stdout.flush()
        time.sleep(1)

    final_message = message_template.format(0) + " Done!"
    logging.info(final_message)
    sys.stdout.write("\r" + final_message + "    \n")


def clean_folder(folder_path):
    """Remove subdirectories in the specified folder if they are older than 24 hours."""
    if folder_path is None:
        print_error("Folder path is None.")
        return

    if os.path.exists(folder_path):
        current_time = time.time()
        for filename in os.listdir(folder_path):
            folder_item_path = os.path.join(folder_path, filename)
            try:
                if os.path.isdir(folder_item_path) and (current_time - os.path.getmtime(folder_item_path) > 86400):
                    shutil.rmtree(folder_item_path)
                    print(f"Deleted directory {folder_item_path}")
            except Exception as e:
                print_error(f"Failed to delete {folder_item_path}.", e)
    else:
        print_error(f"Folder {folder_path} does not exist.")

def load_file_with_creation_time(file_path):
    # Get file creation time (in seconds since epoch)
    creation_time = os.path.getctime(file_path)
    # Format creation time as "YYYY-MM-DD HH:MM:SS"
    formatted_creation_time = datetime.fromtimestamp(creation_time).strftime("%Y-%m-%d %H:%M:%S")
    
    # Read the content of the file
    with open(file_path, 'r') as file:
        content = file.read()
    
    return content, formatted_creation_time
