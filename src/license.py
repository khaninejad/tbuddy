import os
from tkinter import messagebox, simpledialog
import requests
import json

LICENSE_FILE = "../license.json"  

def verify_license(json_file='../license.json'):
    # Load data from the specified JSON file
    try:
        with open(json_file) as f:
            license_data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error loading license data: {e}")
        return False

    # Extract values from the loaded JSON
    device_id = license_data.get("device_id")
    email = license_data.get("email")
    serial_number = license_data.get("serial_number")

    # Check if any of the required fields are missing
    if not all([device_id, email, serial_number]):
        print("Missing required fields in the license data.")
        return False

    url = "https://jzf859i862.execute-api.eu-west-1.amazonaws.com/default/license-verify"

    payload = json.dumps({
        "device_id": device_id,
        "email": email,
        "serial_number": serial_number
    })

    headers = {
        'Content-Type': 'application/json'
    }

    try:
        response = requests.post(url, headers=headers, data=payload)

        # Check for a 200 status code
        if response.status_code == 200:
            try:
                # Attempt to parse response content as JSON
                response_json = response.json()

                # Check if the 'licenseRecord' key exists in the response
                if 'licenseRecord' in response_json:
                    # Return the license record object
                    return response_json['licenseRecord']
                else:
                    print("Error: 'licenseRecord' not found in response.")
                    return False
            except json.JSONDecodeError:
                print("Error: Response content is not valid JSON.")
                return False
        else:
            print(f"Request failed with status code: {response.status_code}")
            print(f"Response content: {response.content}")
            return False
    except requests.RequestException as e:
        print(f"HTTP request failed: {e}")
        return False

def verify_license_data(self):
    """Verify the license by calling an API endpoint or reading from stored license file."""
    global LICENSED, PLAN_TYPE
    print("Starting manual license verification...")  # Debugging statement

    email = simpledialog.askstring("License Verification", "Enter your email:")
    serial_number = simpledialog.askstring("License Verification", "Enter your Serial Number:")

    if email and serial_number:
        print(f"Verifying license for {email} with serial {serial_number}")  # Debugging statement
        license = verify_license()

        if license and license["valid"]:
            LICENSED = True
            PLAN_TYPE = license["plan_type"]
            messagebox.showinfo("License Verification", f"License Verified! Plan Type: {PLAN_TYPE}")
            self.verify_license_button.config(text=f"Licensed - {PLAN_TYPE} Plan", state="disabled")
            self.save_license(email, serial_number)  # Save license to file
        else:
            LICENSED = False
            PLAN_TYPE = "Free"
            messagebox.showerror("License Verification", "Invalid License")
    else:
        messagebox.showerror("License Verification", "Email and Serial Number required.")

def save_license(email, serial_number):
    """Save the verified license to a file."""
    license_data = {"email": email, "serial_number": serial_number}
    print(f"Saving license for {email}")  # Debugging statement
    with open(LICENSE_FILE, "w") as license_file:
        json.dump(license_data, license_file)
        
        
def check_license_on_startup():
    """Check if there is a saved license and verify it on startup."""
    global LICENSED, PLAN_TYPE
    print("Checking for license on startup...")  # Debugging statement

    if os.path.exists(LICENSE_FILE):
        print(f"License file {LICENSE_FILE} found.")  # Debugging statement
        with open(LICENSE_FILE, "r") as license_file:
            try:
                license_data = json.load(license_file)
                email = license_data.get("email")
                serial_number = license_data.get("serial_number")
                
                print(f"Loaded license email: {email}, serial: {serial_number}")  # Debugging

                if email and serial_number:
                    # Verify license via API or local check
                    license = verify_license()
                    
                    if license and license["type"] == "Premium":
                        LICENSED = True
                        PLAN_TYPE = license["type"]
                        self.verify_license_button.config(text=f"Licensed - {PLAN_TYPE} Plan", state="disabled")
                        print(f"License valid. Plan type: {PLAN_TYPE}")  # Debugging
                    else:
                        LICENSED = False
                        PLAN_TYPE = "Free"
                        print("License invalid or expired.")  # Debugging
                else:
                    print("License file is missing email or serial number.")  # Debugging
                    LICENSED = False
                    PLAN_TYPE = "Free"
            except json.JSONDecodeError:
                print("Error: Could not decode license file.")  # Debugging
                LICENSED = False
                PLAN_TYPE = "Free"
    else:
        print(f"No license file {LICENSE_FILE} found. Defaulting to Free plan.")  # Debugging
        LICENSED = False
        PLAN_TYPE = "Free"