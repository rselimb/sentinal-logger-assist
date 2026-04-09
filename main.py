"""
Sentinel-V Main Entry Point - Master orchestration module.

This module:
- Initializes all security monitoring modules
- Manages thread lifecycle
- Orchestrates threat response
- Runs Flask web dashboard
"""

import os
import sys
import signal
import threading
import time
from dotenv import load_dotenv
from pathlib import Path

from database import SecurityDatabase
from monitors import SSHMonitor, WebMonitor, FileIntegrityMonitor
from actions import ActionExecutor
from dashboard import create_app, setup_templates


class SentinelV:
    """
    Master security system orchestrator.
    
    Coordinates all monitoring modules, threat detection, and response actions.
    """

    def __init__(
        self,
        db_path: str = "./sentinel.db",
        discord_webhook: str = None,
        ssh_log: str = "/var/log/auth.log",
        web_log: str = "/var/log/nginx/access.log"
    ) -> None:
        """
        Initialize Sentinel-V system.
        
        Args:
            db_path: Path to SQLite database.
            discord_webhook: Discord webhook URL for alerts.
            ssh_log: Path to SSH authentication log.
            web_log: Path to web server access log.
        """
        self.running = False
        self.db = SecurityDatabase(db_path)
        self.executor = ActionExecutor(self.db, discord_webhook)

        # Initialize monitors
        self.ssh_monitor = SSHMonitor(
            self.db,
            self._on_ssh_threat,
            ssh_log,
            failed_threshold=5
        )

        self.web_monitor = WebMonitor(
            self.db,
            self._on_web_threat,
            web_log
        )

        self.fim_monitor = FileIntegrityMonitor(
            self.db,
            self._on_file_tampering
        )

        # Flask app
        self.flask_app = create_app(self.db)
        setup_templates(self.flask_app)

        # Thread management
        self.monitors_thread: threading.Thread = None
        self.flask_thread: threading.Thread = None

    def _on_ssh_threat(self, ip: str, reason: str) -> None:
        """
        Callback for SSH brute-force detection.
        
        Args:
            ip: Attacker IP address.
            reason: Attack reason/details.
        """
        print(f"🔴 SSH THREAT: {ip} - {reason}")
        self.executor.handle_threat(ip, "SSH_BRUTEFORCE", reason)

    def _on_web_threat(self, ip: str, attack_type: str, details: str) -> None:
        """
        Callback for WAF attack detection.
        
        Args:
            ip: Attacker IP address.
            attack_type: Type of attack (SQL_INJECTION, XSS, etc).
            details: Attack payload/details.
        """
        print(f"🔴 WEB THREAT: {ip} - {attack_type}: {details[:80]}")
        self.executor.handle_threat(ip, f"WAF_{attack_type}", details)

    def _on_file_tampering(self, file_path: str, old_hash: str) -> None:
        """
        Callback for file integrity violation.
        
        Args:
            file_path: Path to tampered file.
            old_hash: Previous SHA-256 hash.
        """
        print(f"🔴 FILE TAMPERING: {file_path}")
        self.executor.handle_file_tampering(file_path, old_hash)

    def start_monitors(self) -> None:
        """
        Start all security monitoring modules.
        
        Runs in dedicated thread to avoid blocking.
        """
        def monitor_loop():
            print("🚀 Starting security monitors...")
            self.ssh_monitor.start()
            self.web_monitor.start()
            self.fim_monitor.start()

            print("✅ All monitors started")
            print("📡 Monitoring:")
            print("   - SSH Authentication (auth.log)")
            print("   - Web Access Logs (nginx/access.log)")
            print("   - File Integrity (critical system files)")

            # Keep thread alive
            while self.running:
                time.sleep(1)

            # Cleanup
            self.ssh_monitor.stop()
            self.web_monitor.stop()
            self.fim_monitor.stop()
            print("✅ All monitors stopped")

        self.monitors_thread = threading.Thread(target=monitor_loop, daemon=False)
        self.monitors_thread.start()

    def start_dashboard(self, host: str = "0.0.0.0", port: int = 5000) -> None:
        """
        Start Flask web dashboard.
        
        Args:
            host: Host to bind to.
            port: Port to listen on.
        """
        def run_flask():
            print(f"📊 Starting Flask dashboard on {host}:{port}")
            self.flask_app.run(
                host=host,
                port=port,
                debug=False,
                use_reloader=False
            )

        self.flask_thread = threading.Thread(target=run_flask, daemon=True)
        self.flask_thread.start()

    def start(self, enable_dashboard: bool = True) -> None:
        """
        Start the entire Sentinel-V system.
        
        Args:
            enable_dashboard: Whether to start Flask dashboard.
        """
        self.running = True
        
        print("""
        ╔════════════════════════════════════════╗
        ║      SENTINEL-V SECURITY SYSTEM        ║
        ║   Enterprise Server Protection Suite   ║
        ╚════════════════════════════════════════╝
        """)

        self.start_monitors()
        
        if enable_dashboard:
            self.start_dashboard()

        print("\n✅ Sentinel-V is operational")
        print("Press Ctrl+C to shutdown gracefully\n")

        # Keep main thread alive
        try:
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n\n⏹️  Shutting down...")
            self.stop()

    def stop(self) -> None:
        """
        Gracefully shutdown Sentinel-V system.
        
        Stops all monitors and saves state.
        """
        self.running = False

        # Wait for monitor thread
        if self.monitors_thread:
            self.monitors_thread.join(timeout=10)

        print("✅ Sentinel-V shutdown complete")
        print("📊 All threat data saved to database")

    def persist_rules(self) -> None:
        """
        Persist iptables rules to survive system reboot.
        
        Saves current firewall rules.
        """
        print("💾 Persisting firewall rules...")
        self.executor.persist_iptables_rules()
        print("✅ Rules persisted")

    def get_status(self) -> dict:
        """
        Get current system status.
        
        Returns:
            Dictionary with system status information.
        """
        threats = self.db.get_all_threats()
        files = self.db.get_file_integrity_status()

        return {
            "running": self.running,
            "blocked_ips": len(threats),
            "monitored_files": len(files),
            "ssh_monitor_active": self.ssh_monitor.running,
            "web_monitor_active": self.web_monitor.running,
            "fim_monitor_active": self.fim_monitor.running
        }


def main() -> None:
    """
    Main entry point for Sentinel-V.
    
    Loads configuration and starts the system.
    """
    # Load environment variables
    load_dotenv()

    # Configuration from environment or defaults
    db_path = os.getenv("SENTINEL_DB_PATH", "./sentinel.db")
    discord_webhook = os.getenv("DISCORD_WEBHOOK_URL")
    ssh_log = os.getenv("SSH_LOG_PATH", "/var/log/auth.log")
    web_log = os.getenv("WEB_LOG_PATH", "/var/log/nginx/access.log")
    dashboard_port = int(os.getenv("DASHBOARD_PORT", "5000"))
    dashboard_host = os.getenv("DASHBOARD_HOST", "0.0.0.0")

    # Initialize system
    sentinel = SentinelV(
        db_path=db_path,
        discord_webhook=discord_webhook,
        ssh_log=ssh_log,
        web_log=web_log
    )

    # Setup signal handlers for graceful shutdown
    def signal_handler(sig, frame):
        print("\n\n⏹️  Received shutdown signal...")
        sentinel.stop()
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Start the system
    sentinel.start(enable_dashboard=True)


if __name__ == "__main__":
    main()
