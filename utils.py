import os
import sys
import time


RED_TEXT = "\033[91m"
RESET_TEXT = "\033[0m"
GREEN_TEXT = "\033[92m"

def print_error(message):
    """Print an error message in red."""
    print(f"{RED_TEXT}Error: {message}{RESET_TEXT}")

def countdown_timer(seconds, message_template="Waiting for {} seconds before login..."):
    """Print a countdown timer that updates every second."""
    max_length = len(message_template.format(seconds))

    for remaining in range(seconds, 0, -1):
        # Construct the message
        message = message_template.format(remaining)
        # Print the message
        sys.stdout.write("\r" + message)
        sys.stdout.flush()
        time.sleep(1)

    final_message = message_template.format(0) + " Done!"
    sys.stdout.write("\r" + final_message + "    \n")  # Final message