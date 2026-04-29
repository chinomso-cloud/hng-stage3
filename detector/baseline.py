from collections import deque
import statistics
import time

class TrafficEngine:
    def __init__(self):
        self.global_window = deque()
        self.ip_windows = {}  

        # Rolling Baseline: Total requests per second for 30 mins
        self.history = deque(maxlen=1800)
        
        # NEW: Hourly Slots requirement
        # Stores the effective mean for each of the 24 hours
        self.hourly_baselines = {hour: {"mean": 1.0, "std": 0.1} for hour in range(24)}
        
        self.current_second_count = 0
        self.last_recalc = time.time()

    def add_request(self, ip, status_code):
        now = time.time()
        self.global_window.append(now)

        if ip not in self.ip_windows:
            self.ip_windows[ip] = deque()
        self.ip_windows[ip].append(now)

        self.current_second_count += 1
        # Logic for "Error Surge" (Status code check) can go here later

    def update_baseline(self):
        """Called every 60 seconds (as per HNG reqs) to recalculate the mean/std."""
        if len(self.history) < 60: return
        
        current_hour = time.localtime().tm_hour
        mean = statistics.mean(self.history)
        std = statistics.stdev(self.history) if len(self.history) > 1 else 0.1
        
        # Update the specific slot for this hour
        self.hourly_baselines[current_hour] = {
            "mean": max(mean, 1.0), # Ensure a floor value
            "std": max(std, 0.1)
        }
        print(f"📈 Baseline Recalculated for Hour {current_hour}: Mean {mean:.2f}")

    def get_z_score(self, current_rate):
        hour = time.localtime().tm_hour
        stats = self.hourly_baselines[hour]
        if stats["std"] == 0: return 0
        return (current_rate - stats["mean"]) / stats["std"]

    def clean_windows(self):
        """Keeps windows at exactly 60 seconds."""
        now = time.time()
        cutoff = now - 60
        while self.global_window and self.global_window[0] < cutoff:
            self.global_window.popleft()
        # ... (keep your existing IP window cleanup logic here)
