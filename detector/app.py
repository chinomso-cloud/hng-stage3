from flask import Flask, render_template_string
import subprocess
import os

START_TIME = time.time()

def get_sys_stats():
    return {
        "cpu": psutil.cpu_percent(),
        "ram": psutil.virtual_memory().percent,
        "uptime": str(datetime.timedelta(seconds=int(time.time() - START_TIME)))
    }

app = Flask(__name__)

def get_active_bans():
    """Fetch current blocked IPs from iptables."""
    try:
        # Runs the system command to list firewall rules
        output = subprocess.check_output(["sudo", "iptables", "-L", "-n"], text=True)
        # Filters for the 'DROP' (banned) lines
        bans = [line.split()[3] for line in output.splitlines() if "DROP" in line]
        return bans
    except Exception as e:
        return [f"Error fetching bans: {e}"]

@app.route('/')
def dashboard():
    # Read the audit log for history
    history = []
    if os.path.exists("audit.log"):
        with open("audit.log", "r") as f:
            history = f.readlines()[::-1] # Show newest incidents at the top

    active_bans = get_active_bans()

    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>HNG Shield Dashboard</title>
        <meta http-equiv="refresh" content="10"> <style>
            body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #0d1117; color: #c9d1d9; padding: 40px; }
            .container { max-width: 900px; margin: auto; }
            .card { background: #161b22; padding: 25px; border-radius: 12px; border: 1px solid #30363d; margin-bottom: 25px; box-shadow: 0 4px 10px rgba(0,0,0,0.3); }
            h1 { color: #58a6ff; border-bottom: 1px solid #30363d; padding-bottom: 10px; }
            h2 { color: #ff7b72; margin-top: 0; }
            .ban-list { list-style: none; padding: 0; font-family: 'Courier New', Courier, monospace; }
            .ban-item { background: #21262d; padding: 10px; margin: 5px 0; border-radius: 6px; border-left: 4px solid #f85149; }
            .log-box { font-size: 0.85em; white-space: pre-wrap; background: #010409; padding: 15px; border-radius: 6px; border: 1px solid #30363d; max-height: 300px; overflow-y: auto; color: #8b949e; }
            .status-ok { color: #3fb950; font-weight: bold; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🛡️ HNG Security Shield</h1>
            <p>System Status: <span class="status-ok">MONITORING ACTIVE</span></p>
            
            <div class="card">
                <h2>🚫 Current Active Bans</h2>
                <ul class="ban-list">
                    {% for ip in active_bans %}
                        <li class="ban-item">IP Address: {{ ip }}</li>
                    {% else %}
                        <li style="color: #8b949e;">No active threats detected.</li>
                    {% endfor %}
                </ul>
            </div>

            <div class="card">
                <h2>📄 Security Audit Log</h2>
                <div class="log-box">
                    {% for line in history %}
                        <div>{{ line }}</div>
                    {% else %}
                        <div>No incidents recorded yet.</div>
                    {% endfor %}
                </div>
            </div>
        </div>
    </body>
    </html>
    """
    return render_template_string(html, active_bans=active_bans, history=history)

if __name__ == '__main__':
    # Running on port 8080
    app.run(host='0.0.0.0', port=8080)
