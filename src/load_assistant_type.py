import os
from tkinter import Toplevel, messagebox
import tkinter as tk
from utils import print_error  # Make sure utils.py has a print_error function


def load_assistant_type(assistant_name):
    """Load assistant type from a text file."""
    assistants_dir = os.path.join(os.path.dirname(__file__), "assistants")
    assistant_file = os.path.join(assistants_dir, f"{assistant_name}.txt")

    try:
        with open(assistant_file, "r") as file:
            assistant_type = file.read().strip()
            return assistant_type
    except FileNotFoundError as e:
        print_error(f"Assistant type '{assistant_name}' not found.", e)
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


def assistants(master):
    """Entry point to open the assistant management window."""
    open_assistants_window(master)


def open_assistants_window(master):
    """Open a window to manage assistants."""
    assistants_window = Toplevel(master)
    assistants_window.title("Manage Assistants")

    assistant_types = load_assistant_types()

    assistant_listbox = tk.Listbox(assistants_window)
    assistant_listbox.pack(fill="both", expand=True, padx=10, pady=10)

    for assistant in assistant_types:
        assistant_name = assistant if isinstance(assistant, str) else assistant["name"]
        assistant_listbox.insert(tk.END, assistant_name)

    tk.Button(
        assistants_window, text="Edit",
        command=lambda: edit_assistant(master, assistant_listbox, assistant_types)
    ).pack(pady=5)

    tk.Button(
        assistants_window, text="Delete",
        command=lambda: delete_assistant(assistant_listbox)
    ).pack(pady=5)


def edit_assistant(master, assistant_listbox, assistant_types):
    """Edit the selected assistant."""
    selected_index = assistant_listbox.curselection()
    if not selected_index:
        messagebox.showwarning("Selection Error", "No assistant selected.")
        return

    # Retrieve selected assistant name
    selected_assistant_name = assistant_listbox.get(selected_index)
    
    # Check if the selected assistant name exists in assistant_types
    if selected_assistant_name not in assistant_types:
        messagebox.showerror("Error", "Assistant data not found.")
        return

    # Load the assistant type data (if additional data needed from file)
    assistant_type = load_assistant_type(selected_assistant_name)
    
    # Show form with the assistant data
    show_assistant_form(master, {"name": selected_assistant_name}, assistant_type)



def delete_assistant(assistant_listbox):
    """Delete the selected assistant."""
    selected_index = assistant_listbox.curselection()
    if not selected_index:
        messagebox.showwarning("Selection Error", "No assistant selected.")
        return

    selected_assistant = assistant_listbox.get(selected_index)
    assistants_dir = os.path.join(os.path.dirname(__file__), "assistants")
    assistant_file = os.path.join(assistants_dir, f"{selected_assistant}.txt")

    try:
        os.remove(assistant_file)
        assistant_listbox.delete(selected_index)
        messagebox.showinfo("Success", f"{selected_assistant} deleted successfully.")
    except Exception as e:
        messagebox.showerror("Error", f"Could not delete {selected_assistant}: {e}")


def save_assistant(user, assistant_type, form_window):
    """Save the assistant type to a text file and close the form."""
    # Update the assistant type in the user dictionary
    user["assistant_type"] = assistant_type

    # Path to the assistant file
    assistants_dir = os.path.join(os.path.dirname(__file__), "assistants")
    assistant_file = os.path.join(assistants_dir, f"{user['name']}.txt")

    # Write the new assistant type to the file
    try:
        with open(assistant_file, "w") as file:
            file.write(assistant_type)
        messagebox.showinfo("Success", f"{user['name']} saved successfully.")
    except Exception as e:
        messagebox.showerror("Error", f"Could not save {user['name']}: {e}")
    finally:
        form_window.destroy()



def show_assistant_form(master, user, assistant_type=None):
    """Show a form for editing the assistant type."""
    form_window = Toplevel(master)
    form_window.title("Edit Assistant Type")
    
    # Set a larger window size
    form_window.geometry("600x400")

    tk.Label(form_window, text="Enter Assistant Type:").pack(padx=10, pady=10)

    # Frame for text area and scrollbar
    text_frame = tk.Frame(form_window)
    text_frame.pack(fill="both", expand=True, padx=10, pady=10)

    # Text widget with increased width and height
    assistant_text = tk.Text(text_frame, width=70, height=15, wrap=tk.WORD)
    assistant_text.pack(side="left", fill="both", expand=True)

    # Add vertical scrollbar
    scrollbar = tk.Scrollbar(text_frame, command=assistant_text.yview)
    scrollbar.pack(side="right", fill="y")
    assistant_text.config(yscrollcommand=scrollbar.set)

    # Insert assistant type if provided
    if assistant_type:
        assistant_text.insert(tk.END, assistant_type)

    # Save button
    tk.Button(
        form_window,
        text="Save",
        command=lambda: save_assistant(user, assistant_text.get("1.0", tk.END).strip(), form_window)
    ).pack(pady=5)

    # Cancel button
    tk.Button(
        form_window, text="Cancel", command=form_window.destroy
    ).pack(pady=5)
