import os
import tkinter as tk
from tkinter import messagebox, simpledialog
from utils import print_error

class AssistantManager:
    def __init__(self, master):
        self.master = master
        self.master.title("Assistant Manager")

        self.assistant_listbox = tk.Listbox(master)
        self.assistant_listbox.pack(pady=10)

        self.load_button = tk.Button(master, text="Load Assistants", command=self.load_assistants)
        self.load_button.pack(pady=5)

        self.edit_button = tk.Button(master, text="Edit Selected Assistant", command=self.edit_assistant)
        self.edit_button.pack(pady=5)

        self.save_button = tk.Button(master, text="Save Changes", command=self.save_assistant)
        self.save_button.pack(pady=5)

        self.assistants_dir = os.path.join(os.path.dirname(__file__), "assistants")
        self.assistants_data = {}

    def load_assistants(self):
        """Load assistant types from the assistants directory and display in the listbox."""
        self.assistant_listbox.delete(0, tk.END)  # Clear existing list
        self.assistants_data.clear()  # Clear previous data

        try:
            for file in os.listdir(self.assistants_dir):
                if file.endswith(".txt"):
                    assistant_name = file[:-4]  # Remove the '.txt' extension
                    self.assistant_listbox.insert(tk.END, assistant_name)
                    self.assistants_data[assistant_name] = self.load_assistant_type(assistant_name)
        except FileNotFoundError:
            print_error("Assistants directory not found.")

    def load_assistant_type(self, assistant_name):
        """Load assistant type from a text file."""
        assistant_file = os.path.join(self.assistants_dir, f"{assistant_name}.txt")
        try:
            with open(assistant_file, "r") as file:
                assistant_type = file.read().strip()
                return assistant_type
        except FileNotFoundError:
            print_error(f"Assistant type '{assistant_name}' not found.")
            return None

    def edit_assistant(self):
        """Edit the selected assistant's type."""
        selected_index = self.assistant_listbox.curselection()
        if not selected_index:
            messagebox.showwarning("Select Assistant", "Please select an assistant to edit.")
            return

        selected_assistant = self.assistant_listbox.get(selected_index)
        current_type = self.assistants_data[selected_assistant]

        new_type = simpledialog.askstring("Edit Assistant", f"Current Type: {current_type}\nEnter new type:", initialvalue=current_type)
        if new_type is not None:
            self.assistants_data[selected_assistant] = new_type

    def save_assistant(self):
        """Save the edited assistant type back to the text file."""
        selected_index = self.assistant_listbox.curselection()
        if not selected_index:
            messagebox.showwarning("Select Assistant", "Please select an assistant to save.")
            return

        selected_assistant = self.assistant_listbox.get(selected_index)
        new_type = self.assistants_data[selected_assistant]

        assistant_file = os.path.join(self.assistants_dir, f"{selected_assistant}.txt")
        with open(assistant_file, "w") as file:
            file.write(new_type)

        messagebox.showinfo("Save Successful", f"{selected_assistant} saved successfully.")
