# 🛡️ Sentinel-V: Quick Navigation Guide

Welcome to **Sentinel-V** - Enterprise Server Security & Monitoring Suite!

## 🚀 Getting Started (Choose Your Path)

### I'm in a hurry! ⏱️
→ Start here: [QUICKSTART.md](QUICKSTART.md) (5 minutes)

### I want to understand the system first 📚
→ Read this: [README.md](README.md) - Complete feature list and API documentation

### I'm deploying on Docker 🐳
→ Follow this: [DOCKER_GUIDE.md](DOCKER_GUIDE.md) - Container setup and scaling

### I'm deploying on Linux (systemd) 🐧
→ Follow this: [SYSTEMD_GUIDE.md](SYSTEMD_GUIDE.md) - Native service installation

### I need to validate the installation 🧪
→ Run these tests: [TESTING_GUIDE.md](TESTING_GUIDE.md) - Comprehensive test suites

### I'm deploying in enterprise 🏢
→ Use this: [DEPLOYMENT_CHECKLIST.md](DEPLOYMENT_CHECKLIST.md) - Production readiness checklist

### I want to understand the architecture 🏗️
→ See this: [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md) - Complete system overview

---

## 📁 Project Files at a Glance

### 🔧 Application Code (2,400+ lines)

**Core Modules:**
- `main.py` - System orchestrator and thread manager
- `database.py` - Thread-safe SQLite3 threat database
- `monitors.py` - SSH, Web, and File Integrity monitoring
- `actions.py` - IP blocking and Discord notifications
- `dashboard.py` - Flask REST API and web UI

**Configuration:**
- `requirements.txt` - Python dependencies (13 packages)
- `.env.example` - Environment variable template
- `.gitignore` - Git ignore patterns

### 🐳 Infrastructure & Deployment

**Containerization:**
- `Dockerfile` - Docker image (Python 3.11 slim)
- `docker-compose.yml` - Multi-container orchestration

**Linux Service:**
- `sentinel-v.service` - Systemd service template

**Setup Scripts:**
- `setup.sh` - Linux/macOS automated setup
- `setup.bat` - Windows automated setup

### 📚 Documentation (8,000+ lines)

| Document | Purpose | Read Time |
|----------|---------|-----------|
| [README.md](README.md) | Complete documentation | 20 mins |
| [QUICKSTART.md](QUICKSTART.md) | 30-second setup | 5 mins |
| [DOCKER_GUIDE.md](DOCKER_GUIDE.md) | Docker deployment | 15 mins |
| [SYSTEMD_GUIDE.md](SYSTEMD_GUIDE.md) | Linux service setup | 15 mins |
| [TESTING_GUIDE.md](TESTING_GUIDE.md) | Validation tests | 10 mins |
| [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md) | Architecture overview | 10 mins |
| [DEPLOYMENT_CHECKLIST.md](DEPLOYMENT_CHECKLIST.md) | Production readiness | 20 mins |

---

## 🎯 Common Tasks

### Setup
```bash
# Option 1: Quick setup (recommended)
bash setup.sh          # Linux/macOS
setup.bat              # Windows

# Option 2: Manual Docker
docker-compose up -d

# Option 3: Systemd service
sudo systemctl start sentinel-v
```

### Access Dashboard
```
http://localhost:5000
```

### Check Status
```bash
# Docker
docker-compose logs -f sentinel-v

# Systemd
sudo systemctl status sentinel-v

# Direct
python3 main.py
```

### Test Installation
```bash
# Quick validation
curl http://localhost:5000/api/stats

# Full test suite
bash tests/test_all.sh
```

### Deploy to Production
1. Read [DEPLOYMENT_CHECKLIST.md](DEPLOYMENT_CHECKLIST.md)
2. Follow [SYSTEMD_GUIDE.md](SYSTEMD_GUIDE.md) or [DOCKER_GUIDE.md](DOCKER_GUIDE.md)
3. Run validation from [TESTING_GUIDE.md](TESTING_GUIDE.md)

---

## 💡 Key Features

✅ **SSH Brute-Force Detection** - Blocks IPs after 5 failed attempts
✅ **Web Application Firewall** - Detects SQL Injection, XSS, Path Traversal
✅ **File Integrity Monitoring** - Watches critical system files
✅ **GeoIP Tracking** - Shows attacker locations on map
✅ **Real-Time Dashboard** - Interactive Leaflet.js map + Bootstrap tables
✅ **REST API** - Complete JSON API for integrations
✅ **Discord Alerts** - Instant notifications for new threats
✅ **Docker Ready** - Production-grade containerization
✅ **Linux Service** - Native systemd integration

---

## 🔐 Security Features

| Feature | Detection | Action |
|---------|-----------|--------|
| SSH Brute-Force | Failed login attempts | Immediate IP block |
| SQL Injection | UNION SELECT patterns | Immediate IP block |
| Cross-Site Scripting | `<script>` patterns | Immediate IP block |
| Path Traversal | `../` patterns | Immediate IP block |
| File Tampering | SHA-256 hash changes | Alert + logging |

---

## 📊 Architecture at a Glance

```
┌─────────────────────────────────────┐
│    Web Dashboard (Port 5000)        │
│  ├─ Interactive Leaflet.js Map      │
│  ├─ Bootstrap Theme Tables          │
│  └─ REST API Endpoints              │
└────────────┬────────────────────────┘
             │
    ┌────────┴────────┐
    │                 │
    ▼                 ▼
┌──────────┐   ┌────────────────┐
│ Monitors │   │ SQLite Database│
├─ SSH     │   ├─ Blocked IPs   │
├─ Web     │   ├─ GeoIP Data    │
└─ Files   │   └─ Attack Log    │
           │                    │
    ┌──────┴────────────────────┐
    │                           │
    ▼                           ▼
┌──────────┐           ┌────────────┐
│ Actions  │           │ External   │
├─ Block   │           ├─ ip-api.com│
├─ Alert   │           └─ Discord   │
└──────────┘                        │
                           └────────┘
```

---

## ⚡ Quick Reference

### Installation Time
- **Windows Setup**: ~5 minutes
- **Linux Setup**: ~10 minutes  
- **Docker Setup**: ~15 minutes
- **Systemd Production**: ~30 minutes

### Space Requirements
- **Source Code**: ~500 KB
- **Python Environment**: ~200 MB
- **Database (empty)**: ~100 KB
- **Database (1000 IPs)**: ~5 MB
- **Total**: ~200 MB

### System Requirements
- **OS**: Linux (Ubuntu 20.04+, Debian 10+, CentOS 7+)
- **Python**: 3.9+
- **RAM**: 512 MB minimum
- **CPU**: 1 core minimum
- **Disk**: 500 MB minimum
- **Network**: Internet access for GeoIP

---

## 🎓 Learning Paths

### For Administrators
1. [QUICKSTART.md](QUICKSTART.md) - Initial setup
2. [README.md](README.md) - Features overview
3. [SYSTEMD_GUIDE.md](SYSTEMD_GUIDE.md) - Production deployment
4. [DEPLOYMENT_CHECKLIST.md](DEPLOYMENT_CHECKLIST.md) - Go-live readiness

### For DevOps Engineers
1. [QUICKSTART.md](QUICKSTART.md) - Quick overview
2. [DOCKER_GUIDE.md](DOCKER_GUIDE.md) - Container deployment
3. [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md) - Architecture details
4. [TESTING_GUIDE.md](TESTING_GUIDE.md) - Validation procedures

### For Developers
1. [README.md](README.md) - Feature list
2. [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md) - Code architecture
3. Application code - Review `main.py`, `database.py`, `monitors.py`
4. Dashboard code - Review `dashboard.py`

### For Security Teams
1. [README.md](README.md#-security-features-in-detail) - Security details
2. [TESTING_GUIDE.md](TESTING_GUIDE.md) - Security testing
3. [DEPLOYMENT_CHECKLIST.md](DEPLOYMENT_CHECKLIST.md#-security-hardening) - Hardening guide

---

## 🚨 Important Notes

### Before You Start
- ⚠️ Requires root or sudo access
- ⚠️ Will manage iptables firewall rules
- ⚠️ Reads system log files
- ⚠️ Requires network access to ip-api.com (unless disabled)

### Python Version
- ✅ Python 3.9+
- ✅ Python 3.10, 3.11 recommended
- ❌ Python 2.x not supported
- ❌ Python 3.8 or older not supported

### Linux Distributions
- ✅ Ubuntu 20.04 LTS and later
- ✅ Debian 10 and later  
- ✅ CentOS 7 and later
- ✅ RHEL 8 and later
- ✅ Fedora 34 and later
- ❓ Others may work but not tested

---

## 🆘 Help & Support

### Documentation
- **Full docs**: [README.md](README.md)
- **Setup**: [QUICKSTART.md](QUICKSTART.md)
- **Troubleshooting**: [README.md](README.md#troubleshooting)
- **Architecture**: [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md)

### Deployment Help
- **Docker**: [DOCKER_GUIDE.md](DOCKER_GUIDE.md)
- **Linux Service**: [SYSTEMD_GUIDE.md](SYSTEMD_GUIDE.md)
- **Production**: [DEPLOYMENT_CHECKLIST.md](DEPLOYMENT_CHECKLIST.md)

### Testing & Validation
- **Full test suite**: [TESTING_GUIDE.md](TESTING_GUIDE.md)
- **Manual testing**: TESTING_GUIDE.md (Section 3-9)
- **Integration tests**: TESTING_GUIDE.md (Section 7)

### Common Issues
See [README.md#troubleshooting](README.md#troubleshooting) section

---

## 📞 Contact & Support

For issues, questions, or contributions:
- GitHub Issues: [your-repo/issues](https://github.com/)
- Documentation: Check README.md first
- Guides: Use QUICKSTART.md for setup help

---

## 📈 What's Included

✅ **2,400+ lines** of production-ready Python code
✅ **8,000+ lines** of comprehensive documentation
✅ **5 deployment guides** (Quick Start, Docker, Systemd, Testing, Checklist)
✅ **Complete REST API** with JSON endpoints
✅ **Interactive Dashboard** with Leaflet.js & Bootstrap 5
✅ **SQLite3 database** with 4 tables for threat tracking
✅ **3 monitoring modules** (SSH, Web, File Integrity)
✅ **Thread-safe design** for concurrent threat handling
✅ **Docker support** with proper capabilities
✅ **Systemd integration** for Linux services
✅ **Security hardening** best practices
✅ **Comprehensive testing** guides

---

## 🎉 You're Ready!

**Choose a path above and get started in minutes!**

- 🏃 **In a hurry?** → [QUICKSTART.md](QUICKSTART.md)
- 🔍 **Want details?** → [README.md](README.md)
- 🐳 **Using Docker?** → [DOCKER_GUIDE.md](DOCKER_GUIDE.md)
- 🐧 **Using Linux?** → [SYSTEMD_GUIDE.md](SYSTEMD_GUIDE.md)

---

**Sentinel-V** - Your Server's Digital Guardian 🛡️

*Version 1.0 - Production Ready*
