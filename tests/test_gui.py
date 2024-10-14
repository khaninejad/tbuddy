import threading
import unittest
from unittest.mock import patch, MagicMock, mock_open
import tkinter as tk
import subprocess
import time
import json
import sys
from unittest.mock import call

from src.gui import CONFIG_FILE, BotGUI


class TestBotGUI(unittest.TestCase):
    
    def setUp(self):
        """Create a BotGUI instance with a mock tkinter root."""
        self.root = tk.Tk()  # Mock the main window
        self.app = BotGUI(self.root)

    def tearDown(self):
        """Destroy the tkinter root window after each test."""
        self.root.destroy()

    @patch("builtins.open", new_callable=mock_open, read_data='{"users": [{"username": "testuser", "stream_username": "teststream"}]}')
    @patch("os.path.exists", return_value=True)
    def test_load_users(self, mock_exists, mock_open_file):
        """Test loading users from the configuration file."""
        self.app.load_users()
        self.assertEqual(len(self.app.users), 1)
        self.assertEqual(self.app.users[0]['username'], "testuser")
        self.assertEqual(self.app.users[0]['stream_username'], "teststream")

    @patch("builtins.open", new_callable=mock_open)
    def test_save_users(self, mock_open_file):
        """Test saving users to the configuration file."""
        self.app.users = [{"username": "newuser", "stream_username": "newstream"}]
        self.app.save_users()

        mock_open_file.assert_called_once_with(CONFIG_FILE, "w")
        
        expected_write_calls = [
            call('{'),
            call('"users"'),
            call(': '),
            call('['),
            call('{'),
            call('"username"'),
            call(': '),
            call('"newuser"'),
            call(', '),
            call('"stream_username"'),
            call(': '),
            call('"newstream"'),
            call('}'),
            call(']'),
            call('}')
        ]
        
        mock_open_file().write.assert_has_calls(expected_write_calls)

    @patch("tkinter.messagebox.showerror")
    def test_add_user_license_check(self, mock_showerror):
        """Test license restriction when adding a user."""
        global LICENSED
        LICENSED = False
        self.app.users = [{"username": "testuser"}]  # One user already exists

        self.app.add_user()
        
        mock_showerror.assert_called_once_with("License Error", "Only one user is allowed for free. Please purchase a license to add more users.")


    @patch("tkinter.simpledialog.askstring", side_effect=["test@example.com", "INVALID_KEY"])
    @patch.object(BotGUI, "fake_license_api_call", return_value={"valid": False})
    @patch("tkinter.messagebox.showerror")
    def test_verify_license_failure(self, mock_showerror, mock_fake_license_api, mock_askstring):
        """Test failed license verification."""
        self.app.verify_license()

        mock_askstring.assert_any_call("License Verification", "Enter your email:")
        mock_askstring.assert_any_call("License Verification", "Enter your license key:")
        mock_showerror.assert_called_once_with("License Error", "Invalid license key. Please try again.")
        self.assertFalse(LICENSED)

    @patch("subprocess.Popen")
    def test_start_bot(self, mock_popen):
        """Test starting a bot process for a user."""
        mock_popen.return_value = MagicMock()

        user = {"username": "testuser", "password": "testpass", "stream_username": "teststream", "game_name": "testgame", "openai_api_key": "apikey", "stream_language": "English"}
        time_label = MagicMock()
        
        self.app.start_bot(user, time_label)
        
        mock_popen.assert_called_once_with([sys.executable, "bot.py", "testuser", "testpass", "teststream", "testgame", "apikey", "English"],
                                           stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        self.assertIn("testuser", self.app.processes)

    @patch("subprocess.Popen")
    def test_stop_bot(self, mock_popen):
        """Test stopping a bot process."""
        mock_process = MagicMock()
        self.app.processes["testuser"] = mock_process
        self.app.threads["testuser"] = threading.Thread(target=lambda: None)
        self.app.start_times["testuser"] = time.time()

        user = {"username": "testuser"}
        
        with patch("tkinter.messagebox.showinfo") as mock_info:
            self.app.stop_bot(user)
            mock_info.assert_called_once_with("Bot Stopped", "Bot for user testuser has been stopped.")
            self.assertNotIn("testuser", self.app.processes)

    @patch("tkinter.messagebox.showinfo")
    @patch("tkinter.messagebox.showwarning")
    def test_delete_user(self, mock_showwarning, mock_showinfo):
        """Test deleting a user."""
        user = {"username": "testuser"}
        frame = MagicMock()

        self.app.users = [user]
        self.app.processes = {}

        self.app.delete_user(user, frame)

        mock_showinfo.assert_called_once_with("User Deleted", "User testuser has been successfully deleted.")
        self.assertNotIn(user, self.app.users)
        frame.destroy.assert_called_once()

if __name__ == "__main__":
    unittest.main()
