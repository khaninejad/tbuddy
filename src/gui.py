import logging
import os
import tkinter as tk
from tkinter import messagebox, Toplevel, Frame, ttk
import json
from tkinter import filedialog
import webbrowser
import sv_ttk
from bot_operations import BotOperations
from load_assistant_type import assistants, load_assistant_types
from __version__ import __version__
from config import CONFIG_FILE
from license_manager import LicenseManager
from update_checker import UpdateChecker
from utils import clean_folder, print_info


LICENSED = False
USAGE_TIME_LIMIT = 30 * 1
USAGE_TIME_LEFT = USAGE_TIME_LIMIT
print_info(f"Application Version: {__version__}")

logging.basicConfig(
    filename="bot_errors.log",
    filemode="a",
    level=logging.ERROR,
    format="%(asctime)s - %(levelname)s - %(message)s",
)


class BotGUI:
    def __init__(self, master):
        self.master = master
        master.title("Twitch Bot - User Management")
        
        clean_folder('users')

        update_checker = UpdateChecker(__version__)
        update_available, last_release = update_checker.check_for_updates()

        if update_available:
            self.prompt_for_update(last_release, update_checker)

        self.license_manager = LicenseManager()
        
        self.bot_operations = BotOperations(self.license_manager, self.master)

        self.license_manager.check_license_on_startup()

        if self.license_manager.LICENSED:
            if self.license_manager.PLAN_TYPE == "PREMIUM":
                self.setup_premium_ui()
            else:
                self.setup_free_ui()
                self.start_usage_timer()
        else:
            self.setup_registration_ui()

        self.processes = {}
        self.threads = {}
        self.start_times = {}
        self.languages = [
            "English",
            "Spanish",
            "French",
            "German",
            "Italian",
            "Russian",
            "Chinese",
            "Japanese",
            "Korean",
            "Portuguese",
        ]
        
        feedback_button = tk.Button(
            master, text="Report a Bug or Feedback", command=self.report_feedback
        )
        feedback_button.pack(pady=5)

    def setup_registration_ui(self):
        """UI when no valid license exists, prompting the user to register."""
        register_button = tk.Button(
            self.master, text="Register License", command=self.license_manager.register_new_license
        )
        register_button.pack(pady=20)

    def setup_free_ui(self):
        """UI for Free users, with an upgrade button."""
        upgrade_button = tk.Button(
            self.master, text="Upgrade to Premium", command=self.license_manager.upgrade_to_premium
        )
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

        self.add_user_button = tk.Button(
            self.master, text="Add User", command=self.add_user
        )
        self.add_user_button.pack(pady=5)

        self.assistants_button = tk.Button(
            self.master, text="Assistants", command=lambda: assistants(self.master)
        )
        self.assistants_button.pack(pady=5)

        self.load_users()

    def prompt_for_update(self, last_release, update_checker):
        update_window = Toplevel(self.master)
        update_window.title("Update Available")

        tk.Label(
            update_window, text=f"Update available: v{last_release['version']}"
        ).pack(pady=20)

        def update_now():
            update_filename = update_checker.download_update(last_release)
            update_checker.extract_update(last_release, update_filename)
            update_checker.install_update(last_release)
            update_window.destroy()
            messagebox.showinfo(
                "Update Installed", "The update has been successfully installed."
            )

        def remind_me_later():
            update_window.destroy()

        update_button = tk.Button(update_window, text="Update Now", command=update_now)
        update_button.pack(pady=10)

        remind_me_later_button = tk.Button(
            update_window, text="Remind Me Later", command=remind_me_later
        )
        remind_me_later_button.pack(pady=10)

            
    def report_feedback(self):
        """Collects user feedback, with an option to attach logs."""
        feedback_window = Toplevel(self.master)
        feedback_window.title("Report Feedback")
        if self.prompt_for_logs():
            webbrowser.open("https://tbuddy.chat/contact-us/", new=1)
            feedback_window.destroy()

        
    def prompt_for_logs(self):
        """Prompt user to attach logs, and open save dialog if they agree."""
        attach_logs = messagebox.askyesno(
            "Attach Logs", "Would you like to attach logs with your feedback?"
        )
        if attach_logs:
            file_path = filedialog.asksaveasfilename(
                defaultextension=".log",
                filetypes=[("Log files", "*.log"), ("All files", "*.*")],
                title="Save bot_errors.log",
            )
            if file_path:
                try:
                    with open("bot_errors.log", "r") as log_file:
                        with open(file_path, "w") as save_file:
                            save_file.write(log_file.read())
                    messagebox.showinfo("Logs Saved", "Logs have been saved successfully.")
                except Exception as e:
                    logging.error(f"Failed to save log file: {e}")
                    messagebox.showerror("Error", "Failed to save log file.")
        return True


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

        user_label = tk.Text(
            frame,
            width=40,
            height=1,
            borderwidth=0,
            highlightthickness=0,
            bg=frame.cget("bg"),
            fg="black",
        )
        user_label.insert(tk.END, f'{user["username"]} (')
        user_label.insert(tk.END, user["stream_username"], ("link",))
        user_label.insert(tk.END, ")")
        user_label.tag_config("link", foreground="blue", underline=True)
        user_label.tag_bind(
            "link",
            "<Button-1>",
            lambda e, u=user["stream_username"]: open_stream_url(u),
        )
        user_label.config(state=tk.DISABLED)
        user_label.pack(side="left")

        assistant_label = tk.Label(
            frame, text=f"Assistant: {user.get('assistant_type', 'Not Set')}"
        )
        assistant_label.pack(side="left", padx=5)

        time_label = tk.Label(frame, text="00:00", width=5, anchor="w")
        time_label.pack(side="left")

        button_frame = Frame(frame)
        button_frame.pack(side="right")

        toggle_button = tk.Button(button_frame, text="Start")
        toggle_button.pack(side="left", padx=5)

        toggle_button.config(
            command=lambda u=user, t=time_label, b=toggle_button: self.toggle_bot(
                u, t, b
            )
        )

        edit_button = tk.Button(
            button_frame,
            text="Edit",
            command=lambda u=user, f=frame: self.edit_user(u, f),
        )
        edit_button.pack(side="left", padx=5)

        delete_button = tk.Button(
            button_frame,
            text="Delete",
            command=lambda u=user, f=frame: self.delete_user(u, f),
        )
        delete_button.pack(side="left", padx=5)

        console_button = tk.Button(
            button_frame,
            text="Open Console",
            command=lambda u=user: self.bot_operations.open_console(u),
        )
        console_button.pack(side="left", padx=5)

    def add_user(self):
        """Add a new user with a popup dialog."""

        plan_type = self.license_manager.PLAN_TYPE
        print_info(f"Current plan type: {plan_type}")

        print_info(f"Number of existing users: {len(self.users)}")

        if plan_type == "FREE" and len(self.users) >= 1:
            messagebox.showerror(
                "Upgrade to Premium",
                "You are currently on the Free plan, which allows only one user. Please upgrade to Premium to add more users.",
            )
            print_info("User limit reached. Prompting to upgrade to Premium.")
            return

        print_info("User limit not reached. Showing the user form.")

        self.show_user_form()

    def edit_user(self, user, frame):
        """Edit an existing user."""
        self.show_user_form(user=user, frame=frame)

    def delete_user(self, user, frame):
        """Delete the selected user."""
        username = user["username"]

        if username in self.processes:
            self.bot_operations.stop_bot(user)

        self.users.remove(user)
        self.save_users()

        frame.destroy()
        messagebox.showinfo(
            "User Deleted", f"User {username} has been successfully deleted."
        )

    def save_users(self):
        """Save current user data to the configuration file."""
        config = {"users": self.users}
        with open(CONFIG_FILE, "w") as config_file:
            json.dump(config, config_file)

    def toggle_bot(self, user, time_label, button):
        """Toggle the bot's start and stop functions for the selected user."""
        username = user["username"]
        if username in self.processes:

            self.bot_operations.stop_bot(user)
            button.config(text="Start")
        else:

            self.bot_operations.start_bot(user, time_label)
            button.config(text="Stop")


    def start_usage_timer(self):
        """Start a timer for free usage limit of 30 minutes."""
        self.update_usage_time()
        self.master.after(1000, self.check_usage_time)

    def update_usage_time(self):
        """Reduce the usage time left by 1 second every second."""
        global USAGE_TIME_LEFT
        if USAGE_TIME_LEFT > 0:
            USAGE_TIME_LEFT -= 1

    def check_usage_time(self):
        """Check if the usage time limit is reached."""
        if USAGE_TIME_LEFT <= 0:
            messagebox.showwarning(
                "Usage Time Expired",
                "Your usage time has expired. Please register for a valid license.",
            )
            self.disable_features()
        else:
            self.master.after(1000, self.check_usage_time)

    def disable_features(self):
        """Disable certain features if the time limit has expired."""

        self.add_user_button.config(state=tk.DISABLED)


    def show_user_form(self, user=None, frame=None):
        """Show form to add or edit a user."""
        user_window = Toplevel(self.master)
        user_window.title("Edit User" if user else "Add New User")
        user_window.geometry("600x500")

        tk.Label(user_window, text="Username:").grid(row=0, column=0, sticky="e")
        username_entry = tk.Entry(user_window)
        username_entry.grid(row=0, column=1)

        tk.Label(user_window, text="Password:").grid(row=1, column=0, sticky="e")
        password_entry = tk.Entry(user_window, show="*")
        password_entry.grid(row=1, column=1)
        
        tk.Label(user_window, text="Min Response Frequency (seconds):").grid(row=7, column=0, sticky="e")
        min_response_entry = tk.Entry(user_window)
        min_response_entry.grid(row=7, column=1)

        # Add Max Response Frequency Field
        tk.Label(user_window, text="Max Response Frequency (seconds):").grid(row=8, column=0, sticky="e")
        max_response_entry = tk.Entry(user_window)
        max_response_entry.grid(row=8, column=1)
        
        tooltip_text = (
            "Warning: Setting a response frequency below 30 seconds may result in increased OpenAI usage and costs."
        )
        
        def show_tooltip(event, text):
            """Display tooltip near the widget."""
            tooltip = tk.Toplevel(user_window)
            tooltip.wm_overrideredirect(True)
            tooltip.geometry(f"+{event.x_root + 20}+{event.y_root}")
            label = tk.Label(tooltip, text=text, background="yellow", relief="solid", borderwidth=1)
            label.pack()
            tooltip.after(3000, tooltip.destroy)

        def check_min_response_tooltip(event=None):
            """Show tooltip if Min Response Frequency is less than 30 seconds."""
            try:
                min_value = int(min_response_entry.get())
                if min_value < 30:
                    show_tooltip(event, tooltip_text)
            except ValueError:
                pass
        
        min_response_entry.bind("<FocusOut>", check_min_response_tooltip)
        min_response_entry.bind("<KeyRelease>", check_min_response_tooltip)
        

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
        self.language_combobox = ttk.Combobox(
            user_window, values=self.languages, state="readonly"
        )
        self.language_combobox.grid(row=5, column=1, sticky="ew")

        tk.Label(user_window, text="Assistant Type:").grid(row=6, column=0, sticky="e")
        self.assistant_types = load_assistant_types()
        self.assistant_combobox = ttk.Combobox(
            user_window, values=self.assistant_types, state="readonly"
        )
        self.assistant_combobox.grid(row=6, column=1, sticky="ew")

        if user:
            username_entry.insert(0, user["username"])
            password_entry.insert(0, user["password"])
            min_response_entry.insert(0, user.get("min_response_frequency", "30"))
            max_response_entry.insert(0, user.get("max_response_frequency", "150"))

            stream_username_entry.insert(0, user["stream_username"])
            game_name_entry.insert(0, user["game_name"])
            openai_key_entry.insert(0, user.get("openai_api_key", ""))
            self.language_combobox.set(user.get("stream_language", self.languages[0]))
            self.assistant_combobox.set(
                user.get("assistant_type", self.assistant_types[0])
            )

        def save_user():
            username = username_entry.get()
            password = password_entry.get()
            min_response_frequency = int(min_response_entry.get())
            max_response_frequency = int(max_response_entry.get())
            stream_username = stream_username_entry.get()
            game_name = game_name_entry.get()
            openai_api_key = openai_key_entry.get()
            selected_language = self.language_combobox.get()
            selected_assistant = self.assistant_combobox.get()
            
            if not username or not password:
                messagebox.showerror("Input Error", "All fields are required.")
                return

            if min_response_frequency < 1 or max_response_frequency < min_response_frequency:
                messagebox.showerror("Input Error", "Please enter a valid frequency range.")
                return

            if (
                not username
                or not password
                or not stream_username
                or not game_name
                or not openai_api_key
            ):
                messagebox.showerror("Input Error", "All fields are required.")
                return

            if user:
                user["username"] = username
                user["password"] = password
                user["min_response_frequency"] = min_response_frequency
                user["max_response_frequency"] = max_response_frequency
                user["stream_username"] = stream_username
                user["game_name"] = game_name
                user["openai_api_key"] = openai_api_key
                user["stream_language"] = selected_language
                user["assistant_type"] = selected_assistant
            else:
                new_user = {
                    "username": username,
                    "password": password,
                    "min_response_frequency": min_response_frequency,
                    "max_response_frequency": max_response_frequency,
                    "stream_username": stream_username,
                    "game_name": game_name,
                    "openai_api_key": openai_api_key,
                    "stream_language": selected_language,
                    "assistant_type": selected_assistant,
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
        save_button.grid(row=9, column=1, pady=5)


def start_gui():
    root = tk.Tk()
    root.minsize(400, 300)
    sv_ttk.set_theme("light")
    BotGUI(root)
    root.mainloop()


if __name__ == "__main__":
    start_gui()
