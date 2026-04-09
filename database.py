"""
Database module for managing attacker IPs, GeoIP data, and file integrity.

This module provides SQLite3 abstraction for storing:
- Blocked IP addresses with ban timestamps
- GeoIP location data (country, city, lat, lon)
- File integrity checksums (SHA-256)
"""

import sqlite3
import hashlib
import threading
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Tuple, Dict, Any


class SecurityDatabase:
    """
    SQLite3-based database for security monitoring and threat tracking.
    
    Thread-safe operations using locks for concurrent access.
    """

    def __init__(self, db_path: str = "./sentinel.db") -> None:
        """
        Initialize the security database.
        
        Args:
            db_path: Path to the SQLite database file.
        """
        self.db_path = db_path
        self.lock = threading.RLock()
        self._initialize_db()

    def _initialize_db(self) -> None:
        """
        Initialize database tables if they don't exist.
        
        Creates three main tables:
        - blocked_ips: Tracks banned IP addresses
        - geoip_data: Stores geographic location information
        - file_integrity: Monitors file SHA-256 hashes
        """
        with self.lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Blocked IPs table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS blocked_ips (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ip_address TEXT UNIQUE NOT NULL,
                    ban_timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    reason TEXT,
                    status TEXT DEFAULT 'active'
                )
            """)

            # GeoIP Data table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS geoip_data (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ip_address TEXT UNIQUE NOT NULL,
                    country TEXT,
                    city TEXT,
                    latitude REAL,
                    longitude REAL,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # File Integrity Monitoring table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS file_integrity (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    file_path TEXT UNIQUE NOT NULL,
                    file_hash TEXT NOT NULL,
                    last_checked DATETIME DEFAULT CURRENT_TIMESTAMP,
                    status TEXT DEFAULT 'ok'
                )
            """)

            # Attack Log table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS attack_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ip_address TEXT NOT NULL,
                    attack_type TEXT NOT NULL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    details TEXT
                )
            """)

            conn.commit()
            conn.close()

    def add_blocked_ip(self, ip: str, reason: str = "Automatic ban") -> bool:
        """
        Add an IP address to the blocked list.
        
        Args:
            ip: IP address to block.
            reason: Reason for blocking (default: "Automatic ban").
            
        Returns:
            True if successful, False if IP already exists.
        """
        with self.lock:
            try:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO blocked_ips (ip_address, reason) VALUES (?, ?)",
                    (ip, reason)
                )
                conn.commit()
                conn.close()
                return True
            except sqlite3.IntegrityError:
                return False

    def get_blocked_ips(self) -> List[str]:
        """
        Retrieve all blocked IP addresses.
        
        Returns:
            List of blocked IP addresses with status 'active'.
        """
        with self.lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(
                "SELECT ip_address FROM blocked_ips WHERE status = 'active'"
            )
            ips = [row[0] for row in cursor.fetchall()]
            conn.close()
            return ips

    def is_ip_blocked(self, ip: str) -> bool:
        """
        Check if an IP address is currently blocked.
        
        Args:
            ip: IP address to check.
            
        Returns:
            True if IP is blocked, False otherwise.
        """
        with self.lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(
                "SELECT 1 FROM blocked_ips WHERE ip_address = ? AND status = 'active'",
                (ip,)
            )
            result = cursor.fetchone()
            conn.close()
            return result is not None

    def add_geoip_data(
        self,
        ip: str,
        country: str,
        city: str,
        latitude: float,
        longitude: float
    ) -> bool:
        """
        Store GeoIP location data for an IP address.
        
        Args:
            ip: IP address.
            country: Country name.
            city: City name.
            latitude: Geographic latitude.
            longitude: Geographic longitude.
            
        Returns:
            True if successful, False if data already exists.
        """
        with self.lock:
            try:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                cursor.execute(
                    """INSERT OR REPLACE INTO geoip_data 
                       (ip_address, country, city, latitude, longitude, updated_at)
                       VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)""",
                    (ip, country, city, latitude, longitude)
                )
                conn.commit()
                conn.close()
                return True
            except sqlite3.Error:
                return False

    def get_geoip_data(self, ip: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve GeoIP data for a specific IP.
        
        Args:
            ip: IP address to look up.
            
        Returns:
            Dictionary with country, city, latitude, longitude or None.
        """
        with self.lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(
                """SELECT country, city, latitude, longitude 
                   FROM geoip_data WHERE ip_address = ?""",
                (ip,)
            )
            row = cursor.fetchone()
            conn.close()
            
            if row:
                return {
                    "country": row[0],
                    "city": row[1],
                    "latitude": row[2],
                    "longitude": row[3]
                }
            return None

    def add_file_hash(self, file_path: str, file_hash: str) -> bool:
        """
        Store or update file integrity hash.
        
        Args:
            file_path: Path to the file being monitored.
            file_hash: SHA-256 hash of the file.
            
        Returns:
            True if successful.
        """
        with self.lock:
            try:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                cursor.execute(
                    """INSERT OR REPLACE INTO file_integrity 
                       (file_path, file_hash, last_checked, status)
                       VALUES (?, ?, CURRENT_TIMESTAMP, 'ok')""",
                    (file_path, file_hash)
                )
                conn.commit()
                conn.close()
                return True
            except sqlite3.Error:
                return False

    def get_file_hash(self, file_path: str) -> Optional[str]:
        """
        Retrieve stored hash for a monitored file.
        
        Args:
            file_path: Path to the file.
            
        Returns:
            Stored SHA-256 hash or None if not found.
        """
        with self.lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(
                "SELECT file_hash FROM file_integrity WHERE file_path = ?",
                (file_path,)
            )
            row = cursor.fetchone()
            conn.close()
            return row[0] if row else None

    def log_attack(self, ip: str, attack_type: str, details: str = "") -> bool:
        """
        Log a security attack event.
        
        Args:
            ip: IP address of the attacker.
            attack_type: Type of attack (SSH_BRUTEFORCE, SQL_INJECTION, XSS, PATH_TRAVERSAL).
            details: Additional attack details.
            
        Returns:
            True if successful.
        """
        with self.lock:
            try:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                cursor.execute(
                    """INSERT INTO attack_log (ip_address, attack_type, details)
                       VALUES (?, ?, ?)""",
                    (ip, attack_type, details)
                )
                conn.commit()
                conn.close()
                return True
            except sqlite3.Error:
                return False

    def get_attack_history(self, ip: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Retrieve attack history for an IP.
        
        Args:
            ip: IP address to look up.
            limit: Maximum number of records to return.
            
        Returns:
            List of attack records.
        """
        with self.lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(
                """SELECT attack_type, timestamp, details FROM attack_log 
                   WHERE ip_address = ? ORDER BY timestamp DESC LIMIT ?""",
                (ip, limit)
            )
            rows = cursor.fetchall()
            conn.close()
            
            return [
                {
                    "attack_type": row[0],
                    "timestamp": row[1],
                    "details": row[2]
                }
                for row in rows
            ]

    def get_all_threats(self) -> List[Dict[str, Any]]:
        """
        Retrieve all active threats with complete data.
        
        Returns:
            List of threats with IP, location, and attack types.
        """
        with self.lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(
                """SELECT b.ip_address, b.reason, b.ban_timestamp,
                          g.country, g.city, g.latitude, g.longitude
                   FROM blocked_ips b
                   LEFT JOIN geoip_data g ON b.ip_address = g.ip_address
                   WHERE b.status = 'active'
                   ORDER BY b.ban_timestamp DESC"""
            )
            rows = cursor.fetchall()
            conn.close()
            
            threats = []
            for row in rows:
                threats.append({
                    "ip": row[0],
                    "reason": row[1],
                    "ban_timestamp": row[2],
                    "country": row[3],
                    "city": row[4],
                    "latitude": row[5],
                    "longitude": row[6]
                })
            return threats

    def get_file_integrity_status(self) -> List[Dict[str, Any]]:
        """
        Retrieve status of all monitored files.
        
        Returns:
            List of file paths with their integrity status.
        """
        with self.lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(
                """SELECT file_path, status, last_checked FROM file_integrity
                   ORDER BY last_checked DESC"""
            )
            rows = cursor.fetchall()
            conn.close()
            
            return [
                {
                    "file_path": row[0],
                    "status": row[1],
                    "last_checked": row[2]
                }
                for row in rows
            ]
