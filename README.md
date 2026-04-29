# 🛡️ HNG Stage 3: Anomaly Detection Engine (The Shield)

A real-time, adaptive security engine built to protect a Nextcloud instance from DDoS and brute-force attacks using Z-Score statistical analysis and automated `iptables` mitigation.

---

## 🔗 Project Links
- **Security Dashboard:** [http://34.228.22.114.sslip.io:8080](http://34.228.22.114.sslip.io:8080)
- **Beginner-Friendly Blog Post:** [https://www.linkedin.com/posts/eucharia-chinomso-622900188_activity-7455173750301392896-5nb0?utm_source=share&utm_medium=member_desktop&rcm=ACoAACxFr3oBnlPpg8CwMk0qNJp9R03Pg1Gdyt0]
- **Nextcloud Instance:** [http://34.228.22.114.sslip.io](http://34.228.22.114.sslip.io)

---

## 📖 Project Overview
This project implements a custom **Intrusion Prevention System (IPS)**. It doesn't just block traffic based on static limits; it learns the "normal" rhythm of your server and only intervenes when traffic patterns become statistically anomalous.

### Key Features
* **Real-time Log Tailing:** Monitors Nginx JSON logs across Docker volumes.
* **Sliding Window Analysis:** Analyzes traffic in a moving 60-second window using Python `deques`.
* **Adaptive Baseline:** Recalculates the Mean and Standard Deviation of traffic every 60 seconds to adapt to natural traffic growth.
* **Z-Score Detection:** Flags any IP with a Z-Score > 3.0 or a rate 5x higher than the current mean.
* **Automated Mitigation:** Instantly blocks IPs via `iptables` with an incremental backoff strategy (10m, 30m, 2h, Permanent).
* **Slack Integration:** Sends real-time Red (Ban) and Green (Unban) notifications to a security channel.

---

## 🏗️ Architecture
The system follows a decoupled architecture where the detection engine runs as a background daemon, feeding an audit log that populates the Flask dashboard.

![Architecture Diagram](docs/architecture.png)

---

## 📁 Repository Structure
```text
hng-stage3/
├── detector/
│   ├── main.py          # The Detection Engine
│   ├── app.py           # Flask Dashboard
│   ├── notifier.py      # Slack Integration logic
│   ├── audit.log        # Permanent record of security events
│   └── ban_history.json # Persistent ban count for backoff logic
├── nginx/
│   └── nginx.conf       # Configured for JSON logging
├── docs/
│   └── architecture.png # System Architecture Diagram
├── screenshots/         # 7 required evidence screenshots
└── README.md
