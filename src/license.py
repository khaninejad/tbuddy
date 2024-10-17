import os
import json
import requests
from tkinter import messagebox, simpledialog
from device import get_device_id  # Assuming this correctly fetches the device_id

LICENSE_FILE = "license.json"

class LicenseManager:
    def __init__(self):
        self.email = None
        self.serial_number = None
        self.device_id = get_device_id()
        self.LICENSED = False
        self.PLAN_TYPE = "Free"

    def register_license(self):
        """Registers the license by sending email and device_id to the server."""
        email = simpledialog.askstring("Registration", "Enter your email:")

        if not email:
            messagebox.showerror("Registration Error", "Email is required.")
            return False

        self.email = email
        url = "https://jzf859i862.execute-api.eu-west-1.amazonaws.com/default/license-register"
        payload = json.dumps({
            "device_id": self.device_id,
            "email": self.email
        })
        
        print(payload)

        headers = {'Content-Type': 'application/json'}

        try:
            response = requests.post(url, headers=headers, data=payload)
            if response.status_code == 200:
                messagebox.showinfo("Registration", "An email with your serial number has been sent.")
                return True
            else:
                messagebox.showerror("Registration Error", f"Registration failed with status code {response.status_code}.")
                return False
        except requests.RequestException as e:
            messagebox.showerror("Registration Error", f"Failed to register: {e}")
            return False

    def verify_license(self):
        """Verifies the license using the entered serial number and saved data."""
        try:
            with open(LICENSE_FILE, "r") as f:
                license_data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            print("Error: License file not found or corrupt.")
            return False

        device_id = license_data.get("device_id")
        email = license_data.get("email")
        serial_number = license_data.get("serial_number")

        if not all([device_id, email, serial_number]):
            print("Error: Missing required fields in license data.")
            return False

        url = "https://jzf859i862.execute-api.eu-west-1.amazonaws.com/default/license-verify"
        payload = json.dumps({
            "device_id": device_id,
            "email": email,
            "serial_number": serial_number
        })

        headers = {'Content-Type': 'application/json'}

        try:
            response = requests.post(url, headers=headers, data=payload)
            if response.status_code == 200:
                response_json = response.json()
                license_record = response_json.get('licenseRecord', None)

                if license_record:
                    self.LICENSED = True
                    self.PLAN_TYPE = license_record["type"]
                    return license_record
                else:
                    print("Error: 'licenseRecord' not found in response.")
                    return False
            else:
                print(f"Error: Request failed with status code {response.status_code}")
                return False
        except requests.RequestException as e:
            print(f"Error: HTTP request failed: {e}")
            return False

    def prompt_for_serial_number(self):
        """Prompts the user to input their email and serial number after receiving the email."""
        email = simpledialog.askstring("License Verification", "Enter your email:")
        serial_number = simpledialog.askstring("License Verification", "Enter your Serial Number:")

        if not (email and serial_number):
            messagebox.showerror("License Verification", "Both email and serial number are required.")
            return False

        self.email = email
        self.serial_number = serial_number
        self.save_license()
        license_record = self.verify_license()

        if license_record:
            self.LICENSED = True
            self.PLAN_TYPE = license_record["type"]
            return True
        else:
            self.LICENSED = False
            self.PLAN_TYPE = "Free"
            messagebox.showerror("License Verification", "Invalid License")
            return False

    def save_license(self):
        """Saves license data to a file after verification."""
        license_data = {
            "email": self.email,
            "serial_number": self.serial_number,
            "device_id": self.device_id
        }

        with open(LICENSE_FILE, "w") as license_file:
            json.dump(license_data, license_file)

        print(f"License saved for {self.email}.")

    def check_license_on_startup(self):
        """Checks if a saved license exists and verifies it, otherwise prompts registration."""
        print("Checking for license on startup...")

        if os.path.exists(LICENSE_FILE):
            print(f"License file {LICENSE_FILE} found.")
            license_record = self.verify_license()

            if license_record:
                self.LICENSED = True
                self.PLAN_TYPE = license_record["type"]
                print(f"License valid. Plan type: {self.PLAN_TYPE}")
            else:
                print("Invalid or expired license. Prompting for serial number input...")
                self.prompt_for_serial_number()
        else:
            print("No license file found. Prompting for registration...")
            if self.register_license():
                self.prompt_for_serial_number()
