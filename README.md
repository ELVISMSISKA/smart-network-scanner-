# 🛰️ Network Scanner & Remote Shutdown Tool

A clean, step‑by‑step guide for a Python tool that scans your local network, identifies connected devices (PCs, servers, mobile/IoT), and can **optionally** shut down PCs/servers you manage. Mobile and most IoT devices are detected but **never** shut down for safety.

---

## ✅ At a glance

* Detects active devices on your subnet
* Shows **IP · Hostname · MAC · Vendor/Type**
* Flags mobile devices (Apple/Samsung/etc.)
* **Remote shutdown** (PCs/servers you own/manage):

  * Windows via `shutdown /m` (admin required)
  * Linux/macOS via SSH (key‑based only)
* Saves results to `alive_hosts.txt`

> **Use responsibly.** Only scan/shutdown devices you own or are authorized to administer.

---

## 1) Requirements

* **Python**: 3.7+
* **OS**: Windows, Linux, or macOS
* **Permissions**: Admin rights to remotely shut down Windows PCs; SSH key access for Linux/macOS
* **Python deps** (installed via `requirements.txt`):

  * `Flask`
  * `mac-vendor-lookup`

* Optional extension dependencies:

  * `psutil` *(optional if you extend the scanner)*

---

## 2) Install (step‑by‑step)

1. **Clone the repo**

   ```bash
   git clone https://github.com/chromeheartbeat/Network-Scanner-Shutdown.git
   cd network-scanner-shutdown
   ```
2. **(Optional) Create a virtual environment**

   ```bash
   # Windows (PowerShell)
   python -m venv .venv
   .\.venv\Scripts\activate

   # macOS/Linux (bash/zsh)
   python3 -m venv .venv
   source .venv/bin/activate
   ```
3. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

---

## 3) Optional: Prepare remote shutdown

### A) Windows targets

1. Sign in with an account that has **local admin** rights on the target.
2. Ensure the target allows RPC shutdown (typical in managed networks). If needed, allow through firewall/group policy.
3. Make sure both machines can resolve each other (hostname or IP) and are on the same network/VPN.

### B) Linux/macOS targets (SSH key‑based)

1. **Generate an SSH key** (if you don't already have one):

   ```bash
   ssh-keygen -t rsa -b 4096
   ```
2. **Copy your public key** to the target:

   ```bash
   ssh-copy-id username@TARGET_IP
   ```
3. **Test login** (should not prompt for a password):

   ```bash
   ssh username@TARGET_IP
   ```

---

## 4) Run the scanner

1. **Start the script**

   ```bash
   python network_scan.py
   ```
   Or provide more control with CLI options:

   ```bash
   python network_scan.py --network 192.168.1.0/24 --output alive_hosts.txt --csv alive_hosts.csv
   python network_scan.py --skip-shutdown
   python network_scan.py --no-save
   ```
2. The tool will:

   * Detect your local IP and subnet
   * Ping/sweep the subnet
   * Resolve **Hostname · MAC · Vendor/Type**
   * Save a list of active hosts to `alive_hosts.txt`

3. **Review output** in your terminal, e.g.:

   ```text
   [+] Active Devices:
    1. 10.125.131.1   | Hostname: router.local   | MAC: 00:11:22:33:44:55 | Type: Router
    2. 10.125.131.20  | Hostname: printer.office | MAC: 3c:52:82:9a:1f:2b | Type: HP
    3. 10.125.131.42  | Hostname: laptop-john    | MAC: a0:b1:c2:d3:e4:f5 | Type: Dell
    4. 10.125.131.55  | Hostname: iPhone.local   | MAC: 28:cf:e9:xx:xx:xx | Type: Mobile (Apple)
    5. 10.125.131.60  | Hostname: android-12345  | MAC: 88:32:9b:xx:xx:xx | Type: Mobile (Samsung)
   ```

---

## 5) Optional: Remote shutdown flow

After the scan, you'll be prompted:

```text
Do you want to shutdown a device? (y/n):
```

### If **Yes**

1. Select the device number from the list.
2. If the device is **Windows PC/Server**:

   * The tool uses the native Windows shutdown mechanism over RPC.
3. If the device is **Linux/macOS**:

   * You’ll be prompted for:

     * **SSH username**
     * **Path to your private key** (e.g., `~/.ssh/id_rsa`)

### If the device is **Mobile/IoT**

You'll see:

```text
[!] Shutdown not supported for mobile devices.
```

---

## 6) Files generated

* `alive_hosts.txt` — list of active devices discovered during the scan.

---

## 7) Troubleshooting

* **No devices found**: Confirm you're on the correct network/subnet; temporarily test with AV/firewall relaxed (admin networks only).
* **Windows shutdown fails**: Ensure admin rights, RPC allowed, and the target is reachable (try `ping TARGET_IP`).
* **SSH prompts for password**: Re‑copy your key with `ssh-copy-id` and verify file permissions on the target (`~/.ssh/authorized_keys`).

---

## 8) Safety & ethics

* Only scan and administer networks/devices you own or are explicitly authorized to manage.
* Follow your organization’s AUP and local laws.

---

## 9) Run the Web UI

A lightweight Flask interface is included for browser-based scanning and shutdown control.

1. Install the project requirements:

```bash
pip install -r requirements.txt
```
2. Start the web app:

```bash
python app.py
```
3. Open your browser at:

```bash
http://127.0.0.1:5000
```

Use the web page to scan a network and trigger remote shutdowns for managed Windows or Linux/macOS devices.

The results page also includes a filter box and a CSV export button so you can download the current scan results directly.

## 10) License

This project is licensed under the **MIT License**. Use at your own risk and only on authorized networks.
