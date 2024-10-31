import logging
from logging.handlers import RotatingFileHandler
import os
import shutil
import sys
import time


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
    """Print an error message in red."""
    print(f"{RED_TEXT}Error: {message}{RESET_TEXT}")
    logging.error(message, e)


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
    """Remove all files in the specified folder."""
    if folder_path is None:
        print_error("Folder path is None.")
        return

    if os.path.exists(folder_path):
        for filename in os.listdir(folder_path):
            file_path = os.path.join(folder_path, filename)
            try:
                if os.path.isfile(file_path):
                    os.remove(file_path)
                    print(f"Deleted {file_path}")
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)
                    print(f"Deleted directory {file_path}")
            except Exception as e:
                print_error(f"Failed to delete {file_path}.", e)
    else:
        print_error(f"Folder {folder_path} does not exist.")