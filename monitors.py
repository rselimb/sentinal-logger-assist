"""
Asynchronous log monitoring module for SSH and Web threats.

This module provides classes for:
- SSH logMonitoring: Tracks failed password attempts in auth.log
- Web log monitoring: Analyzes nginx/access.log for WAF patterns
- Both run asynchronously using threading
"""

import re
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Callable, Optional, List
from collections import defaultdict

from database import SecurityDatabase


class SSHMonitor:
    """
    Monitors SSH authentication logs for brute-force attacks.
    
    Tracks failed password attempts and triggers bans after threshold.
    """

    def __init__(
        self,
        db: SecurityDatabase,
        callback: Callable[[str, str], None],
        log_path: str = "/var/log/auth.log",
        failed_threshold: int = 5
    ) -> None:
        """
        Initialize SSH monitor.
        
        Args:
            db: SecurityDatabase instance.
            callback: Function to call when attack detected (ip, reason).
            log_path: Path to auth.log file.
            failed_threshold: Number of failed attempts before ban.
        """
        self.db = db
        self.callback = callback
        self.log_path = log_path
        self.failed_threshold = failed_threshold
        self.failed_attempts = defaultdict(int)
        self.last_line_read = 0
        self.running = False
        self.thread: Optional[threading.Thread] = None

    def start(self) -> None:
        """
        Start the SSH monitoring thread.
        
        Runs asynchronously in background.
        """
        if not self.running:
            self.running = True
            self.thread = threading.Thread(target=self._monitor_loop, daemon=True)
            self.thread.start()

    def stop(self) -> None:
        """
        Stop the SSH monitoring thread.
        
        Gracefully shuts down monitoring.
        """
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)

    def _monitor_loop(self) -> None:
        """
        Main monitoring loop that continuously watches auth.log.
        
        Parses new lines and detects SSH brute-force attacks.
        """
        while self.running:
            try:
                if not Path(self.log_path).exists():
                    time.sleep(5)
                    continue

                with open(self.log_path, 'r') as f:
                    # Skip to last known position
                    f.seek(self.last_line_read)
                    
                    for line in f:
                        self._parse_ssh_log(line.strip())
                    
                    self.last_line_read = f.tell()

                time.sleep(5)  # Check every 5 seconds
            except Exception as e:
                print(f"SSH Monitor Error: {e}")
                time.sleep(5)

    def _parse_ssh_log(self, line: str) -> None:
        """
        Parse SSH log line and detect failed login attempts.
        
        Args:
            line: A line from auth.log.
        """
        # Pattern for failed password attempts
        if "Failed password for" in line or "Invalid user" in line:
            # Extract IP address
            ip_match = re.search(r'(\d+\.\d+\.\d+\.\d+)', line)
            if ip_match:
                ip = ip_match.group(1)
                self.failed_attempts[ip] += 1

                # Check if threshold reached
                if self.failed_attempts[ip] >= self.failed_threshold:
                    reason = f"SSH Brute-force: {self.failed_attempts[ip]} failed attempts"
                    self.callback(ip, reason)
                    self.failed_attempts[ip] = 0  # Reset counter

    def reset_ip(self, ip: str) -> None:
        """
        Reset failed attempts counter for an IP.
        
        Args:
            ip: IP address to reset.
        """
        if ip in self.failed_attempts:
            del self.failed_attempts[ip]


class WebMonitor:
    """
    Monitors web server logs for WAF-level attacks.
    
    Detects SQL Injection, XSS, Path Traversal patterns in nginx logs.
    """

    def __init__(
        self,
        db: SecurityDatabase,
        callback: Callable[[str, str, str], None],
        log_path: str = "/var/log/nginx/access.log"
    ) -> None:
        """
        Initialize Web monitor.
        
        Args:
            db: SecurityDatabase instance.
            callback: Function to call when attack detected (ip, attack_type, details).
            log_path: Path to nginx access.log file.
        """
        self.db = db
        self.callback = callback
        self.log_path = log_path
        self.last_line_read = 0
        self.running = False
        self.thread: Optional[threading.Thread] = None

        # WAF detection patterns
        self.patterns = {
            "SQL_INJECTION": re.compile(
                r"(UNION\s+SELECT|SELECT.*FROM|INSERT\s+INTO|DELETE\s+FROM|"
                r"DROP\s+TABLE|UPDATE.*SET|OR\s+1\s*=\s*1|' OR ')",
                re.IGNORECASE
            ),
            "XSS": re.compile(
                r"(<script[^>]*>|javascript:|onerror=|onload=|<iframe|<svg)",
                re.IGNORECASE
            ),
            "PATH_TRAVERSAL": re.compile(
                r"(\.\./|\.\.\\|%2e%2e%2f|%252e%252e%252f)"
            ),
            "COMMAND_INJECTION": re.compile(
                r"(;\s*ls|;\s*cat|`|&&|;sh|;\s*bash|\$\()",
                re.IGNORECASE
            )
        }

    def start(self) -> None:
        """
        Start the Web monitoring thread.
        
        Runs asynchronously in background.
        """
        if not self.running:
            self.running = True
            self.thread = threading.Thread(target=self._monitor_loop, daemon=True)
            self.thread.start()

    def stop(self) -> None:
        """
        Stop the Web monitoring thread.
        
        Gracefully shuts down monitoring.
        """
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)

    def _monitor_loop(self) -> None:
        """
        Main monitoring loop that continuously watches nginx access.log.
        
        Parses new lines and detects WAF attacks.
        """
        while self.running:
            try:
                if not Path(self.log_path).exists():
                    time.sleep(5)
                    continue

                with open(self.log_path, 'r') as f:
                    # Skip to last known position
                    f.seek(self.last_line_read)
                    
                    for line in f:
                        self._parse_web_log(line.strip())
                    
                    self.last_line_read = f.tell()

                time.sleep(5)  # Check every 5 seconds
            except Exception as e:
                print(f"Web Monitor Error: {e}")
                time.sleep(5)

    def _parse_web_log(self, line: str) -> None:
        """
        Parse web server log line and detect attacks.
        
        Args:
            line: A line from nginx access.log.
        """
        # Extract IP address from log (nginx format)
        ip_match = re.match(r'^(\d+\.\d+\.\d+\.\d+)', line)
        if not ip_match:
            return

        ip = ip_match.group(1)

        # Extract the request part (between quotes)
        request_match = re.search(r'"([^"]*)"', line)
        if not request_match:
            return

        request = request_match.group(1)

        # Check against all WAF patterns
        for attack_type, pattern in self.patterns.items():
            if pattern.search(request):
                self.callback(ip, attack_type, request)
                break  # Report only the first match per request


class FileIntegrityMonitor:
    """
    Monitors critical system files for unauthorized changes.
    
    Tracks SHA-256 hashes of sensitive files like /etc/passwd.
    """

    def __init__(
        self,
        db: SecurityDatabase,
        callback: Callable[[str, str], None],
        files: Optional[List[str]] = None
    ) -> None:
        """
        Initialize File Integrity Monitor.
        
        Args:
            db: SecurityDatabase instance.
            callback: Function to call when change detected (file_path, old_hash).
            files: List of file paths to monitor (default: critical system files).
        """
        self.db = db
        self.callback = callback
        self.files = files or [
            "/etc/passwd",
            "/etc/shadow",
            "/etc/sudoers",
            "/root/.ssh/authorized_keys"
        ]
        self.running = False
        self.thread: Optional[threading.Thread] = None

    def start(self) -> None:
        """
        Start the File Integrity monitoring thread.
        
        Runs asynchronously in background.
        """
        if not self.running:
            self.running = True
            # Initialize hashes
            for file_path in self.files:
                self._update_hash(file_path)
            
            self.thread = threading.Thread(target=self._monitor_loop, daemon=True)
            self.thread.start()

    def stop(self) -> None:
        """
        Stop the File Integrity monitoring thread.
        
        Gracefully shuts down monitoring.
        """
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)

    def _monitor_loop(self) -> None:
        """
        Main monitoring loop that checks file hashes.
        
        Runs every 60 seconds by default.
        """
        while self.running:
            try:
                for file_path in self.files:
                    self._check_file_integrity(file_path)
                time.sleep(60)  # Check every 60 seconds
            except Exception as e:
                print(f"FIM Monitor Error: {e}")
                time.sleep(60)

    def _get_file_hash(self, file_path: str) -> Optional[str]:
        """
        Calculate SHA-256 hash of a file.
        
        Args:
            file_path: Path to file to hash.
            
        Returns:
            Hex string of SHA-256 hash or None if file doesn't exist.
        """
        import hashlib
        
        try:
            if not Path(file_path).exists():
                return None
            
            sha256_hash = hashlib.sha256()
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(chunk)
            return sha256_hash.hexdigest()
        except Exception:
            return None

    def _check_file_integrity(self, file_path: str) -> None:
        """
        Check if a file's hash has changed.
        
        Args:
            file_path: Path to file to check.
        """
        current_hash = self._get_file_hash(file_path)
        
        if current_hash is None:
            return  # File doesn't exist
        
        stored_hash = self.db.get_file_hash(file_path)
        
        if stored_hash is None:
            # First time seeing this file
            self.db.add_file_hash(file_path, current_hash)
        elif stored_hash != current_hash:
            # File has changed!
            old_hash = stored_hash
            self.db.add_file_hash(file_path, current_hash)
            self.callback(file_path, old_hash)

    def _update_hash(self, file_path: str) -> None:
        """
        Update stored hash for a file.
        
        Args:
            file_path: Path to file to update.
        """
        file_hash = self._get_file_hash(file_path)
        if file_hash:
            self.db.add_file_hash(file_path, file_hash)
