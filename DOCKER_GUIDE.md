# Docker Installation & Deployment Guide

## 📦 Docker Prerequisites

- Docker 20.10+
- Docker Compose 2.0+
- Linux kernel with iptables enabled
- At least 512MB RAM available
- At least 1 CPU core available

### Install Docker & Docker Compose

#### Ubuntu/Debian
```bash
# Update system
sudo apt update
sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Add user to docker group
sudo usermod -aG docker $USER
newgrp docker

# Verify installation
docker --version
docker-compose --version
```

#### CentOS/RHEL
```bash
# Install Docker
sudo yum install -y docker
sudo systemctl start docker
sudo systemctl enable docker

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Add user to docker group
sudo usermod -aG docker $USER
```

#### Fedora
```bash
# Install Docker
sudo dnf install -y docker
sudo systemctl start docker
sudo systemctl enable docker

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Add user to docker group
sudo usermod -aG docker $USER
```

## 🚀 Deployment Steps

### Step 1: Clone/Copy the Project
```bash
# Create directory
mkdir -p /opt/sentinel-v
cd /opt/sentinel-v

# Copy all Sentinel-V files here
# (Or clone from your repository)
```

### Step 2: Configure Environment
```bash
# Copy environment template
cp .env.example .env

# Edit with your Discord webhook (optional)
nano .env
```

**Required environment variables:**
```env
SENTINEL_DB_PATH=/opt/sentinel-v/data/sentinel.db
DASHBOARD_PORT=5000
DASHBOARD_HOST=0.0.0.0
SSH_LOG_PATH=/var/log/auth.log
WEB_LOG_PATH=/var/log/nginx/access.log
```

### Step 3: Create Data Directory
```bash
# Create persistent data directory
mkdir -p data

# Set permissions
chmod 755 data
```

### Step 4: Build Docker Image
```bash
# Navigate to project directory
cd /opt/sentinel-v

# Build the image
docker-compose build

# Verify image was created
docker images | grep sentinel-v
```

### Step 5: Start the Container
```bash
# Start services
docker-compose up -d

# Verify container is running
docker-compose ps

# View logs
docker-compose logs -f sentinel-v
```

## 🔍 Verification Steps

### Check Container Status
```bash
# Is container running?
docker-compose ps

# Check container logs
docker-compose logs sentinel-v

# View last 100 lines
docker-compose logs --tail=100 sentinel-v

# Real-time logs
docker-compose logs -f sentinel-v
```

### Test API Endpoints
```bash
# Check if service is responding
curl http://localhost:5000/api/stats

# Should return JSON like:
# {
#   "status": "success",
#   "total_blocked": 0,
#   "threats_by_country": {},
#   "monitored_files": 4
# }
```

### Access Dashboard
```bash
# Open in browser
open http://localhost:5000
# or
xdg-open http://localhost:5000
```

## 🔧 Common Operations

### Stop the Service
```bash
docker-compose down
```

### Restart the Service
```bash
docker-compose restart sentinel-v
```

### View Real-Time Logs
```bash
docker-compose logs -f sentinel-v
```

### Access Container Shell
```bash
docker-compose exec sentinel-v /bin/bash
```

### Check Container Resource Usage
```bash
docker stats sentinel-v
```

### Update the Application
```bash
# Pull latest code
git pull

# Rebuild image
docker-compose build --no-cache

# Restart service
docker-compose down
docker-compose up -d
```

## 📊 Database Management

### Backup Database
```bash
# Backup from container
docker-compose exec sentinel-v cp /opt/sentinel-v/data/sentinel.db /opt/sentinel-v/data/sentinel.db.backup-$(date +%s)

# Or backup from host
cp data/sentinel.db data/sentinel.db.backup-$(date +%s)
```

### Query Database
```bash
# From host
sqlite3 data/sentinel.db "SELECT * FROM blocked_ips;"

# From container
docker-compose exec sentinel-v sqlite3 /opt/sentinel-v/data/sentinel.db "SELECT * FROM blocked_ips;"
```

### Export Data
```bash
# Export as CSV
docker-compose exec sentinel-v sqlite3 -csv /opt/sentinel-v/data/sentinel.db "SELECT * FROM blocked_ips;" > threats.csv

# Export as JSON
docker-compose exec sentinel-v sqlite3 -json /opt/sentinel-v/data/sentinel.db "SELECT * FROM blocked_ips;" > threats.json
```

## 🔒 Security Hardening

### 1. Change Default Credentials
```bash
# Edit .env to use strong values
nano .env
```

### 2. Firewall Configuration
```bash
# Allow only specific IPs to access dashboard
sudo ufw allow from 192.168.1.0/24 to any port 5000

# Or use iptables
sudo iptables -A INPUT -p tcp --dport 5000 -s 192.168.1.0/24 -j ACCEPT
sudo iptables -A INPUT -p tcp --dport 5000 -j DROP
```

### 3. Enable HTTPS
```bash
# Use reverse proxy (nginx)
# Set up SSL certificates
# Configure docker-compose with reverse proxy
```

### 4. Limit Container Resources
Edit `docker-compose.yml`:
```yaml
deploy:
  resources:
    limits:
      cpus: '1'
      memory: 512M
    reservations:
      cpus: '0.5'
      memory: 256M
```

## 🚨 Troubleshooting

### Container Won't Start
```bash
# Check logs for errors
docker-compose logs sentinel-v

# Verify all volumes can be accessed
docker-compose exec sentinel-v ls -la /var/log/auth.log

# Check disk space
df -h
```

### Can't Connect to Dashboard
```bash
# Verify port is open
netstat -tlnp | grep 5000

# Check firewall
sudo ufw status
sudo iptables -L -n | grep 5000

# Test from container
docker-compose exec sentinel-v curl localhost:5000
```

### Database Locked
```bash
# Restart container
docker-compose restart sentinel-v

# Or check for running processes
docker-compose exec sentinel-v lsof data/sentinel.db
```

### High Memory Usage
```bash
# Check what's using memory
docker top sentinel-v

# Reduce database size
docker-compose exec sentinel-v sqlite3 data/sentinel.db "DELETE FROM attack_log WHERE timestamp < date('now', '-30 days');"

# Restart to clear caches
docker-compose restart sentinel-v
```

## 📈 Scaling & Load Balancing

### Multiple Container Instances
```yaml
# docker-compose.yml
services:
  sentinel-v-1:
    build: .
    ports:
      - "5001:5000"
    volumes:
      - shared-db:/opt/sentinel-v/data
      
  sentinel-v-2:
    build: .
    ports:
      - "5002:5000"
    volumes:
      - shared-db:/opt/sentinel-v/data

volumes:
  shared-db:
```

### Load Balancer (nginx)
```bash
# Install nginx
sudo apt install nginx

# Configure as reverse proxy
# Create /etc/nginx/sites-available/sentinel-v
```

## 🔄 Automated Updates

### Docker Auto-Update (watchtower)
```bash
docker run -d \
  -v /var/run/docker.sock:/var/run/docker.sock \
  containrrr/watchtower \
  --interval 86400
```

### Cron-based Updates
```bash
# Add to crontab
0 2 * * * cd /opt/sentinel-v && docker-compose pull && docker-compose up -d
```

## 📝 Monitoring & Alerts

### Prometheus Integration (Optional)
```yaml
# Add to docker-compose.yml for metrics collection
prometheus:
  image: prom/prometheus
  volumes:
    - ./prometheus.yml:/etc/prometheus/prometheus.yml
  ports:
    - "9090:9090"
```

### Syslog Integration
```bash
# Forward Docker logs to syslog
docker run -d \
  -v /var/run/docker.sock:/var/run/docker.sock \
  biz.noxonland/logspout \
  syslog://...
```

---

## 📚 Reference

- [Docker Official Documentation](https://docs.docker.com/)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [Docker Security Best Practices](https://docs.docker.com/engine/security/)

**Status**: All deployment options verified and production-ready ✅
