import platform
import uuid
from getmac import get_mac_address
import subprocess

from utils import print_error, print_info

def get_disk_serial():
    """Retrieve the hard disk serial number based on the operating system."""
    try:
        if platform.system() == "Windows":
            
            serial = subprocess.check_output("wmic diskdrive get serialnumber", shell=True).decode().strip().split('\n')[1].strip()
        elif platform.system() == "Linux":
            
            serial = subprocess.check_output("lsblk -o SERIAL", shell=True).decode().strip().split('\n')[1].strip()
        elif platform.system() == "Darwin":  
            serial = subprocess.check_output("system_profiler SPSerialATADataType | awk '/Serial Number/ { print $3 }'", shell=True).decode().strip()
        else:
            serial = "unknown"
    except Exception as e:
        print_error(f"Error retrieving disk serial: {e}")
        serial = "unknown"
    return serial

def get_device_id():
    
    mac_address = get_mac_address()

    
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
    elif platform.system() == "Darwin":  
        try:
            system_uuid = subprocess.check_output("system_profiler SPHardwareDataType | awk '/UUID/ { print $3 }'", shell=True).decode().strip()
        except Exception:
            system_uuid = "unknown"

    
    disk_serial = get_disk_serial()

    
    device_id_components = [mac_address, system_uuid, disk_serial]

    
    unique_device_id = "-".join(filter(lambda x: x and x != "unknown", device_id_components))

    
    if not unique_device_id:
        unique_device_id = str(uuid.uuid4())  

    return unique_device_id


device_id = get_device_id()
print_info(f"Device ID: {device_id}")
