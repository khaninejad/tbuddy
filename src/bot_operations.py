import subprocess
import sys
import time
import threading
import logging
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext

class BotOperations:
    def __init__(self, license_manager, parent_window):
        self.processes = {}
        self.threads = {}
        self.start_times = {}
        self.license_manager = license_manager
        self.console_windows = {}
        self.parent_window = parent_window  # Main tk.Tk window passed here

    def start_bot(self, user, time_label):
        """Start the bot for the selected user."""
        try:
            username = user["username"]
            if username in self.processes:
                messagebox.showwarning(
                    "Process Running", "A bot for this user is already running."
                )
                return

            command = [
                sys.executable,
                "bot.py",
                user["username"],
                user["password"],
                user["stream_username"],
                user["game_name"],
                user["openai_api_key"],
                user["stream_language"],
                str(user["min_response_frequency"]), 
                str(user["max_response_frequency"]),  
            ]
            process = subprocess.Popen(
                command,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            self.processes[username] = process
            self.start_times[username] = time.time()

            # Call method to open the console (this method must exist in the main file)
            self.open_console(user)

            thread = threading.Thread(
                target=self.update_timer, args=(username, time_label), daemon=True
            )
            thread.start()
            self.threads[username] = thread

            output_thread = threading.Thread(
                target=self.read_output, args=(process, username), daemon=True
            )
            output_thread.start()
        except Exception as e:
            logging.error(f"Failed to start bot for user {user['username']}: {e}")
            messagebox.showerror("Error", f"An error occurred: {e}")

    def update_timer(self, username, time_label):
        """Update the elapsed time for the bot."""
        while username in self.processes:
            elapsed_time = time.time() - self.start_times[username]
            minutes, seconds = divmod(int(elapsed_time), 60)
            time_label.config(text=f"{minutes:02}:{seconds:02}")

            # Check for free plan limit
            if self.license_manager.PLAN_TYPE == "FREE" and elapsed_time >= 30 * 1:
                self.stop_bot({"username": username})
                messagebox.showinfo(
                    "Limit Reached",
                    "You have reached the 30-minute limit for free users. Please upgrade to continue using the bot.",
                )
                break

            time.sleep(1)

    def stop_bot(self, user):
        """Stop the bot for the selected user."""
        username = user["username"]
        if username in self.processes:
            process = self.processes[username]
            process.terminate()
            del self.processes[username]
            del self.threads[username]
            del self.start_times[username]
            messagebox.showinfo(
                "Bot Stopped", f"Bot for user {username} has been stopped."
            )
        else:
            messagebox.showwarning(
                "Process Not Found", "No running process found for this user."
            )

    def read_output(self, process, username):
        """Read the output from the bot process and store it in memory."""
        if username not in self.console_windows:
            return

        while True:
            output = process.stdout.readline()
            if output == "" and process.poll() is not None:
                break
            if output:
                self.console_windows[username]["output_buffer"].append(output)

                if (
                    self.console_windows[username]["window"] is not None
                    and self.console_windows[username]["window"].winfo_exists()
                ):
                    console_output = self.console_windows[username]["output"]
                    console_output.config(state="normal")
                    console_output.insert(tk.END, output)
                    console_output.see(tk.END)
                    console_output.config(state="disabled")
    
    def toggle_bot(self, user, time_label, button):
        """Toggle the bot's start and stop functions for the selected user."""
        username = user["username"]
        if username in self.processes:

            self.stop_bot(user)
            button.config(text="Start")
        else:

            self.start_bot(user, time_label)
            button.config(text="Stop")
    
    def open_console(self, user):
        """Open a console window for the selected user."""
        username = user["username"]

        if username in self.console_windows:
            if (
                self.console_windows[username]["window"] is None
                or not self.console_windows[username]["window"].winfo_exists()
            ):
                del self.console_windows[username]

        if username not in self.console_windows:
            console_window = tk.Toplevel(self.parent_window)
            console_window.title(f"Console - {username}")

            console_output = scrolledtext.ScrolledText(
                console_window, width=80, height=20, state="disabled"
            )
            console_output.pack()

            # Create an Entry widget with padding and placeholder text
            input_field = tk.Entry(console_window, width=80)
            input_field.pack(pady=5)
            input_field.insert(0, "Enter command here...")  # Placeholder text
            input_field.bind("<FocusIn>", lambda event: input_field.delete(0, tk.END))  # Clear on focus

            def send_command():
                command = input_field.get()
                if command and username in self.processes:
                    process = self.processes[username]
                    process.stdin.write(command + "\n")
                    process.stdin.flush()
                    input_field.delete(0, tk.END)
                    input_field.insert(0, "Enter command here...")  # Reset placeholder after sending

            # Create a blue "primary" Send button
            send_button = tk.Button(
                console_window, 
                text="Send", 
                command=send_command,
            )
            send_button.pack(pady=5)

            if username not in self.console_windows:
                self.console_windows[username] = {
                    "window": console_window,
                    "output": console_output,
                    "output_buffer": [],
                }
            else:
                self.console_windows[username]["window"] = console_window
                self.console_windows[username]["output"] = console_output

            def on_close():
                self.console_windows[username]["window"] = None
                console_window.destroy()

            console_window.protocol("WM_DELETE_WINDOW", on_close)

        console_output = self.console_windows[username]["output"]
        console_output.config(state="normal")
        for line in self.console_windows[username]["output_buffer"]:
            console_output.insert(tk.END, line)
        console_output.see(tk.END)
        console_output.config(state="disabled")

        self.console_windows[username]["window"].lift()