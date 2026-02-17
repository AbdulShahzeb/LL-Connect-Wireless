import os
from pathlib import Path
import platform
import subprocess
from vars import APP_NAME

DEV_MODE = os.getenv("DEV")
ROOT_DIR = Path(os.path.realpath(__file__)).parent
SOCKET_DIR = (ROOT_DIR / ".sock") if DEV_MODE else Path("/run") / APP_NAME
SOCKET_PATH = str(SOCKET_DIR / "ll-connect-wireless.sock")

def get_build_identity():
    arch = platform.machine()
    dist_info = {}
    try:
        with open("/etc/os-release") as f:
            for line in f:
                if "=" in line:
                    k, v = line.rstrip().split("=", 1)
                    dist_info[k] = v.strip('"')
    except FileNotFoundError:
        pass

    os_id = dist_info.get("ID", "linux")
    
    if os_id in ["fedora", "centos", "rhel"]:
        ext = ".rpm"
        try:
            dist_tag = subprocess.check_output(["rpm", "-E", "%{?dist}"], text=True).strip().strip('.')
        except:
            dist_tag = f"fc{dist_info.get('VERSION_ID', '')}"
    elif os_id in ["ubuntu", "debian"]:
        ext = ".deb"
        dist_tag = os_id + dist_info.get("VERSION_ID", "")
    else:
        ext = ".tar.gz"
        dist_tag = "linux"

    return dist_tag, arch, ext