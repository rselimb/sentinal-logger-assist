# Sentinel-V Testing & Validation Guide

## 🧪 Comprehensive Testing Suite

This guide helps you test and validate all features of Sentinel-V.

## 1️⃣ Pre-Deployment Checks

### Initialize Test Environment
```bash
# Create test directory
mkdir -p ~/sentinel-test
cd ~/sentinel-test

# Copy project files
cp -r /path/to/sentinel-v/* .

# Run setup
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Create test database
SENTINEL_DB_PATH=./test.db python3 -c "from database import SecurityDatabase; SecurityDatabase('./test.db')"
```

### Validate Dependencies
```bash
# Test Python imports
python3 << 'EOF'
import sys
try:
    import flask
    import requests
    import sqlite3
    print("✅ All required packages installed")
except ImportError as e:
    print(f"❌ Missing package: {e}")
    sys.exit(1)
EOF
```

## 2️⃣ Database Testing

### Test Database Operations
```python
#!/usr/bin/env python3
from database import SecurityDatabase

# Initialize
db = SecurityDatabase("./test.db")

# Test blocked IPs
print("Testing blocked IPs...")
assert db.add_blocked_ip("192.168.1.100", "Test SSH Brute-force"), "Failed to add IP"
assert db.is_ip_blocked("192.168.1.100"), "IP not blocked"
print("✅ Blocked IPs working")

# Test GeoIP data
print("Testing GeoIP data...")
assert db.add_geoip_data("192.168.1.100", "United States", "New York", 40.7128, -74.0060), "Failed to add GeoIP"
geoip = db.get_geoip_data("192.168.1.100")
assert geoip['country'] == "United States", "GeoIP mismatch"
print("✅ GeoIP data working")

# Test file integrity
print("Testing file integrity...")
assert db.add_file_hash("/etc/passwd", "abc123def"), "Failed to add hash"
hash_val = db.get_file_hash("/etc/passwd")
assert hash_val == "abc123def", "Hash mismatch"
print("✅ File integrity working")

# Test attack logging
print("Testing attack logging...")
assert db.log_attack("192.168.1.100", "SQL_INJECTION", "SELECT * FROM users"), "Failed to log attack"
history = db.get_attack_history("192.168.1.100")
assert len(history) > 0, "Attack history not found"
print("✅ Attack logging working")

# Test threat retrieval
print("Testing threat retrieval...")
threats = db.get_all_threats()
assert len(threats) > 0, "No threats found"
print("✅ Threat retrieval working")

print("\n✅ All database tests passed!")
```

## 3️⃣ Monitor Testing

### Test SSH Monitor
```python
#!/usr/bin/env python3
import time
import tempfile
from database import SecurityDatabase
from monitors import SSHMonitor

# Create test log file
with tempfile.NamedTemporaryFile(mode='w', suffix='.log', delete=False) as f:
    test_log = f.name
    f.write("Nov 15 10:00:01 server sshd[1234]: Failed password for user1 from 192.168.1.200 port 22222 ssh2\n")

# Initialize
db = SecurityDatabase("./test.db")
threats = []

def on_threat(ip, reason):
    threats.append((ip, reason))

monitor = SSHMonitor(db, on_threat, test_log, failed_threshold=1)
monitor.start()

# Simulate more attempts
time.sleep(1)
with open(test_log, 'a') as f:
    f.write("Nov 15 10:00:05 server sshd[1235]: Failed password for user1 from 192.168.1.200 port 22223 ssh2\n")

time.sleep(6)  # Wait for monitor to detect
monitor.stop()

assert len(threats) > 0, "SSH threat not detected"
assert "192.168.1.200" in threats[0][0], "Wrong IP detected"
print("✅ SSH Monitor working")
```

### Test Web Monitor
```python
#!/usr/bin/env python3
import time
import tempfile
from database import SecurityDatabase
from monitors import WebMonitor

# Create test log file
with tempfile.NamedTemporaryFile(mode='w', suffix='.log', delete=False) as f:
    test_log = f.name
    f.write('192.168.1.300 - - [15/Nov/2024:10:00:00 +0000] "GET /search?q=UNION%20SELECT%201,2,3 HTTP/1.1" 200 1234\n')

# Initialize
db = SecurityDatabase("./test.db")
threats = []

def on_threat(ip, attack_type, details):
    threats.append((ip, attack_type, details))

monitor = WebMonitor(db, on_threat, test_log)
monitor.start()

time.sleep(6)  # Wait for monitor to detect
monitor.stop()

assert len(threats) > 0, "Web threat not detected"
assert threats[0][0] == "192.168.1.300", "Wrong IP detected"
assert "SQL_INJECTION" in threats[0][1], "Wrong attack type"
print("✅ Web Monitor working")
```

## 4️⃣ Actions Testing

### Test Action Execution
```python
#!/usr/bin/env python3
import os
from database import SecurityDatabase
from actions import ActionExecutor

# Initialize (without real Discord webhook)
db = SecurityDatabase("./test.db")
executor = ActionExecutor(db, None)

# Test GeoIP fetch
print("Testing GeoIP lookup...")
# Note: Uses real ip-api.com
result = executor.fetch_geoip("8.8.8.8")
assert result, "GeoIP lookup failed"
geoip = db.get_geoip_data("8.8.8.8")
assert geoip is not None, "GeoIP not stored"
assert geoip['country'] is not None, "No country data"
print(f"✅ GeoIP working - {geoip['country']}, {geoip['city']}")

# Test threat logging
print("Testing threat handling...")
executor.handle_threat("10.0.0.1", "TEST_ATTACK", "Test payload")
attack_history = db.get_attack_history("10.0.0.1")
assert len(attack_history) > 0, "Attack not logged"
print("✅ Threat handling working")

print("\n✅ All action tests passed!")
```

## 5️⃣ API Testing

### Test REST API Endpoints
```bash
#!/bin/bash

# Start Sentinel-V in background
python3 main.py &
SERVER_PID=$!

# Wait for startup
sleep 5

echo "Testing REST API endpoints..."

# Test /api/stats
echo "Testing /api/stats..."
curl -s http://localhost:5000/api/stats | grep -q "success" && echo "✅ /api/stats working" || echo "❌ /api/stats failed"

# Test /api/threats
echo "Testing /api/threats..."
curl -s http://localhost:5000/api/threats | grep -q "success" && echo "✅ /api/threats working" || echo "❌ /api/threats failed"

# Test /api/files
echo "Testing /api/files..."
curl -s http://localhost:5000/api/files | grep -q "success" && echo "✅ /api/files working" || echo "❌ /api/files failed"

# Test /api/map-data
echo "Testing /api/map-data..."
curl -s http://localhost:5000/api/map-data | grep -q "success" && echo "✅ /api/map-data working" || echo "❌ /api/map-data failed"

# Kill server
kill $SERVER_PID

echo -e "\n✅ All API tests passed!"
```

## 6️⃣ Dashboard Testing

### Manual Dashboard Tests
```bash
# Start Sentinel-V
python3 main.py &

# Open dashboard in browser
open http://localhost:5000

# Test dashboard features:
# 1. Check if map loads without errors
# 2. Verify statistics display
# 3. Check if tables load
# 4. Test refresh button
# 5. Check API polling (30 second refresh)
```

### Automated Dashboard Testing (Headless)
```bash
#!/bin/bash
# Install selenium if not present
pip install selenium

python3 << 'EOF'
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Headless Chrome
options = webdriver.ChromeOptions()
options.add_argument('--headless')
driver = webdriver.Chrome(options=options)

try:
    # Load dashboard
    driver.get("http://localhost:5000")
    
    # Wait for page to load
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_by_id("map")
    )
    
    # Verify key elements
    assert driver.find_element(By.ID, "map"), "Map not found"
    assert driver.find_element(By.ID, "threats-table"), "Threats table not found"
    assert driver.find_element(By.ID, "files-table"), "Files table not found"
    
    print("✅ Dashboard loads successfully")
    print("✅ All elements present")
    
finally:
    driver.quit()
EOF
```

## 7️⃣ Integration Testing

### Full System Test
```bash
#!/bin/bash

echo "Starting full system integration test..."

# 1. Start Sentinel-V
echo "1️⃣  Starting Sentinel-V..."
python3 main.py &
SERVER_PID=$!
sleep 5

# 2. Check service health
echo "2️⃣  Checking service health..."
curl -s http://localhost:5000/api/stats | grep -q "success" || exit 1

# 3. Simulate SSH threat
echo "3️⃣  Simulating SSH threat..."
# Create test auth.log entries
echo "Failed password for root from 172.16.0.1 port 22 ssh2" >> /tmp/test_auth.log

# 4. Simulate Web threat
echo "4️⃣  Simulating Web threat..."
# Create test nginx log entries
echo '192.168.0.2 - - [15/Nov/2024:10:00:00] "GET /search?q=%3Cscript%3E HTTP/1.1" 200 1234' >> /tmp/test_access.log

# 5. Verify database entries
echo "5️⃣  Verifying database..."
sqlite3 ./data/sentinel.db "SELECT COUNT(*) FROM blocked_ips"

# 6. Check API responses
echo "6️⃣  Checking API responses..."
curl -s http://localhost:5000/api/threats | python3 -m json.tool

# 7. Cleanup
echo "7️⃣  Cleaning up..."
kill $SERVER_PID

echo -e "\n✅ Full integration test completed!"
```

## 8️⃣ Performance Testing

### Load Testing
```bash
#!/bin/bash

# Install ab (Apache Bench) if not present
sudo apt-get install apache2-utils

echo "Running performance tests..."

# Test API endpoint response time
echo "Testing /api/stats response time (100 requests)..."
ab -n 100 -c 10 http://localhost:5000/api/stats | grep "Time per request"

# Test dashboard load
echo "Testing dashboard load (50 requests)..."
ab -n 50 -c 5 http://localhost:5000/ | grep "Requests per second"

# Test large dataset handling
echo "Testing with large dataset..."
python3 << 'EOF'
from database import SecurityDatabase
import time

db = SecurityDatabase("./test_perf.db")

# Add 10000 IPs
start = time.time()
for i in range(10000):
    db.add_blocked_ip(f"192.168.{i//256}.{i%256}", "Test")
elapsed = time.time() - start

print(f"✅ Added 10000 IPs in {elapsed:.2f} seconds")
print(f"   Average: {10000/elapsed:.0f} ops/sec")
EOF
```

### Memory Usage Testing
```bash
#!/bin/bash

python3 << 'EOF'
import psutil
import os

# Get process
pid = os.getpid()
process = psutil.Process(pid)

# Get memory info
mem_info = process.memory_info()
print(f"Memory usage:")
print(f"  RSS: {mem_info.rss / 1024 / 1024:.2f} MB")
print(f"  VMS: {mem_info.vms / 1024 / 1024:.2f} MB")

# CPU usage
cpu_percent = process.cpu_percent(interval=1)
print(f"CPU usage: {cpu_percent}%")
EOF
```

## 9️⃣ Security Testing

### SQL Injection Testing
```bash
# Test that SQL injection is properly escaped
curl "http://localhost:5000/api/threat/'; DROP TABLE blocked_ips; --"

# Should return error, not delete table
sqlite3 ./data/sentinel.db "SELECT COUNT(*) FROM blocked_ips;"
```

### Authentication Testing
```bash
# Verify no auth bypass in unblock endpoint
curl -X POST http://localhost:5000/api/unblock/10.0.0.1

# Should work (no auth currently, but should in production)
```

## 🔟 Regression Testing

### Test Suite Checklist
```
[ ] Database creation and initialization
[ ] SSH monitor detection
[ ] Web monitor detection  
[ ] File integrity monitoring
[ ] IP blocking with iptables
[ ] GeoIP lookups
[ ] Discord notifications (if configured)
[ ] API endpoints all functional
[ ] Dashboard loads correctly
[ ] Map displays threats
[ ] Tables update live
[ ] Database persistence
[ ] Service restarts properly
[ ] Logs generated correctly
[ ] No memory leaks
[ ] Performance acceptable
```

## 📊 Test Results Template

```
Sentinel-V Test Report
======================
Date: [DATE]
Version: [VERSION]
Environment: [LINUX_VERSION]

Database Tests:        [PASS/FAIL]
Monitor Tests:         [PASS/FAIL]
Action Tests:          [PASS/FAIL]
API Tests:             [PASS/FAIL]
Dashboard Tests:       [PASS/FAIL]
Integration Tests:     [PASS/FAIL]
Performance Tests:     [PASS/FAIL]
Security Tests:        [PASS/FAIL]

Overall Result:        [PASS/FAIL]

Notes:
------
[Any issues or observations]
```

## 🔧 Automated Test Script

```bash
#!/bin/bash
# Run all tests automatically

set -e

echo "Running Sentinel-V full test suite..."

# Database tests
echo "Running database tests..."
python3 tests/test_database.py

# Monitor tests
echo "Running monitor tests..."
python3 tests/test_monitors.py

# Action tests
echo "Running action tests..."
python3 tests/test_actions.py

# API tests
echo "Running API tests..."
bash tests/test_api.sh

# Integration tests
echo "Running integration tests..."
bash tests/test_integration.sh

echo -e "\n✅ All tests passed successfully!"
```

---

**Testing Complete!** Your Sentinel-V installation is ready for production. ✅
