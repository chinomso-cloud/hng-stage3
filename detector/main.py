import json
import time
import threading
import subprocess
import os
from collections import deque
import statistics
from notifier import send_slack_alert

# --- CONFIGURATION ---
LOG_PATH = "/var/lib/docker/volumes/hng-stage3_HNG-nginx-logs/_data/hng-access.log"
AUDIT_LOG = "audit.log"
BAN_HISTORY_FILE = "ban_history.json"

class HNGShield:
    def __init__(self):
        # Sliding Windows (60s)
        self.global_window = deque()
        self.ip_windows = {}  
        self.error_windows = {} 
        
        # Rolling Baseline (Initial state)
        self.history = deque(maxlen=1800)
        self.hourly_baselines = {h: {"mean": 1.0, "std": 0.5} for h in range(24)}
        self.current_sec_count = 0
        
        # Ban Management
        self.active_bans = {} 
        self.ban_counts = self.load_ban_history()

    def load_ban_history(self):
        if os.path.exists(BAN_HISTORY_FILE):
            with open(BAN_HISTORY_FILE, 'r') as f: return json.load(f)
        return {}

    def save_ban_history(self):
        with open(BAN_HISTORY_FILE, 'w') as f: json.dump(self.ban_counts, f)

    def write_audit(self, action, ip, condition, rate, baseline, duration):
        timestamp = time.strftime("[%Y-%m-%d %H:%M:%S]")
        entry = f"{timestamp} {action} {ip} | {condition} | {rate} req/s | {baseline:.2f} | {duration}\n"
        with open(AUDIT_LOG, "a") as f: f.write(entry)

    def add_request(self, ip, status):
        now = time.time()
        self.global_window.append(now)
        self.current_sec_count += 1
        
        if ip not in self.ip_windows: self.ip_windows[ip] = deque()
        self.ip_windows[ip].append(now)

        if str(status).startswith(('4', '5')):
            if ip not in self.error_windows: self.error_windows[ip] = deque()
            self.error_windows[ip].append(now)

    def update_baseline(self):
        """Called every 60s to rotate the rolling window."""
        self.history.append(self.current_sec_count)
        print(f"📊 Minute Sync: {self.current_sec_count} reqs in last 60s")
        self.current_sec_count = 0
        
        # Recalculate mean/std every 60s once we have enough data
        if len(self.history) >= 60:
            h = time.localtime().tm_hour
            m = statistics.mean(self.history)
            s = statistics.stdev(self.history) if len(self.history) > 1 else 0.5
            self.hourly_baselines[h] = {"mean": max(m, 1.0), "std": max(s, 0.5)}
            print(f"📈 Baseline Recalculated for Hour {h}: Mean {m:.2f}")

    def trigger_ban(self, ip, z_score, rate):
        if ip in self.active_bans: return
        count = self.ban_counts.get(ip, 0) + 1
        self.ban_counts[ip] = count
        self.save_ban_history()
        
        durations = {1: 600, 2: 1800, 3: 7200}
        sec = durations.get(count, 31536000) 
        label = f"{sec//60}m" if sec < 31536000 else "PERMANENT"

        subprocess.run(["sudo", "iptables", "-A", "INPUT", "-s", ip, "-j", "DROP"])
        self.active_bans[ip] = time.time() + sec
        
        h_stats = self.hourly_baselines[time.localtime().tm_hour]
        self.write_audit("BAN", ip, f"Z-Score {z_score:.2f}", rate, h_stats['mean'], label)
        send_slack_alert(ip, z_score, rate, "BANNED", label, h_stats['mean'])

    def unbanner_check(self):
        while True:
            now = time.time()
            to_unban = [ip for ip, expiry in self.active_bans.items() if now >= expiry]
            for ip in to_unban:
                subprocess.run(["sudo", "iptables", "-D", "INPUT", "-s", ip, "-j", "DROP"])
                del self.active_bans[ip]
                self.write_audit("UNBAN", ip, "Timer Expired", "-", 0.0, "-")
                send_slack_alert(ip, 0, 0, "UNBANNED")
            time.sleep(10)

shield = HNGShield()

def monitor():
    threading.Thread(target=shield.unbanner_check, daemon=True).start()
    
    def recalc_timer():
        while True:
            time.sleep(60)
            shield.update_baseline()
    threading.Thread(target=recalc_timer, daemon=True).start()

    while True:
        try:
            with open(LOG_PATH, 'r') as f:
                f.seek(0, 2)
                while True:
                    line = f.readline()
                    if not line:
                        time.sleep(0.1); continue
                    
                    data = json.loads(line)
                    ip, status = data.get('source_ip'), data.get('status')
                    shield.add_request(ip, status)
                    
                    now = time.time()
                    cutoff = now - 60
                    
                    if ip in shield.ip_windows:
                        while shield.ip_windows[ip] and shield.ip_windows[ip][0] < cutoff:
                            shield.ip_windows[ip].popleft()
                        
                        rate = len(shield.ip_windows[ip])
                        h_stats = shield.hourly_baselines[time.localtime().tm_hour]
                        z = (rate - h_stats['mean']) / h_stats['std']
                        
                        if z > 3.0 or rate > (h_stats['mean'] * 5):
                            shield.trigger_ban(ip, z, rate)
                    
                    while shield.global_window and shield.global_window[0] < cutoff:
                        shield.global_window.popleft()
                    
                    if len(shield.global_window) > (h_stats['mean'] * 10):
                        send_slack_alert(None, 0, len(shield.global_window), "GLOBAL SPIKE", baseline=h_stats['mean'])

        except Exception as e:
            print(f"Error: {e}"); time.sleep(1)

if __name__ == "__main__":
    monitor()
