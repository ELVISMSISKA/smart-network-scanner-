from flask import Flask, render_template, request, redirect, url_for, flash, session, make_response
import ipaddress
from network_scan import scan_network, shutdown_device

app = Flask(__name__)
app.secret_key = "replace-with-a-secure-secret"


@app.route("/", methods=["GET", "POST"])
def index():
    default_network = "192.168.1.0/24"
    if request.method == "POST":
        network = request.form.get("network", default_network).strip()
        try:
            network = str(ipaddress.ip_network(network, strict=False))
            hosts = scan_network(network)
            session["last_scan_network"] = network
            session["last_scan_hosts"] = hosts
            if not hosts:
                flash("Scan completed but no devices were discovered.", "warning")
            return render_template(
                "index.html",
                network=network,
                hosts=hosts,
                scan_done=True,
            )
        except ValueError:
            flash("Invalid network format. Use a CIDR like 192.168.1.0/24.", "danger")
            return render_template(
                "index.html",
                network=network,
                hosts=[],
                scan_done=False,
            )

    network = session.get("last_scan_network", default_network)
    hosts = session.get("last_scan_hosts", [])
    return render_template(
        "index.html",
        network=network,
        hosts=hosts,
        scan_done=bool(hosts),
    )


@app.route("/shutdown", methods=["POST"])
def shutdown():
    hosts = session.get("last_scan_hosts", [])
    if not hosts:
        flash("Please run a scan before attempting shutdown.", "warning")
        return redirect(url_for("index"))

    ip = request.form.get("ip")
    os_type = request.form.get("os_type", "windows")
    username = request.form.get("username", "").strip()
    key_path = request.form.get("key_path", "").strip()

    host = next((h for h in hosts if h["ip"] == ip), None)
    if not host:
        flash("The selected device is not in the last scan results.", "danger")
        return redirect(url_for("index"))

    if "Mobile" in host["type"]:
        flash("Shutdown is not supported for mobile/IoT devices.", "warning")
        return redirect(url_for("index"))

    if os_type == "windows":
        success, message = shutdown_device(ip, windows=True)
    else:
        if not username or not key_path:
            flash("SSH username and private key path are required for Linux/macOS shutdown.", "danger")
            return redirect(url_for("index"))
        success, message = shutdown_device(
            ip,
            windows=False,
            username=username,
            key_path=key_path,
        )

    flash(message, "success" if success else "danger")
    return redirect(url_for("index"))


@app.route("/export-csv")
def export_csv():
    hosts = session.get("last_scan_hosts", [])
    network = session.get("last_scan_network", "scan")
    if not hosts:
        flash("Please run a scan before exporting results.", "warning")
        return redirect(url_for("index"))

    csv_lines = ["IP,Hostname,MAC,Type"]
    for host in hosts:
        csv_lines.append(
            f'{host["ip"]},{host["hostname"]},{host["mac"]},{host["type"]}'
        )
    response = make_response("\n".join(csv_lines))
    response.headers["Content-Type"] = "text/csv; charset=utf-8"
    response.headers["Content-Disposition"] = f"attachment; filename=scan_{network}.csv"
    return response


if __name__ == "__main__":
    app.run(debug=True, host="127.0.0.1", port=5000)
