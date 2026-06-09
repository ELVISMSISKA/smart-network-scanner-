import csv
import os
import platform
import sys
import argparse
import ipaddress
import socket
import subprocess
from concurrent.futures import ThreadPoolExecutor
from mac_vendor_lookup import MacLookup

try:
    import psutil
except ImportError:
    psutil = None

# ------------------ Network Utilities ------------------ #

def ping(ip):
    """Ping an IP address, return True if alive."""
    param = "-n 1" if platform.system().lower() == "windows" else "-c 1"
    response = os.system(
        f"ping {param} -w 1000 {ip} >nul 2>&1" if platform.system().lower() == "windows"
        else f"ping {param} -W 1 {ip} >/dev/null 2>&1"
    )
    return response == 0

def get_hostname(ip):
    """Try to resolve hostname from IP."""
    try:
        return socket.getfqdn(ip)
    except Exception:
        return "Unknown"

def get_mac(ip):
    """Get MAC address from ARP table after pinging."""
    try:
        if platform.system().lower() == "windows":
            output = subprocess.check_output(f"arp -a {ip}", shell=True).decode()
        else:
            output = subprocess.check_output(f"arp -n {ip}", shell=True).decode()
        for line in output.splitlines():
            if ip in line:
                parts = line.split()
                for part in parts:
                    if ":" in part or "-" in part:  # MAC format
                        return part
        return "Unknown"
    except Exception:
        return "Unknown"

def detect_device_type(mac):
    """Guess device type based on MAC vendor."""
    try:
        vendor = MacLookup().lookup(mac)
        vendor_lower = vendor.lower()
        if any(x in vendor_lower for x in ["apple", "samsung", "huawei", "xiaomi", "oneplus", "oppo"]):
            return f"Mobile ({vendor})"
        return vendor
    except Exception:
        return "Unknown"

# ------------------ Auto-detection and output helpers ------------------ #

def get_default_network():
    """Try to detect a local IPv4 network automatically."""
    if psutil is None:
        return None

    for iface_addrs in psutil.net_if_addrs().values():
        for addr in iface_addrs:
            if addr.family == socket.AF_INET and addr.address != "127.0.0.1":
                if addr.netmask:
                    try:
                        network = ipaddress.IPv4Network(f"{addr.address}/{addr.netmask}", strict=False)
                        return str(network)
                    except Exception:
                        continue
    return None


def save_hosts_text(hosts, filename):
    with open(filename, "w", encoding="utf-8") as f:
        for host in hosts:
            f.write(f"{host['ip']} | Hostname: {host['hostname']} | MAC: {host['mac']} | Type: {host['type']}\n")


def save_hosts_csv(hosts, filename):
    fieldnames = ["ip", "hostname", "mac", "type"]
    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(hosts)

# ------------------ Scanner ------------------ #

def scan_ip(ip):
    """Scan a single IP, return details if alive."""
    if ping(ip):
        hostname = get_hostname(ip)
        mac = get_mac(ip)
        device_type = detect_device_type(mac) if mac != "Unknown" else "Unknown"
        return {"ip": ip, "hostname": hostname, "mac": mac, "type": device_type}
    return None

def scan_network(network):
    """Scan the network and return list of alive hosts with details."""
    alive_hosts = []
    with ThreadPoolExecutor(max_workers=100) as executor:
        results = executor.map(scan_ip, [str(ip) for ip in ipaddress.IPv4Network(network, strict=False).hosts()])
        for result in results:
            if result:
                alive_hosts.append(result)
    return alive_hosts

# ------------------ Shutdown ------------------ #

def shutdown_device(ip, windows=True, username=None, key_path=None):
    """Shutdown a remote device (Windows via RPC, Linux/Mac via SSH keys)."""
    if windows:
        try:
            cmd = f"shutdown /s /m \\\\{ip} /t 0 /f"
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            if result.returncode == 0:
                message = f"[+] Shutdown command sent to {ip}"
                print(message)
                return True, message
            message = f"[!] Failed to shutdown {ip}: {result.stderr.strip()}"
            print(message)
            return False, message
        except Exception as e:
            message = f"[!] Error shutting down {ip}: {e}"
            print(message)
            return False, message
    else:
        if username is None or key_path is None:
            message = "[!] Username and key_path required for SSH shutdown."
            print(message)
            return False, message
        try:
            cmd = f'ssh -i {key_path} -o StrictHostKeyChecking=no {username}@{ip} "sudo shutdown -h now"'
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            if result.returncode == 0:
                message = f"[+] Shutdown command sent to {ip}"
                print(message)
                return True, message
            message = f"[!] Failed to shutdown {ip}: {result.stderr.strip()}"
            print(message)
            return False, message
        except Exception as e:
            message = f"[!] Error shutting down {ip}: {e}"
            print(message)
            return False, message

# ------------------ Main ------------------ #

def main():
    parser = argparse.ArgumentParser(description="Scan a local network and optionally issue remote shutdown commands.")
    parser.add_argument("--network", "-n", help="Network CIDR to scan, e.g. 192.168.1.0/24")
    parser.add_argument("--output", "-o", default="alive_hosts.txt", help="Text output file")
    parser.add_argument("--csv", help="Optional CSV output file")
    parser.add_argument("--no-save", action="store_true", help="Do not save results to disk")
    parser.add_argument("--skip-shutdown", action="store_true", help="Scan only; skip interactive shutdown prompt")
    args = parser.parse_args()

    network = args.network
    if not network:
        network = get_default_network()
        if network is None:
            print("[!] Could not auto-detect the local network. Please provide --network.")
            return 1
    else:
        try:
            network = str(ipaddress.ip_network(network, strict=False))
        except ValueError:
            print("[!] Invalid network format. Use a CIDR like 192.168.1.0/24.")
            return 1

    print(f"[+] Scanning network: {network}")
    alive = scan_network(network)

    if alive:
        print("\n[+] Active Devices:")
        for i, host in enumerate(alive, 1):
            print(f" {i}. {host['ip']} | Hostname: {host['hostname']} | MAC: {host['mac']} | Type: {host['type']}")

    else:
        print("\n[!] No active devices were found.")

    if not args.no_save:
        save_hosts_text(alive, args.output)
        print(f"\n[+] Results saved to {args.output}")
        if args.csv:
            save_hosts_csv(alive, args.csv)
            print(f"[+] CSV results saved to {args.csv}")

    if not args.skip_shutdown and alive:
        choice = input("\nDo you want to shutdown a device? (y/n): ").strip().lower()
        if choice == "y":
            try:
                device_num = int(input("Enter the device number from the list: ").strip())
                target = alive[device_num - 1]
                print(f"[+] Selected: {target['ip']} ({target['hostname']}) - {target['type']}")

                if "Mobile" in target["type"]:
                    print("[!] Shutdown not supported for mobile devices.")
                else:
                    os_type = input("Is the target Windows (w) or Linux/Mac (l)? ").strip().lower()
                    if os_type == "w":
                        success, message = shutdown_device(target["ip"], windows=True)
                    else:
                        username = input("Enter SSH username: ").strip()
                        key_path = input("Enter path to your private key (e.g., ~/.ssh/id_rsa): ").strip()
                        success, message = shutdown_device(target["ip"], windows=False, username=username, key_path=key_path)

                    if success:
                        print("[+] Shutdown command completed.")
                    else:
                        print(message)

            except Exception as e:
                print(f"[!] Invalid selection: {e}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
# ------------------ End of network_scan.py ------------------ #