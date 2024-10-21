import logging
from logging.handlers import RotatingFileHandler
import sys
import time

# Define constants for colors
WHITE_TEXT = "\033[97m"
RED_TEXT = "\033[91m"
RESET_TEXT = "\033[0m"
GREEN_TEXT = "\033[92m"

# Log file configuration
log_filename = f"bot_errors.log"
max_log_size = 5 * 1024 * 1024  # Max log file size: 5 MB
backup_count = 5  # Keep up to 5 backup log files

# Configure rotating log handler
log_handler = RotatingFileHandler(
    log_filename, 
    mode='a',  # Append mode
    maxBytes=max_log_size,  # Max size per log file in bytes
    backupCount=backup_count,  # Number of backup files to retain
    encoding='utf-8',
    delay=0
)

# Configure logging
logging.basicConfig(
    handlers=[log_handler], 
    level=logging.INFO, 
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def print_error(message):
    """Print an error message in red."""
    print(f"{RED_TEXT}Error: {message}{RESET_TEXT}")
    logging.error(message)

def print_info(message):
    """Print an info message in white."""
    print(f"{WHITE_TEXT}{message}{RESET_TEXT}")
    logging.info(message)

def countdown_timer(seconds, message_template="Waiting for {} seconds before login..."):
    """Print a countdown timer that updates every second."""
    max_length = len(message_template.format(seconds))

    for remaining in range(seconds, 0, -1):
        message = message_template.format(remaining)
        sys.stdout.write("\r" + message)
        logging.info(message)
        sys.stdout.flush()
        time.sleep(1)

    final_message = message_template.format(0) + " Done!"
    logging.info(final_message)
    sys.stdout.write("\r" + final_message + "    \n")
