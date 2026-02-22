import json
import os
from pathlib import Path
import platform
import subprocess
import time
from typing import List
import httpx
from pydantic import ValidationError
from models import LinearMode, Settings, VersionInfo, VersionStatus
from parseArg import extractVersion
from vars import APP_NAME, APP_RAW_VERSION, APP_RC, APP_VERSION

DEV_MODE = os.getenv("DEV")
ROOT_DIR = Path(os.path.realpath(__file__)).parent
SOCKET_DIR = (ROOT_DIR / ".sock") if DEV_MODE else Path(f"/run/user/{os.getuid()}")
SOCKET_PATH = str(SOCKET_DIR / "ll-connect-wireless.sock")
CACHE_DIR = Path(os.path.expanduser("~/.cache/")) / APP_NAME
CACHE_PATH = CACHE_DIR / "remoteVer.json"
CONFIG_DIR = Path(os.path.expanduser("~/.config/")) / APP_NAME
CONFIG_PATH = CONFIG_DIR / "config.json"

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

CACHE_TTL = 75 
NOTIFY_TTL = 600

def check_latest_version() -> VersionStatus:
    latest = load_version_cache()
    outdated = is_outdated(latest)

    notify = should_notify(outdated, latest)

    if notify:
        latest.last_notified = time.time()
        save_version_cache(latest)
    return VersionStatus(
        data=latest,
        outdated=outdated,
        notified=not notify
    )

def version_tuple(semver: str):
    try:
        major, minor, patch = map(int, semver.split("."))
        return (major, minor, patch)
    except:
        return (0, 0, 0)

def is_outdated(latest: VersionInfo) -> bool:
    new_ver = version_tuple(latest.semver) > version_tuple(APP_VERSION)
    graduation = (
        latest.semver == APP_VERSION
        and APP_RC > 0
        and latest.rc == 0
    )
    new_rc = (
        latest.semver == APP_VERSION
        and latest.rc > APP_RC
    )

    return new_ver or graduation or new_rc

def should_notify(outdated: bool, latest: VersionInfo) -> bool:
    if not outdated:
        return False

    last = latest.last_notified or 0
    return (time.time() - last) > NOTIFY_TTL

def load_version_cache():
    os.makedirs(CACHE_DIR, exist_ok=True)

    if not os.path.exists(CACHE_PATH):
        version = fetch_github_tag()
        save_version_cache(version)
        return version

    if time.time() - os.path.getmtime(CACHE_PATH) > CACHE_TTL:
        version = fetch_github_tag()
        save_version_cache(version)
        return version

    try:
        with open(CACHE_PATH, "r") as f:
            data = json.load(f)

        data = VersionInfo(**data)
        if data.last_notified and data.last_notified > time.time(): data.last_notified = 0
        return data

    except (json.JSONDecodeError, ValidationError, OSError):
        version = fetch_github_tag()
        save_version_cache(version)
        return version

def save_version_cache(version: VersionInfo):
    os.makedirs(CACHE_DIR, exist_ok=True)

    with open(CACHE_PATH, "w") as f:
        json.dump(version.model_dump(), f)

def fetch_github_tag():
    current_ver = extractVersion(APP_RAW_VERSION)
    repo = "Yoinky3000/LL-Connect-Wireless"
    url = f"https://api.github.com/repos/{repo}/releases"

    TEST_MODE = DEV_MODE and False 
    test_releases = [
        {"tag_name": "v1.2.1-rc9-rel3"},
        {"tag_name": "1.1.0-rel5"},
        {"tag_name": "1.1.0-rc2-rel1"},
    ]

    try:
        if TEST_MODE:
            release_res = test_releases
        else:
            with httpx.Client(timeout=5.0) as client:
                response = client.get(url)
                if response.status_code == 200:
                    release_res = response.json()
                else:
                    release_res = None

        if not release_res:
            return current_ver
        
        releases: List[VersionInfo] = []
        dist, arch, ext = get_build_identity()
        match_pattern = f"{dist}.{arch}{ext}"
        for r in release_res:
            assets = r.get("assets", [])
            installer_url=None 
            for asset in assets:
                if match_pattern in asset["name"]:
                    installer_url = asset["browser_download_url"]
                    break
            releases.append(extractVersion(raw_tag=r["tag_name"].lstrip('v'), release_note=r.get("body", "No release notes provided."), installer_url=installer_url))
        if APP_RC == 0:
            for r in releases:
                if not r.rc:
                    return r
        else:
            for r in releases:
                if r.rc == 0:
                    return r
                
                if r.semver == APP_VERSION and r.rc > 0:
                    return r
        return current_ver

    except Exception as e:
        print(f"Failed to fetch latest tag: {e}")
        return current_ver

def load_settings() -> Settings:
    os.makedirs(CONFIG_DIR, exist_ok=True)

    settings = Settings()
    changed = False

    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r") as f:
                raw = json.load(f)

            if "mode" in raw:
                try:
                    settings.mode = raw["mode"]
                except Exception:
                    changed = True

            if "linear" in raw:
                try:
                    settings.linear = LinearMode(**raw["linear"])
                except ValidationError:
                    changed = True

        except Exception:
            changed = True
    else:
        changed = True

    if changed:
        save_settings(settings)

    return settings

def save_settings(settings: Settings):
    with open(CONFIG_PATH, "w") as f:
        json.dump(settings.model_dump(), f, indent=4)

def parse_curve_input(curve: str) -> LinearMode:
    if curve.isdigit():
        pwm = int(curve)
        return LinearMode(
            min_temp=60,
            max_temp=61,
            min_pwm=pwm,
            max_pwm=pwm
        )

    try:
        part1, part2 = curve.split(",")
        min_t, min_p = map(int, part1.split(":"))
        max_t, max_p = map(int, part2.split(":"))

        return LinearMode(
            min_temp=min_t,
            min_pwm=min_p,
            max_temp=max_t,
            max_pwm=max_p
        )
    except Exception:
        raise ValueError(
            "Invalid format. Use minTemp:minPwm,maxTemp:maxPwm or single integer."
        )