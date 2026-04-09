# Systemd Service Installation Guide

## 📋 Overview

This guide covers installing Sentinel-V as a native Linux systemd service for production deployments.

## ✅ Prerequisites

- Ubuntu 18.04+, Debian 10+, CentOS 7+, or RHEL 8+
- Python 3.9+
- systemd (standard on modern Linux distributions)
- sudo or root access
- At least 500MB disk space
- Read access to `/var/log/auth.log`

## 🚀 Installation Steps

### Step 1: Prepare the System

```bash
# Create service directory
sudo mkdir -p /opt/sentinel-v
cd /opt/sentinel-v

# Create service user (without login shell)
sudo useradd -r -s /bin/false sentinel 2>/dev/null || true

# Copy project files
sudo cp -r /path/to/sentinel-v/* .

# Set ownership
sudo chown -R sentinel:sentinel /opt/sentinel-v
```

### Step 2: Install Python and Dependencies

```bash
# Update system packages
sudo apt update && sudo apt upgrade -y  # Debian/Ubuntu
# OR
sudo yum update -y  # CentOS/RHEL

# Install Python development tools
sudo apt install -y python3 python3-venv python3-dev  # Debian/Ubuntu
# OR
sudo yum install -y python3 python3-devel  # CentOS/RHEL

# Ensure required system packages
sudo apt install -y iptables nginx openssh-server  # Debian/Ubuntu
# OR  
sudo yum install -y iptables nginx openssh-server  # CentOS/RHEL
```

### Step 3: Create Python Virtual Environment

```bash
# Create venv as service user
sudo -u sentinel python3 -m venv /opt/sentinel-v/venv

# Activate and install dependencies
cd /opt/sentinel-v
sudo /opt/sentinel-v/venv/bin/pip install --upgrade pip
sudo /opt/sentinel-v/venv/bin/pip install -r requirements.txt
```

### Step 4: Configure Environment

```bash
# Copy environment template
sudo cp .env.example /opt/sentinel-v/.env

# Edit configuration
sudo nano /opt/sentinel-v/.env

# Set correct permissions
sudo chmod 600 /opt/sentinel-v/.env
sudo chown sentinel:sentinel /opt/sentinel-v/.env
```

**Edit these variables in `.env`:**
```env
SENTINEL_DB_PATH=/opt/sentinel-v/data/sentinel.db
DASHBOARD_HOST=0.0.0.0
DASHBOARD_PORT=5000
SSH_LOG_PATH=/var/log/auth.log
WEB_LOG_PATH=/var/log/nginx/access.log
```

### Step 5: Create Data Directory

```bash
# Create data directory
sudo mkdir -p /opt/sentinel-v/data

# Set permissions (service user only)
sudo chown sentinel:sentinel /opt/sentinel-v/data
sudo chmod 750 /opt/sentinel-v/data
```

### Step 6: Install Systemd Service

```bash
# Copy service file and edit as needed
sudo cp /opt/sentinel-v/sentinel-v.service /etc/systemd/system/

# Edit if paths differ
sudo nano /etc/systemd/system/sentinel-v.service

# Reload systemd configuration
sudo systemctl daemon-reload
```

### Step 7: Set Service Permissions

```bash
# Allow sentinel user to run iptables commands
sudo visudo -f /etc/sudoers.d/sentinel
```

Add these lines to `/etc/sudoers.d/sentinel`:
```sudoers
# Allow sentinel to run iptables
sentinel ALL=(ALL) NOPASSWD: /sbin/iptables
sentinel ALL=(ALL) NOPASSWD: /sbin/ip6tables
sentinel ALL=(ALL) NOPASSWD: /usr/sbin/iptables
sentinel ALL=(ALL) NOPASSWD: /usr/sbin/ip6tables
```

Or, easier approach - use CAP_NET_ADMIN:

```bash
# Make executable require CAP_NET_ADMIN
sudo setcap cap_net_admin=+ep /opt/sentinel-v/venv/bin/python3
```

### Step 8: Enable and Start Service

```bash
# Enable service (start on boot)
sudo systemctl enable sentinel-v

# Start service
sudo systemctl start sentinel-v

# Check status
sudo systemctl status sentinel-v

# View logs
sudo journalctl -u sentinel-v -f
```

## ✅ Verification

### Check Service Status
```bash
# Is service running?
sudo systemctl status sentinel-v

# Should show:
# ● sentinel-v.service - Sentinel-V Enterprise Security System
#    Loaded: loaded (/etc/systemd/system/sentinel-v.service; enabled; vendor preset: enabled)
#    Active: active (running)
```

### View Real-Time Logs
```bash
# Follow logs
sudo journalctl -u sentinel-v -f

# View last 50 lines
sudo journalctl -u sentinel-v -n 50

# View since last boot
sudo journalctl -u sentinel-v -b
```

### Test API
```bash
# Check if dashboard is accessible
curl http://localhost:5000/api/stats

# Should return JSON with threat stats
```

### Verify iptables Access
```bash
# Check if iptables rules can be created
sudo iptables -L INPUT -n | head -5

# Check CAP_NET_ADMIN
getcap /opt/sentinel-v/venv/bin/python3
```

## 🔧 Service Management

### Start/Stop/Restart
```bash
# Start service
sudo systemctl start sentinel-v

# Stop service
sudo systemctl stop sentinel-v

# Restart service
sudo systemctl restart sentinel-v

# Reload configuration
sudo systemctl reload sentinel-v

# Check if enabled
sudo systemctl is-enabled sentinel-v

# Disable (won't start on boot)
sudo systemctl disable sentinel-v
```

### View Service Configuration
```bash
# Display service file
sudo systemctl cat sentinel-v

# Edit service file
sudo systemctl edit sentinel-v
```

## 📊 Monitoring Service

### System Monitoring
```bash
# View resource usage
ps aux | grep sentinel-v

# Check process memory
ps -o pid,vsz,rss -p $(systemctl show -p MainPID --value sentinel-v)

# Monitor in real-time
top -p $(systemctl show -p MainPID --value sentinel-v)
```

### Log Analysis
```bash
# Count errors in logs
sudo journalctl -u sentinel-v --since today | grep ERROR | wc -l

# Find specific errors
sudo journalctl -u sentinel-v | grep "SSH THREAT"

# Export logs to file
sudo journalctl -u sentinel-v -o short-iso > sentinel-v-logs.txt
```

### Database Status
```bash
# Check database size
du -h /opt/sentinel-v/data/sentinel.db

# Count blocked IPs
sqlite3 /opt/sentinel-v/data/sentinel.db "SELECT COUNT(*) FROM blocked_ips;"

# List recent threats
sqlite3 /opt/sentinel-v/data/sentinel.db "SELECT * FROM blocked_ips ORDER BY ban_timestamp DESC LIMIT 5;"
```

## 🚨 Troubleshooting

### Service Won't Start

```bash
# Check service logs for errors
sudo journalctl -u sentinel-v -n 50

# Verify Python virtual environment
/opt/sentinel-v/venv/bin/python3 --version

# Test Python imports
/opt/sentinel-v/venv/bin/python3 -c "import flask, requests, sqlite3"

# Check file permissions
ls -la /opt/sentinel-v/

# Verify data directory exists
ls -la /opt/sentinel-v/data/
```

### Dashboard Not Accessible

```bash
# Check if listening on port 5000
sudo netstat -tlnp | grep 5000

# Check firewall
sudo ufw status
sudo iptables -L -n | grep 5000

# Allow port through firewall
sudo ufw allow 5000/tcp

# Test localhost
curl -v http://localhost:5000/
```

### iptables Commands Failing

```bash
# Check service user capabilities
getcap /opt/sentinel-v/venv/bin/python3

# Set CAP_NET_ADMIN
sudo setcap cap_net_admin=+ep /opt/sentinel-v/venv/bin/python3

# Or use sudoers (less secure)
sudo visudo -f /etc/sudoers.d/sentinel
```

### Service Crashes After Start

```bash
# Check for port conflicts
sudo lsof -i :5000

# Check available memory
free -h

# Check disk space
df -h /opt/sentinel-v/

# Run in foreground to see errors
cd /opt/sentinel-v
/opt/sentinel-v/venv/bin/python3 main.py
```

### Logs Not Being Generated

```bash
# Verify log file paths
ls -la /var/log/auth.log
ls -la /var/log/nginx/access.log

# Check permissions
sudo cat /var/log/auth.log | head -5

# Add service user to relevant groups
sudo usermod -aG adm sentinel  # For auth.log access
```

## 📈 Performance Tuning

### Increase File Limits
Edit `/etc/systemd/system/sentinel-v.service.d/override.conf`:
```ini
[Service]
LimitNOFILE=65536
LimitNPROC=65536
```

### Optimize Database
```bash
# Vacuum database (reclaim space)
sqlite3 /opt/sentinel-v/data/sentinel.db VACUUM;

# Add indexes for faster queries
sqlite3 /opt/sentinel-v/data/sentinel.db "
CREATE INDEX IF NOT EXISTS idx_blocked_ips_ip ON blocked_ips(ip_address);
CREATE INDEX IF NOT EXISTS idx_attack_log_ip ON attack_log(ip_address);
"
```

### Configure Log Rotation
Create `/etc/logrotate.d/sentinel-v`:
```
/var/log/sentinel-v/*.log {
    daily
    rotate 7
    compress
    delaycompress
    missingok
    notifempty
    create 0640 sentinel sentinel
    sharedscripts
    postrotate
        systemctl reload sentinel-v > /dev/null 2>&1 || true
    endscript
}
```

## 🔐 Security Hardening

### Restrict Service User
```bash
# Lock the sentinel user account
sudo usermod -L sentinel

# Disable password login
sudo usermod -s /bin/false sentinel
```

### Firewall Rules
```bash
# Allow only local dashboard access
sudo ufw allow from 127.0.0.1 to any port 5000

# Or restrict to specific IP range
sudo ufw allow from 192.168.1.0/24 to any port 5000
```

### SELinux Policy (RHEL/CentOS)
```bash
# Check if SELinux is enabled
getenforce

# Create policy context
sudo semanage fcontext -a -t var_log_t "/opt/sentinel-v(/.*)?"
sudo restorecon -Rv /opt/sentinel-v
```

## 🔄 Updates & Maintenance

### Update Application
```bash
# Stop service
sudo systemctl stop sentinel-v

# Update files
cd /opt/sentinel-v
sudo git pull  # Or copy new version

# Reinstall dependencies
sudo /opt/sentinel-v/venv/bin/pip install -r requirements.txt --upgrade

# Start service
sudo systemctl start sentinel-v

# Verify
sudo systemctl status sentinel-v
```

### Backup Configuration
```bash
# Backup service configuration
sudo cp /opt/sentinel-v/.env /opt/sentinel-v/.env.backup-$(date +%s)
sudo cp /opt/sentinel-v/data/sentinel.db /opt/sentinel-v/data/sentinel.db.backup-$(date +%s)

# Backup systemd service file
sudo cp /etc/systemd/system/sentinel-v.service /root/sentinel-v.service.backup
```

### Restore from Backup
```bash
# Restore configuration
sudo cp /opt/sentinel-v/.env.backup-TIMESTAMP /opt/sentinel-v/.env
sudo cp /opt/sentinel-v/data/sentinel.db.backup-TIMESTAMP /opt/sentinel-v/data/sentinel.db

# Restart service
sudo systemctl restart sentinel-v
```

## 📞 Systemd Command Reference

| Command | Purpose |
|---------|---------|
| `sudo systemctl start sentinel-v` | Start the service |
| `sudo systemctl stop sentinel-v` | Stop the service |
| `sudo systemctl restart sentinel-v` | Restart the service |
| `sudo systemctl enable sentinel-v` | Enable on boot |
| `sudo systemctl disable sentinel-v` | Disable on boot |
| `sudo systemctl status sentinel-v` | Check status |
| `sudo journalctl -u sentinel-v -f` | View live logs |
| `sudo systemctl reload sentinel-v` | Reload configuration |
| `sudo systemctl is-active sentinel-v` | Check if running |
| `sudo systemctl is-enabled sentinel-v` | Check if enabled on boot |

---

**Installation Complete!** Your Sentinel-V service is ready for production use. ✅
