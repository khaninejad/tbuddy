import requests
import subprocess
import platform
import os
import zipfile
import shutil

class UpdateChecker:
    def __init__(self, current_version, app_dir=None):
        """
        Initialize the UpdateChecker instance.

        :param current_version: The current version of the application.
        :param app_dir: The directory where the application is installed (optional).
        """
        self.current_version = current_version
        self.update_url = "https://jzf859i862.execute-api.eu-west-1.amazonaws.com/default/release-check"
        self.app_dir = app_dir if app_dir else os.path.dirname(os.path.abspath(__file__))

    def check_for_updates(self):
        """
        Check for updates by comparing the current version with the last release.
        If an update is available, download, extract, and install the new version.
        """
        print(f"Current Version: {self.current_version}")

        response = self._get_last_release_info()
        if response:
            last_release = response["last_release"]
            last_release_version = last_release["version"]
            print(f"Last Release Version: {last_release_version}")

            if self.compare_versions(self.current_version, last_release_version) < 0:
                print("Update available!")
                return True, last_release
            else:
                print("No updates available.")
                return False, None
        else:
            print("Failed to check for updates.")

    def _get_last_release_info(self):
        """
        Send a GET request to the update API endpoint and return the response JSON.
        """
        try:
            response = requests.get(self.update_url)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"Error fetching update info: {e}")
            return None

    def compare_versions(self, v1, v2):
        """
        Compare two version strings (e.g., '1.0.25' and '1.0.30').
        Return:
            -1 if v1 < v2
            0 if v1 == v2
            1 if v1 > v2
        """
        v1_parts = list(map(int, v1.split('.')))
        v2_parts = list(map(int, v2.split('.')))

        for part1, part2 in zip(v1_parts, v2_parts):
            if part1 < part2:
                return -1
            elif part1 > part2:
                return 1

        # If all parts are equal, the versions are equal
        if len(v1_parts) < len(v2_parts):
            return -1
        elif len(v1_parts) > len(v2_parts):
            return 1
        else:
            return 0

    def download_update(self, last_release):
        """
        Download the update based on the current platform.
        """
        current_platform = platform.system()
        print(f"Current Platform: {current_platform}")

        if current_platform == "Darwin":  # macOS
            download_url = last_release["macos"]
        elif current_platform == "Windows":
            download_url = last_release["windows"]
        elif current_platform == "Linux":
            download_url = last_release["linux"]
        else:
            print("Unsupported platform.")
            return

        # Download the update
        update_filename = f"tbuddy-{current_platform}-v{last_release['version']}.zip"
        with requests.get(download_url, stream=True) as r:
            r.raise_for_status()
            with open(update_filename, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)

        print(f"Update downloaded: {update_filename}")
        return update_filename

    def extract_update(self, last_release, update_filename):
        """
        Extract the downloaded update zip file.
        """
        try:
            with zipfile.ZipFile(update_filename, 'r') as zip_ref:
                extract_dir = os.path.join(self.app_dir, f"update_{last_release['version']}")
                os.makedirs(extract_dir, exist_ok=True)
                zip_ref.extractall(extract_dir)
            print(f"Update extracted to: {extract_dir}")
        except zipfile.BadZipFile as e:
            print(f"Error extracting update: {e}")

    def install_update(self, last_release):
        """
        Install the extracted update by replacing the old application files.
        """
        # Backup the current application directory (optional)
        # shutil.make_archive(f"backup_{self.current_version}", 'zip', self.app_dir)

        extract_dir = os.path.join(self.app_dir, f"update_{last_release['version']}")
        for root, dirs, files in os.walk(extract_dir):
            for file in files:
                file_path = os.path.join(root, file)
                rel_path = os.path.relpath(file_path, extract_dir)
                dest_path = os.path.join(self.app_dir, rel_path)
                os.makedirs(os.path.dirname(dest_path), exist_ok=True)
                shutil.copy2(file_path, dest_path)

        print("Update installed successfully!")
        # Clean up the extract directory
        shutil.rmtree(extract_dir)