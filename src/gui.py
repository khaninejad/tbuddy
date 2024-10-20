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
from license import LicenseManager
from load_assistant_type import load_assistant_types
from update_checker import UpdateChecker


CONFIG_FILE = "config.json"
LICENSED = False
print(f"Application Version: {__version__}")

class BotGUI:
    def __init__(self, master):
        self.master = master
        master.title("Twitch Bot - User Management")
        
        update_checker = UpdateChecker(__version__)
        update_available, last_release = update_checker.check_for_updates()

        if update_available:
            self.prompt_for_update(last_release, update_checker)

        self.license_manager = LicenseManager()

        
        self.license_manager.check_license_on_startup()

        
        if self.license_manager.LICENSED:
            if self.license_manager.PLAN_TYPE == "PREMIUM":
                self.setup_premium_ui()
            else:
                self.setup_free_ui()
        else:
            self.setup_registration_ui()

        self.processes = {}  
        self.threads = {}    
        self.console_windows = {}  
        self.start_times = {}  
        self.languages = ["English", "Spanish", "French", "German", "Italian", "Russian", "Chinese", "Japanese", "Korean", "Portuguese"]

    def prompt_for_update(self, last_release, update_checker):
        update_window = Toplevel(self.master)
        update_window.title("Update Available")

        tk.Label(update_window, text=f"Update available: v{last_release['version']}").pack(pady=20)

        def update_now():
            update_filename = update_checker.download_update(last_release)
            update_checker.extract_update(last_release, update_filename)
            update_checker.install_update(last_release)
            update_window.destroy()
            messagebox.showinfo("Update Installed", "The update has been successfully installed.")

        def remind_me_later():
            update_window.destroy()

        update_button = tk.Button(update_window, text="Update Now", command=update_now)
        update_button.pack(pady=10)

        remind_me_later_button = tk.Button(update_window, text="Remind Me Later", command=remind_me_later)
        remind_me_later_button.pack(pady=10)
    
    
    
    def setup_registration_ui(self):
        """UI when no valid license exists, prompting the user to register."""
        register_button = tk.Button(self.master, text="Register License", command=self.register_new_license)
        register_button.pack(pady=20)

    def upgrade_to_premium(self):
        """Directs the user to a URL to upgrade to premium."""
        webbrowser.open("https://your-upgrade-link.com")

    def setup_free_ui(self):
        """UI for Free users, with an upgrade button."""
        upgrade_button = tk.Button(self.master, text="Upgrade to Premium", command=self.upgrade_to_premium)
        upgrade_button.pack(pady=20)

        
        self.create_user_management_ui()

    def setup_premium_ui(self):
        """UI for Premium users, showing they are licensed."""
        license_label = tk.Label(self.master, text="Licensed - Premium")
        license_label.pack(pady=20)

        
        self.create_user_management_ui()

    def create_user_management_ui(self):
        """Create the user management section in the UI."""
        self.user_frame = tk.LabelFrame(self.master, text="Users")
        self.user_frame.pack(padx=10, pady=10, fill="both")

        self.users_frame = Frame(self.user_frame)
        self.users_frame.pack(fill="both", expand=True)

        self.add_user_button = tk.Button(self.master, text="Add User", command=self.add_user)
        self.add_user_button.pack(pady=5)

        self.load_users()

    def register_new_license(self):
        """Register a new license by using the LicenseManager."""
        if self.license_manager.register_license():
            self.license_manager.prompt_for_serial_number()

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
        
        assistant_label = tk.Label(frame, text=f"Assistant: {user.get('assistant_type', 'Not Set')}")
        assistant_label.pack(side="left", padx=5)
        

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
        
        plan_type = self.license_manager.PLAN_TYPE
        print(f"Current plan type: {plan_type}")

        
        print(f"Number of existing users: {len(self.users)}")

        
        if plan_type == "FREE" and len(self.users) >= 1:
            messagebox.showerror(
                "Upgrade to Premium",
                "You are currently on the Free plan, which allows only one user. Please upgrade to Premium to add more users."
            )
            print("User limit reached. Prompting to upgrade to Premium.")
            return  

        print("User limit not reached. Showing the user form.")
        
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
        
        
        tk.Label(user_window, text="Assistant Type:").grid(row=6, column=0, sticky="e")
        self.assistant_types = load_assistant_types()
        self.assistant_combobox = ttk.Combobox(user_window, values=self.assistant_types, state="readonly")
        self.assistant_combobox.grid(row=6, column=1, sticky="ew")

        if user:
            username_entry.insert(0, user["username"])
            password_entry.insert(0, user["password"])
            stream_username_entry.insert(0, user["stream_username"])
            game_name_entry.insert(0, user["game_name"])
            openai_key_entry.insert(0, user.get("openai_api_key", ""))  
            self.language_combobox.set(user.get("stream_language", self.languages[0]))
            self.assistant_combobox.set(user.get("assistant_type", self.assistant_types[0]))

        def save_user():
            username = username_entry.get()
            password = password_entry.get()
            stream_username = stream_username_entry.get()
            game_name = game_name_entry.get()
            openai_api_key = openai_key_entry.get()
            selected_language = self.language_combobox.get()
            selected_assistant = self.assistant_combobox.get()

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
                user["assistant_type"] = selected_assistant
            else:
                new_user = {
                    "username": username,
                    "password": password,
                    "stream_username": stream_username,
                    "game_name": game_name,
                    "openai_api_key": openai_api_key,  
                    "stream_language": selected_language,
                    "assistant_type": selected_assistant  
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
        save_button.grid(row=7, column=1, pady=5)


    



    def start_bot(self, user, time_label):
        """Start the bot for the selected user."""
        username = user["username"]
        if username in self.processes:
            messagebox.showwarning("Process Running", "A bot for this user is already running.")
            return

        
        command = [sys.executable, "bot.py", user["username"], user["password"], user["stream_username"], user["game_name"], user["openai_api_key"], user["stream_language"]]
        
        
        process = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

        self.processes[username] = process
        self.start_times[username] = time.time()

        
        self.open_console(user)

        
        thread = threading.Thread(target=self.update_timer, args=(username, time_label), daemon=True)
        thread.start()
        self.threads[username] = thread

        
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

        
        while True:
            output = process.stdout.readline()  
            if output == '' and process.poll() is not None:
                break
            if output:
                
                self.console_windows[username]["output_buffer"].append(output)

                
                if self.console_windows[username]["window"] is not None and self.console_windows[username]["window"].winfo_exists():
                    console_output = self.console_windows[username]["output"]
                    console_output.config(state='normal')
                    console_output.insert(tk.END, output)
                    console_output.see(tk.END)
                    console_output.config(state='disabled')




    def open_console(self, user):
        """Open a console window for the selected user."""
        username = user["username"]

        
        if username in self.console_windows:
            if self.console_windows[username]["window"] is None or not self.console_windows[username]["window"].winfo_exists():
                
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

            
            if username not in self.console_windows:
                self.console_windows[username] = {"window": console_window, "output": console_output, "output_buffer": []}
            else:
                self.console_windows[username]["window"] = console_window
                self.console_windows[username]["output"] = console_output

            
            def on_close():
                self.console_windows[username]["window"] = None  
                console_window.destroy()

            console_window.protocol("WM_DELETE_WINDOW", on_close)

        
        console_output = self.console_windows[username]["output"]
        console_output.config(state='normal')
        for line in self.console_windows[username]["output_buffer"]:
            console_output.insert(tk.END, line)
        console_output.see(tk.END)
        console_output.config(state='disabled')

        
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
