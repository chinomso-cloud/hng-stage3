import requests
import json

SLACK_WEBHOOK_URL = "https://hooks.slack.com/services/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"

def send_slack_alert(ip, z_score, rate, action="BANNED", duration="10 Minutes", baseline=0.0):
    """
    Unified notifier for Ban, Unban, and Global Spikes.
    """
    if action == "BANNED":
        header = "🚨 *HNG SECURITY ALERT: IP BANNED* 🚨"
        color = "#ff0000" # Red
    elif action == "UNBANNED":
        header = "✅ *HNG SECURITY ALERT: ACCESS RESTORED* ✅"
        color = "#00ff00" # Green
    else: # GLOBAL SPIKE
        header = "⚠️ *HNG SECURITY ALERT: GLOBAL TRAFFIC SPIKE* ⚠️"
        color = "#ffff00" # Yellow

    body = f"*Event:* {action}\n"
    if ip:
        body += f"*Source IP:* `{ip}`\n"
    
    body += (
        f"*Z-Score:* `{z_score:.2f}`\n"
        f"*Current Rate:* `{rate} req/s`\n"
        f"*Baseline Mean:* `{baseline:.2f}`\n"
    )
    
    if action == "BANNED":
        body += f"*Ban Duration:* `{duration}`"

    payload = {"text": f"{header}\n{body}"}
    
    try:
        response = requests.post(
            SLACK_WEBHOOK_URL, 
            data=json.dumps(payload),
            headers={'Content-Type': 'application/json'},
            timeout=5
        )
        return response.status_code == 200
    except Exception as e:
        print(f"Slack Error: {e}")
        return False
