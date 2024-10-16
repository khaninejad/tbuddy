import os
import platform
import uuid
from getmac import get_mac_address
import psutil
import subprocess

def get_disk_serial():
    """Retrieve the hard disk serial number based on the operating system."""
    try:
        if platform.system() == "Windows":
            # Use WMIC to get the disk serial number
            serial = subprocess.check_output("wmic diskdrive get serialnumber", shell=True).decode().strip().split('\n')[1].strip()
        elif platform.system() == "Linux":
            # Attempt to read from /dev/disk/by-id
            serial = subprocess.check_output("lsblk -o SERIAL", shell=True).decode().strip().split('\n')[1].strip()
        elif platform.system() == "Darwin":  # macOS
            serial = subprocess.check_output("system_profiler SPSerialATADataType | awk '/Serial Number/ { print $3 }'", shell=True).decode().strip()
        else:
            serial = "unknown"
    except Exception as e:
        print(f"Error retrieving disk serial: {e}")
        serial = "unknown"
    return serial

def get_device_id():
    # Get MAC Address
    mac_address = get_mac_address()

    # Get UUID (available on most systems)
    system_uuid = None
    if platform.system() == "Windows":
        try:
            system_uuid = subprocess.check_output("wmic csproduct get uuid").decode().strip().split('\n')[1].strip()
        except Exception:
            system_uuid = "unknown"
    elif platform.system() == "Linux":
        try:
            with open('/etc/machine-id', 'r') as f:
                system_uuid = f.read().strip()
        except Exception:
            system_uuid = "unknown"
    elif platform.system() == "Darwin":  # macOS
        try:
            system_uuid = subprocess.check_output("system_profiler SPHardwareDataType | awk '/UUID/ { print $3 }'", shell=True).decode().strip()
        except Exception:
            system_uuid = "unknown"

    # Get the disk serial number
    disk_serial = get_disk_serial()

    # Combine the identifiers to create a unique device ID
    device_id_components = [mac_address, system_uuid, disk_serial]

    # Filter out 'unknown' values
    unique_device_id = "-".join(filter(lambda x: x and x != "unknown", device_id_components))

    # Fallback if all components are unknown
    if not unique_device_id:
        unique_device_id = str(uuid.uuid4())  # Generate a random UUID if all else fails

    return unique_device_id

# Generate the device ID
device_id = get_device_id()
print("Device ID:", device_id)
