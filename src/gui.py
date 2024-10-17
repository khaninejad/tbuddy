import os
import sys
import subprocess
import tkinter as tk
from tkinter import messagebox, Toplevel, Frame, scrolledtext, ttk
import threading
import json
import time
import webbrowser
from __version__ import __version__
from license import check_license_on_startup, verify_license_data


CONFIG_FILE = "config.json"
LICENSED = False
print(f"Application Version: {__version__}")

class BotGUI:
    def __init__(self, master):
        self.master = master
        master.title("Twitch Bot - User Management")

        self.user_frame = tk.LabelFrame(master, text="Users")
        self.user_frame.pack(padx=10, pady=10, fill="both")

        self.users_frame = Frame(self.user_frame)
        self.users_frame.pack(fill="both", expand=True)

        self.add_user_button = tk.Button(master, text="Add User", command=self.add_user)
        self.add_user_button.pack(pady=5)

        self.verify_license_button = tk.Button(master, text="Verify License", command=verify_license_data)
        self.verify_license_button.pack(pady=5)

        self.load_users()
        check_license_on_startup()  # Automatically check for license on startup

        self.processes = {}  
        self.threads = {}    
        self.console_windows = {}  
        self.start_times = {}  

        self.languages = ["English", "Spanish", "French", "German", "Italian", "Russian", "Chinese", "Japanese", "Korean", "Portuguese"]

    def load_users(self):
        """Load user data from the configuration file."""
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, "r") as config_file:
                config = json.load(config_file)
                self.users = config.get("users", [])
        else:
            self.users = []

        for widget in self.users_frame.winfo_children():
            widget.destroy()  

        for index, user in enumerate(self.users):
            self.create_user_controls(index, user)

    def create_user_controls(self, index, user):
        """Create controls for each user."""
        def open_stream_url(stream_username):
            url = f"https://www.twitch.tv/{stream_username}"
            webbrowser.open(url)

        frame = Frame(self.users_frame)
        frame.pack(fill="x", padx=5, pady=5)

        user_label = tk.Text(frame, width=40, height=1, borderwidth=0, highlightthickness=0, bg=frame.cget("bg"), fg="black")
        user_label.insert(tk.END, f'{user["username"]} (')
        user_label.insert(tk.END, user["stream_username"], ('link',))
        user_label.insert(tk.END, ')')
        user_label.tag_config('link', foreground='blue', underline=True)
        user_label.tag_bind('link', '<Button-1>', lambda e, u=user["stream_username"]: open_stream_url(u))
        user_label.config(state=tk.DISABLED)
        user_label.pack(side="left")

        time_label = tk.Label(frame, text="00:00", width=5, anchor="w")
        time_label.pack(side="left")

        start_button = tk.Button(frame, text="Start", command=lambda u=user, t=time_label: self.start_bot(u, t))
        start_button.pack(side="left", padx=5)

        stop_button = tk.Button(frame, text="Stop", command=lambda u=user: self.stop_bot(u))
        stop_button.pack(side="left", padx=5)

        edit_button = tk.Button(frame, text="Edit", command=lambda u=user, f=frame: self.edit_user(u, f))
        edit_button.pack(side="left", padx=5)

        delete_button = tk.Button(frame, text="Delete", command=lambda u=user, f=frame: self.delete_user(u, f))
        delete_button.pack(side="left", padx=5)

        console_button = tk.Button(frame, text="Open Console", command=lambda u=user: self.open_console(u))
        console_button.pack(side="left", padx=5)

    def save_users(self):
        """Save current user data to the configuration file."""
        config = {"users": self.users}
        with open(CONFIG_FILE, "w") as config_file:
            json.dump(config, config_file)

    def add_user(self):
        """Add a new user with a popup dialog."""
        global LICENSED, PLAN_TYPE
        if PLAN_TYPE == "Free" and len(self.users) >= 1:
            messagebox.showerror("License Error", "Only one user is allowed for free. Please purchase a license to add more users.")
            return

        self.show_user_form()

    def edit_user(self, user, frame):
        """Edit an existing user."""
        self.show_user_form(user=user, frame=frame)

    def show_user_form(self, user=None, frame=None):
        """Show form to add or edit a user."""
        user_window = Toplevel(self.master)
        user_window.title("Edit User" if user else "Add New User")

        tk.Label(user_window, text="Username:").grid(row=0, column=0, sticky="e")
        username_entry = tk.Entry(user_window)
        username_entry.grid(row=0, column=1)

        tk.Label(user_window, text="Password:").grid(row=1, column=0, sticky="e")
        password_entry = tk.Entry(user_window, show="*")
        password_entry.grid(row=1, column=1)

        tk.Label(user_window, text="Stream Username:").grid(row=2, column=0, sticky="e")
        stream_username_entry = tk.Entry(user_window)
        stream_username_entry.grid(row=2, column=1)

        tk.Label(user_window, text="Game Name:").grid(row=3, column=0, sticky="e")
        game_name_entry = tk.Entry(user_window)
        game_name_entry.grid(row=3, column=1)

        tk.Label(user_window, text="OpenAI API Key:").grid(row=4, column=0, sticky="e")
        openai_key_entry = tk.Entry(user_window, show="*")  
        openai_key_entry.grid(row=4, column=1)

        tk.Label(user_window, text="Stream Language:").grid(row=5, column=0, sticky="e")
        self.language_combobox = ttk.Combobox(user_window, values=self.languages, state="readonly")
        self.language_combobox.grid(row=5, column=1, sticky="ew")

        if user:
            username_entry.insert(0, user["username"])
            password_entry.insert(0, user["password"])
            stream_username_entry.insert(0, user["stream_username"])
            game_name_entry.insert(0, user["game_name"])
            openai_key_entry.insert(0, user.get("openai_api_key", ""))  
            self.language_combobox.set(user.get("stream_language", self.languages[0]))

        def save_user():
            username = username_entry.get()
            password = password_entry.get()
            stream_username = stream_username_entry.get()
            game_name = game_name_entry.get()
            openai_api_key = openai_key_entry.get()
            selected_language = self.language_combobox.get()

            if not username or not password or not stream_username or not game_name or not openai_api_key:
                messagebox.showerror("Input Error", "All fields are required.")
                return

            if user:
                user["username"] = username
                user["password"] = password
                user["stream_username"] = stream_username
                user["game_name"] = game_name
                user["openai_api_key"] = openai_api_key  
                user["stream_language"] = selected_language  
            else:
                new_user = {
                    "username": username,
                    "password": password,
                    "stream_username": stream_username,
                    "game_name": game_name,
                    "openai_api_key": openai_api_key,  
                    "stream_language": selected_language  
                }
                self.users.append(new_user)
                self.create_user_controls(len(self.users) - 1, new_user)

            self.save_users()
            user_window.destroy()

            if frame:
                for widget in frame.winfo_children():
                    widget.destroy()
                self.create_user_controls(self.users.index(user), user)

        save_button = tk.Button(user_window, text="Save", command=save_user)
        save_button.grid(row=6, column=1, pady=5)


    # Placeholder for methods: start_bot, stop_bot, delete_user, open_console



    def start_bot(self, user, time_label):
        """Start the bot for the selected user."""
        username = user["username"]
        if username in self.processes:
            messagebox.showwarning("Process Running", "A bot for this user is already running.")
            return

        # Command to start the bot process
        command = [sys.executable, "bot.py", user["username"], user["password"], user["stream_username"], user["game_name"], user["openai_api_key"], user["stream_language"]]
        
        # Add stdin=subprocess.PIPE to allow sending commands
        process = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

        self.processes[username] = process
        self.start_times[username] = time.time()

        # Open console for the user to ensure the console window is ready
        self.open_console(user)

        # Start the timer update thread
        thread = threading.Thread(target=self.update_timer, args=(username, time_label), daemon=True)
        thread.start()
        self.threads[username] = thread

        # Start the output reading thread
        output_thread = threading.Thread(target=self.read_output, args=(process, username), daemon=True)
        output_thread.start()

        

    def update_timer(self, username, time_label):
        """Update the elapsed time for the bot."""
        while username in self.processes:
            elapsed_time = time.time() - self.start_times[username]
            minutes, seconds = divmod(int(elapsed_time), 60)
            time_label.config(text=f"{minutes:02}:{seconds:02}")
            time.sleep(1)

    def read_output(self, process, username):
        """Read the output from the bot process and store it in memory."""
        if username not in self.console_windows:
            return

        # Keep reading the process output in a loop
        while True:
            output = process.stdout.readline()  # Read a line of output from the bot process
            if output == '' and process.poll() is not None:
                break
            if output:
                # Append the output to the user's output buffer
                self.console_windows[username]["output_buffer"].append(output)

                # Update the console window if it exists
                if self.console_windows[username]["window"] is not None and self.console_windows[username]["window"].winfo_exists():
                    console_output = self.console_windows[username]["output"]
                    console_output.config(state='normal')
                    console_output.insert(tk.END, output)
                    console_output.see(tk.END)
                    console_output.config(state='disabled')




    def open_console(self, user):
        """Open a console window for the selected user."""
        username = user["username"]

        # Check if the user already has a console window
        if username in self.console_windows:
            if self.console_windows[username]["window"] is None or not self.console_windows[username]["window"].winfo_exists():
                # Delete the entry if the window was destroyed
                del self.console_windows[username]

        if username not in self.console_windows:
            console_window = Toplevel(self.master)
            console_window.title(f"Console - {username}")

            console_output = scrolledtext.ScrolledText(console_window, width=80, height=20, state='disabled')
            console_output.pack()

            input_field = tk.Entry(console_window, width=80)
            input_field.pack(pady=5)

            def send_command():
                command = input_field.get()
                if command and username in self.processes:
                    process = self.processes[username]
                    process.stdin.write(command + "\n")
                    process.stdin.flush()
                    input_field.delete(0, tk.END)

            send_button = tk.Button(console_window, text="Send", command=send_command)
            send_button.pack(pady=5)

            # Initialize the output buffer in case it doesn't exist
            if username not in self.console_windows:
                self.console_windows[username] = {"window": console_window, "output": console_output, "output_buffer": []}
            else:
                self.console_windows[username]["window"] = console_window
                self.console_windows[username]["output"] = console_output

            # Handle window close event
            def on_close():
                self.console_windows[username]["window"] = None  # Mark the window as closed
                console_window.destroy()

            console_window.protocol("WM_DELETE_WINDOW", on_close)

        # Repopulate the console with previous output
        console_output = self.console_windows[username]["output"]
        console_output.config(state='normal')
        for line in self.console_windows[username]["output_buffer"]:
            console_output.insert(tk.END, line)
        console_output.see(tk.END)
        console_output.config(state='disabled')

        # Bring the window to the front
        self.console_windows[username]["window"].lift()




    def stop_bot(self, user):
        """Stop the bot for the selected user."""
        username = user["username"]

        if username in self.processes:
            process = self.processes[username]
            process.terminate()
            del self.processes[username]
            del self.threads[username]  
            del self.start_times[username]  
            messagebox.showinfo("Bot Stopped", f"Bot for user {username} has been stopped.")
        else:
            messagebox.showwarning("Process Not Found", "No running process found for this user.")

    def delete_user(self, user, frame):
        """Delete the selected user."""
        username = user["username"]

        if username in self.processes:
            self.stop_bot(user)

        self.users.remove(user)
        self.save_users()

        frame.destroy()
        messagebox.showinfo("User Deleted", f"User {username} has been successfully deleted.")

def start_gui():
    root = tk.Tk()
    root.minsize(400, 300)
    app = BotGUI(root)
    root.mainloop()

if __name__ == "__main__":
    start_gui()
