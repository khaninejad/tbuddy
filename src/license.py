import requests
import json

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

    url = "https://vvglmk8ma1.execute-api.eu-west-1.amazonaws.com/default/license-verify"

    payload = json.dumps({
        "device_id": device_id,
        "email": email,
        "serial_number": serial_number
    })

    headers = {
        'Content-Type': 'application/json'
    }

    # Send POST request
    try:
        response = requests.post(url, headers=headers, data=payload)
        print(response)
        # Check the response status
        if response.status_code == 200:
            return True
        else:
            print(f"Request failed with status code: {response.status_code}")
            return False
    except requests.RequestException as e:
        print(f"HTTP request failed: {e}")
        return False
