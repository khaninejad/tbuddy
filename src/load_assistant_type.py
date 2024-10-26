import os

from utils import print_error


def load_assistant_type(assistant_name):
    """Load assistant type from a text file."""
    assistants_dir = os.path.join(os.path.dirname(__file__), "assistants")
    assistant_file = os.path.join(assistants_dir, f"{assistant_name}.txt")

    try:
        with open(assistant_file, "r") as file:
            assistant_type = file.read().strip()
            return assistant_type
    except FileNotFoundError:
        print_error(f"Assistant type '{assistant_name}' not found.")
        return None


def load_assistant_types():
    """Load assistant types from the assistants directory."""
    assistants_dir = os.path.join(os.path.dirname(__file__), "assistants")
    assistant_types = [
        file.split(".")[0]
        for file in os.listdir(assistants_dir)
        if file.endswith(".txt")
    ]
    return assistant_types
