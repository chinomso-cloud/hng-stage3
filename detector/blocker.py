import subprocess
import time

def ban_ip(ip, audit_file):
    """Adds a DROP rule to iptables and logs the action."""
    print(f"🛑 BANNING IP: {ip}")
    try:
        # Prevent duplicate rules
        check = subprocess.run(["sudo", "iptables", "-C", "INPUT", "-s", ip, "-j", "DROP"], capture_output=True)
        if check.returncode == 0:
            return # Already banned

        subprocess.run(["sudo", "iptables", "-A", "INPUT", "-s", ip, "-j", "DROP"], check=True)
        
        with open(audit_file, "a") as f:
            f.write(f"{time.ctime()}: BANNED {ip} due to threshold breach.\n")
            
    except Exception as e:
        print(f"Error executing ban: {e}")

def unban_ip(ip):
    """Removes the DROP rule."""
    print(f"🔓 UNBANNING IP: {ip}")
    subprocess.run(["sudo", "iptables", "-D", "INPUT", "-s", ip, "-j", "DROP"])
