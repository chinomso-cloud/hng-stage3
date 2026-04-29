import json
import time
import os

def get_log_stream(log_path):
    print(f"👀 Opening log file at: {log_path}")
    if not os.path.exists(log_path):
        print("❌ ERROR: Log file does not exist at this path!")
        return

    with open(log_path, 'r') as f:
        # Move to the end, but let's back up slightly (1000 bytes) 
        # to ensure we catch the most recent activity
        f.seek(0, os.SEEK_END)
        
        while True:
            line = f.readline()
            if not line:
                time.sleep(0.1)
                continue
            
            # This is the "Pulse" to prove the script is reading
            print(f"📖 Log Line Detected!")
            try:
                yield json.loads(line)
            except json.JSONDecodeError:
                continue
