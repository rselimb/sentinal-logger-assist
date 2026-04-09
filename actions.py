"""
Security action module for enforcing blocks and sending notifications.

This module:
- Executes iptables commands to block malicious IPs
- Sends Discord webhook notifications for alerts
- Manages GeoIP lookups via ip-api.com
"""

import subprocess
import threading
import requests
from typing import Callable, Optional
from database import SecurityDatabase


class ActionExecutor:
    """
    Executes security actions: IP blocks and notifications.
    
    Operates with thread-safety for concurrent threat responses.
    """

    def __init__(
        self,
        db: SecurityDatabase,
        discord_webhook_url: Optional[str] = None
    ) -> None:
        """
        Initialize the Action Executor.
        
        Args:
            db: SecurityDatabase instance.
            discord_webhook_url: Discord webhook URL for notifications (optional).
        """
        self.db = db
        self.discord_webhook_url = discord_webhook_url
        self.lock = threading.RLock()

    def block_ip(self, ip: str, reason: str = "Security threat") -> bool:
        """
        Block an IP address using iptables.
        
        Args:
            ip: IP address to block.
            reason: Reason for blocking.
            
        Returns:
            True if successful, False otherwise.
        """
        with self.lock:
            # Add to database first
            if not self.db.add_blocked_ip(ip, reason):
                return False  # IP already blocked

            try:
                # Execute iptables command to block the IP
                cmd = f"iptables -I INPUT -s {ip} -j DROP"
                subprocess.run(
                    cmd,
                    shell=True,
                    check=True,
                    capture_output=True,
                    timeout=10
                )
                
                # Also add IPv6 rule if applicable
                cmd_v6 = f"ip6tables -I INPUT -s {ip} -j DROP"
                try:
                    subprocess.run(
                        cmd_v6,
                        shell=True,
                        check=False,
                        capture_output=True,
                        timeout=10
                    )
                except Exception:
                    pass  # IPv6 might not be available

                return True
            except Exception as e:
                print(f"Failed to block IP {ip}: {e}")
                return False

    def unblock_ip(self, ip: str) -> bool:
        """
        Unblock an IP address using iptables.
        
        Args:
            ip: IP address to unblock.
            
        Returns:
            True if successful, False otherwise.
        """
        with self.lock:
            # Mark as inactive in database
            conn = self.db._initialize_db  # Access through lock
            try:
                import sqlite3
                conn = sqlite3.connect(self.db.db_path)
                cursor = conn.cursor()
                cursor.execute(
                    "UPDATE blocked_ips SET status = 'inactive' WHERE ip_address = ?",
                    (ip,)
                )
                conn.commit()
                conn.close()
            except Exception:
                pass

            try:
                # Remove from iptables
                cmd = f"iptables -D INPUT -s {ip} -j DROP"
                subprocess.run(
                    cmd,
                    shell=True,
                    check=True,
                    capture_output=True,
                    timeout=10
                )
                
                # Also remove IPv6 rule
                cmd_v6 = f"ip6tables -D INPUT -s {ip} -j DROP"
                try:
                    subprocess.run(
                        cmd_v6,
                        shell=True,
                        check=False,
                        capture_output=True,
                        timeout=10
                    )
                except Exception:
                    pass

                return True
            except Exception as e:
                print(f"Failed to unblock IP {ip}: {e}")
                return False

    def persist_iptables_rules(self) -> bool:
        """
        Persist iptables rules to survive reboot.
        
        Works on systems with iptables-persistent or similar.
        
        Returns:
            True if successful, False otherwise.
        """
        with self.lock:
            try:
                # Try to save with different methods
                commands = [
                    "iptables-save > /etc/iptables/rules.v4",
                    "ip6tables-save > /etc/iptables/rules.v6",
                    "systemctl restart iptables",
                ]
                
                for cmd in commands:
                    try:
                        subprocess.run(
                            cmd,
                            shell=True,
                            check=False,
                            capture_output=True,
                            timeout=10
                        )
                    except Exception:
                        pass
                
                return True
            except Exception as e:
                print(f"Failed to persist iptables rules: {e}")
                return False

    def fetch_geoip(self, ip: str) -> bool:
        """
        Fetch GeoIP data from ip-api.com.
        
        Args:
            ip: IP address to look up.
            
        Returns:
            True if successful and data stored.
        """
        try:
            # Check if already cached
            if self.db.get_geoip_data(ip) is not None:
                return True

            # Query ip-api.com
            url = f"http://ip-api.com/json/{ip}?fields=country,city,lat,lon"
            response = requests.get(url, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "success":
                    return self.db.add_geoip_data(
                        ip=ip,
                        country=data.get("country", "Unknown"),
                        city=data.get("city", "Unknown"),
                        latitude=data.get("lat", 0.0),
                        longitude=data.get("lon", 0.0)
                    )
            return False
        except Exception as e:
            print(f"GeoIP lookup error for {ip}: {e}")
            return False

    def send_discord_alert(
        self,
        ip: str,
        threat_type: str,
        details: str
    ) -> bool:
        """
        Send alert notification to Discord webhook.
        
        Args:
            ip: IP address of threat.
            threat_type: Type of threat detected.
            details: Detailed description.
            
        Returns:
            True if message sent successfully.
        """
        if not self.discord_webhook_url:
            return False

        try:
            geoip = self.db.get_geoip_data(ip)
            location = "Unknown"
            if geoip:
                location = f"{geoip['city']}, {geoip['country']}"

            # Build Discord embed
            embed = {
                "title": f"🚨 Security Alert: {threat_type}",
                "color": 0xFF0000,
                "fields": [
                    {
                        "name": "IP Address",
                        "value": ip,
                        "inline": True
                    },
                    {
                        "name": "Location",
                        "value": location,
                        "inline": True
                    },
                    {
                        "name": "Threat Type",
                        "value": threat_type,
                        "inline": False
                    },
                    {
                        "name": "Details",
                        "value": details[:1024],  # Limit to 1024 chars
                        "inline": False
                    }
                ],
                "footer": {
                    "text": "Sentinel-V Security System"
                }
            }

            payload = {
                "embeds": [embed]
            }

            response = requests.post(
                self.discord_webhook_url,
                json=payload,
                timeout=10
            )

            return response.status_code == 204
        except Exception as e:
            print(f"Failed to send Discord alert: {e}")
            return False

    def handle_threat(
        self,
        ip: str,
        threat_type: str,
        details: str
    ) -> None:
        """
        Comprehensive threat handling workflow.
        
        Blocks IP, fetches GeoIP, logs attack, and sends alert.
        
        Args:
            ip: IP address of threat.
            threat_type: Type of threat.
            details: Threat details.
        """
        # Check if already blocked
        if self.db.is_ip_blocked(ip):
            return

        # Block the IP
        self.block_ip(ip, f"{threat_type}: {details[:100]}")

        # Fetch GeoIP in background
        def fetch_geo():
            self.fetch_geoip(ip)
        
        geo_thread = threading.Thread(target=fetch_geo, daemon=True)
        geo_thread.start()

        # Log the attack
        self.db.log_attack(ip, threat_type, details)

        # Send Discord alert
        def send_alert():
            self.send_discord_alert(ip, threat_type, details)
        
        alert_thread = threading.Thread(target=send_alert, daemon=True)
        alert_thread.start()

    def handle_file_tampering(self, file_path: str, old_hash: str) -> None:
        """
        Handle detected file tampering.
        
        Args:
            file_path: Path to tampered file.
            old_hash: Previous SHA-256 hash.
        """
        print(f"⚠️  FILE TAMPERING DETECTED: {file_path}")
        
        # Log to database
        self.db.log_attack(
            "127.0.0.1",
            "FILE_TAMPERING",
            f"File: {file_path}, Previous Hash: {old_hash}"
        )

        # Send alert
        self.send_discord_alert(
            "127.0.0.1",
            "FILE_TAMPERING",
            f"Critical file changed: {file_path}"
        )
