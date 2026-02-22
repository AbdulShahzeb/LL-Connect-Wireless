import os
import shutil
import sys
import time
import argparse
import subprocess
from typing import Optional
import httpx
from utils import CACHE_DIR, CONFIG_DIR, SOCKET_PATH, check_latest_version, get_build_identity, load_settings, parse_curve_input, save_settings
from models import FanMode, LinearMode, Settings, SystemStatus, VersionInfo, VersionStatus
from vars import APP_RAW_VERSION, APP_NAME, APP_ALIAS
import shtab

def clear_console():
    sys.stdout.write("\033[H\033[J")
    sys.stdout.flush()

def fetch_state() -> SystemStatus:
    transport = httpx.HTTPTransport(uds=SOCKET_PATH)
    with httpx.Client(transport=transport) as client:
        resp = client.get("http://localhost/status")
        resp.raise_for_status()
        return SystemStatus(**resp.json())
    
def reload_service_settings():
    transport = httpx.HTTPTransport(uds=SOCKET_PATH)
    with httpx.Client(transport=transport) as client:
        client.post("http://localhost/reload-settings")

def render(status: SystemStatus):
    clear_console()
    print(f"LL-Connect-Wireless Monitor\n\n")

    print(f"CPU Temp: {status.cpu_temp:.1f} °C\n")
    print(f"{'Fan Address':17} | Fans | Cur % | Tgt % | RPM")
    print("-" * 72)

    for f in status.fans:
        cur_pct = int(f.pwm / 255 * 100)
        tgt_pct = int(f.target_pwm / 255 * 100)
        rpm = ", ".join(str(r) for r in f.rpm)

        print(
            f"{f.mac:17} | "
            f"{f.fan_count:>4} | "
            f"{cur_pct:>5}% | "
            f"{tgt_pct:>5}% | "
            f"{rpm}"
        )

def run_monitor():
    err = 0
    while True:
        try:
            state = fetch_state()
            render(state)
            err = 0
        except Exception as e:
            err += 1
            clear_console()
            print(f"Connection Lost. Retrying... ({err})")
            if err > 5:
                print(f"\nDaemon might be down. Try: {APP_NAME} status")
                sys.exit(1)
        time.sleep(1)

def run_systemctl(action: str, service = True):
    service_name = f"{APP_NAME}.service"
    
    try:
        command = ["systemctl", "--user", action]
        display = f"systemctl --user {action}"
        if service:
            command.append(service_name)
            display += f" {service_name}"
        print(f"Running: {display}...")
        subprocess.run(command, check=False)
        print("Done.")
    except subprocess.CalledProcessError as e:
        print(f"Error executing command: {e}")
        sys.exit(e.returncode)
    except FileNotFoundError:
        print("Error: 'systemctl' command not found. Are you sure you are using in Linux?")
        sys.exit(1)

def run_info(remote_ver: Optional[VersionStatus]):
    try:
        print("\033[1mLL-Connect-Wireless Information\033[0m")
        print("-" * 30)
        print(f"\033[1mCURRENT_VERSION:\033[0m {APP_RAW_VERSION}")
        
        if remote_ver:
            v = remote_ver.data
            print(f"\033[1mREMOTE_VERSION:\033[0m  {v.raw_tag}")
            release_note = getattr(v, "release_note", "")
        else: 
            print(f"\033[1mREMOTE_VERSION:\033[0m  Unknown")
            release_note = f"You can run '{APP_ALIAS} update' to update to latest version from GitHub."
        print("-" * 30)
        print("\033[1mCHANGE_LOG:\033[0m")
        print(release_note)
        print("-" * 30)
    except Exception as e:
        print(f"Could not connect to daemon: {e}")

def run_update(remote_ver: Optional[VersionStatus]):
    if not remote_ver:
        print("Could not retrieve version information from the daemon.")
        return

    if not remote_ver.outdated:
        print("You are already up to date.")
        return
    
    dist_tag, arch, ext = get_build_identity()
    print(f"\033[1mYour System Info\033[0m -")
    print(f"  Distribution Tag > {dist_tag}")
    print(f"  Architecture > {arch}")
    print(f"  Installer Extension > {ext}\n")
    
    url = remote_ver.data.installer_url
    if not url:
        print("\033[91mNo compatible installer found for your specific system architecture/distro.\033[0m")
        return

    tmp_path = f"/tmp/llcw_update{ext}"

    print(f"\n\033[1mUpdate Found: {remote_ver.data.raw_tag}\033[0m")
    print(f"Download URL: {url}")
    print(f"Target Path:  {tmp_path}")
    print("-" * 40)

    confirm = input("Do you want to proceed with the download and installation? (y/N): ").lower()
    if confirm != 'y':
        print("Update cancelled.")
        return

    print(f"\nDownloading {url}...")
    try:
        with httpx.Client(follow_redirects=True) as client:
            with client.stream("GET", url) as response:
                response.raise_for_status()
                with open(tmp_path, "wb") as f:
                    for chunk in response.iter_bytes():
                        f.write(chunk)
        
        print("Download complete. Starting installation...")
        if ext == ".rpm":
            subprocess.run(["sudo", "dnf", "install", "-y", tmp_path], check=True)
        elif ext == ".deb":
            subprocess.run(["sudo", "apt", "install", "-y", tmp_path], check=True)
        else:
            print(f"\033[93mAutomatic installation not supported for {ext}.\033[0m")
            print(f"Please install the file manually from: {tmp_path}")
            return
        try:
            os.remove(tmp_path)
        except OSError:
            pass
        print("Reloading systemd...")
        run_systemctl("daemon-reload", False)
        print("Refreshing service (if running)...")
        run_systemctl("try-restart")
        print("\033[92mLL-Connect-Wireless updated successfully!\033[0m")

    except httpx.HTTPError as e:
        print(f"\033[91mDownload failed: {e}\033[0m")
    except subprocess.CalledProcessError as e:
        print(f"\033[91mInstallation failed: {e}\033[0m")
    except Exception as e:
        print(f"\033[91mAn unexpected error occurred: {e}\033[0m")

def printOutdated(newVer: VersionInfo, wait = False):
    display = newVer.semver
    if newVer.rc:
        display += f" (RC{newVer.rc})"
    print(f"\n\033[93m[!] UPDATE AVAILABLE: Version {display} is out!\033[0m")
    print(f"Current version: {APP_RAW_VERSION}")
    print(f"Run '{APP_ALIAS} update' to update")
    print(f"Or you can download from: https://github.com/Yoinky3000/LL-Connect-Wireless/releases/tag/{newVer.raw_tag}\n")
    if wait: 
        time.sleep(5)

def show_settings(settings: Settings):
    print("\033[1mCurrent Settings\033[0m")
    print("-" * 30)
    print(f"Mode: {settings.mode}")
    print()
    print("Linear Mode:")
    print(f"  Min Temp : {settings.linear.min_temp} °C")
    print(f"  Max Temp : {settings.linear.max_temp} °C")
    print(f"  Min PWM  : {settings.linear.min_pwm}%")
    print(f"  Max PWM  : {settings.linear.max_pwm}%")
    print("-" * 30)


def show_linear_settings(settings: Settings):
    print("\033[1mLinear Mode Settings\033[0m")
    print("-" * 30)
    print(f"Min Temp : {settings.linear.min_temp} °C")
    print(f"Max Temp : {settings.linear.max_temp} °C")
    print(f"Min PWM  : {settings.linear.min_pwm}%")
    print(f"Max PWM  : {settings.linear.max_pwm}%")
    print("-" * 30)

def run_uninstall():
    confirm = input("Confirm? (y/N): ").lower()
    if confirm != "y":
        print("Uninstall cancelled.")
        return

    dist_tag, arch, ext = get_build_identity()
    print("Removing configuration...")
    shutil.rmtree(CONFIG_DIR, ignore_errors=True)
    shutil.rmtree(CACHE_DIR, ignore_errors=True)
    print(f"Uninstalling {APP_ALIAS}...")
    if ext == ".rpm":
        subprocess.run(["sudo", "dnf", "remove", "-y", APP_NAME], check=True)
    print("Stopping service...")
    run_systemctl("stop")
    run_systemctl("disable")
    print("Uninstall completed")

if __name__ == "__main__":
    try:
        parser = argparse.ArgumentParser(
            description=f"LL-Connect-Wireless (LLCW) CLI (Version: {APP_RAW_VERSION})",
            epilog=f"You can also use '{APP_NAME}' without arguments to see live monitor.\n\n'{APP_ALIAS}' is also an alias command to '{APP_NAME}'"
        )
        
        subparsers = parser.add_subparsers(dest="command", help="Available commands")

        subparsers.add_parser("help", help="same as -h/--help")

        subparsers.add_parser("info", help=f"show app version info and changelog of {APP_ALIAS}")

        subparsers.add_parser("update", help=f"check and update {APP_ALIAS} to latest version")

        subparsers.add_parser("status", help=f"show systemd service status")

        subparsers.add_parser("enable", help=f"enable {APP_ALIAS} service and start it")

        subparsers.add_parser("disable", help=f"disable {APP_ALIAS} service")

        subparsers.add_parser("start", help=f"start the {APP_ALIAS} service")

        subparsers.add_parser("stop", help=f"stop the {APP_ALIAS} service")

        subparsers.add_parser("restart", help=f"restart the {APP_ALIAS} service")
        
        subparsers.add_parser("monitor", help="show live fan monitor (Default to it if no command is provided)")

        subparsers.add_parser("uninstall", help=f"stop, disable and remove {APP_ALIAS}")

        settings_parser = subparsers.add_parser("settings", help="Manage settings")
        settings_sub = settings_parser.add_subparsers(dest="settings_cmd")
        settings_sub.add_parser(
            "set-mode",
            help="set control mode"
        ).add_argument(
            "mode",
            choices=[m.value for m in FanMode],
            help="control mode"
        )
        settings_sub.add_parser("reset", help="reset the settings")
        
        linear_parser = settings_sub.add_parser("linear", help="Linear mode settings")
        linear_sub = linear_parser.add_subparsers(dest="linear_cmd")

        linear_sub.add_parser("reset", help="reset linear curve")
        linear_set = linear_sub.add_parser("set-curve", help="set linear curve")
        linear_set.add_argument("curve", help="format: 'minT:minP,maxT:maxP', or just give a single pwm percentage for fixed pwm")

        parser.add_argument(
            "--print-completion",
            choices=shtab.SUPPORTED_SHELLS,
            help="print shell completion script",
        )

        args = parser.parse_args()

        if args.print_completion:
            print(shtab.complete(parser, shell=args.print_completion))
            sys.exit(0)

        is_monitor = args.command == "monitor" or args.command is None
        remoteVer = check_latest_version()
        if (remoteVer and remoteVer.outdated and not remoteVer.notified and not args.command == "info" and not args.command == "update"):
            printOutdated(remoteVer.data, is_monitor)

        if is_monitor:
            run_monitor()
        elif args.command == "uninstall":
            run_uninstall()
        elif args.command == "info":
            run_info(remoteVer)
        elif args.command == "update":
            run_update(remoteVer)
        elif args.command == "status":
            run_systemctl("status")
        elif args.command == "enable":
            run_systemctl("enable")
        elif args.command == "disable":
            run_systemctl("disable")
        elif args.command == "start":
            run_systemctl("start")
        elif args.command == "stop":
            run_systemctl("stop")
        elif args.command == "restart":
            run_systemctl("restart")
        elif args.command == "settings":
            settings = load_settings()

            if args.settings_cmd == "set-mode":
                settings.mode = args.mode
                save_settings(settings)
                reload_service_settings()
                print(f"Mode updated to {args.mode}")
            elif args.settings_cmd == "reset":
                save_settings(Settings())
                reload_service_settings()
                print(f"Finished reset")
            elif args.settings_cmd == "linear":
                if args.linear_cmd == "set-curve":
                    try:
                        new_curve = parse_curve_input(args.curve)
                        settings.linear = new_curve
                        save_settings(settings)
                        reload_service_settings()
                        print("Linear curve updated successfully.")
                    except Exception as e:
                        print(f"Error: {e}")
                elif args.linear_cmd == "reset":
                    settings.linear = LinearMode()
                    save_settings(settings)
                    reload_service_settings()
                    print(f"Finished reset linear curve")
                else:
                    show_linear_settings(settings)
            else:
                show_settings(settings)
        else:
            parser.print_help()
    except KeyboardInterrupt:
        sys.exit(0)