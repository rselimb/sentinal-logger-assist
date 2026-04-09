# Sentinel-V Quick Start Guide

## 🚀 30-Second Setup

### Windows Users
```batch
setup.bat
```

### Linux/macOS Users
```bash
chmod +x setup.sh
./setup.sh
```

## 🐳 Docker Quick Start (Recommended)

```bash
# 1. Clone/download the project
cd sentinel-v

# 2. Configure (optional - Discord webhook)
cp .env.example .env
nano .env

# 3. Start with Docker
docker-compose up -d

# 4. Access dashboard
open http://localhost:5000
```

## 📊 Testing the System

### Generate Fake SSH Brute-Force Attacks
```bash
# Log in to the server
ssh user@target

# Try logging in with wrong password 5 times
# The 5th attempt will trigger a block
```

### Test WAF Detection
```bash
# SQL Injection
curl "http://localhost/search?q=UNION%20SELECT%201,2,3"

# XSS
curl "http://localhost/search?q=%3Cscript%3Ealert(1)%3C/script%3E"

# Path Traversal
curl "http://localhost/files/../../etc/passwd"
```

### Monitor in Real-Time
```bash
# Watch logs
tail -f /var/log/auth.log

# Check iptables rules
sudo iptables -L INPUT -n | grep DROP

# View database
sqlite3 data/sentinel.db
sqlite> SELECT * FROM blocked_ips;
```

## 💻 System Requirements

| Component | Requirement |
|-----------|-------------|
| Python | 3.9+ |
| OS | Linux (CentOS, Ubuntu, Debian) |
| Memory | 512 MB minimum |
| Disk | 100 MB for database |
| Network | Internet (for GeoIP lookups) |
| Firewall | iptables support |

## 📝 Configuration Checklist

- [ ] Copy `.env.example` to `.env`
- [ ] Add Discord webhook URL (optional)
- [ ] Verify log paths exist
- [ ] Check file permissions
- [ ] Test SSH and Nginx access logs
- [ ] Verify iptables is installed
- [ ] Create data directory

## 🔍 Verify Installation

```bash
# Check Python version
python3 --version

# Test imports
python3 -c "import flask, requests, sqlite3; print('✅ All imports OK')"

# Check database
sqlite3 data/sentinel.db "SELECT COUNT(*) FROM blocked_ips;"

# Test API
curl http://localhost:5000/api/stats
```

## 🐛 Common Issues

| Issue | Solution |
|-------|----------|
| "Port 5000 already in use" | Change port in `.env`: `DASHBOARD_PORT=8080` |
| "Permission denied" when accessing logs | Add user to adm group: `sudo usermod -aG adm $USER` |
| "iptables: Protocol not available" | Install iptables: `sudo apt install iptables` |
| No threats detected | Check log file paths in `.env` |
| Discord alerts not working | Verify webhook URL format in `.env` |

## 🔧 Environment Variables

```bash
# Core
SENTINEL_DB_PATH=./data/sentinel.db

# Web
DASHBOARD_HOST=0.0.0.0
DASHBOARD_PORT=5000

# Logging
SSH_LOG_PATH=/var/log/auth.log
WEB_LOG_PATH=/var/log/nginx/access.log

# Notifications
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/...
```

## 📚 Next Steps

1. **Read the README**: Full documentation and troubleshooting
2. **Configure Discord**: Set up real-time alerts
3. **Test the system**: Generate fake attacks to verify
4. **Deploy**: Use Docker or Systemd for production
5. **Monitor**: Check logs and dashboard regularly

## 💬 Need Help?

Check the README.md for:
- Complete feature list
- Detailed architecture
- API documentation
- Troubleshooting guide
- Performance metrics

---

**Sentinel-V** - Your Server's Digital Guardian
