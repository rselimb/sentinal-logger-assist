"""
Flask-based web dashboard and REST API for Sentinel-V.

Provides:
- Interactive web UI with Leaflet.js map and Bootstrap tables
- REST API endpoints for accessing threat data
- Real-time metrics and statistics
"""

from flask import Flask, render_template, jsonify, request
from datetime import datetime, timedelta
from database import SecurityDatabase
from pathlib import Path
import json


def create_app(db: SecurityDatabase) -> Flask:
    """
    Create and configure Flask application.
    
    Args:
        db: SecurityDatabase instance.
        
    Returns:
        Configured Flask app instance.
    """
    app = Flask(__name__)
    app.config['JSON_SORT_KEYS'] = False

    # API Endpoints

    @app.route('/api/threats', methods=['GET'])
    def get_threats():
        """
        Get all active threats with location data.
        
        Returns:
            JSON array of threat objects.
        """
        threats = db.get_all_threats()
        return jsonify({
            "status": "success",
            "count": len(threats),
            "data": threats
        })

    @app.route('/api/threat/<ip>', methods=['GET'])
    def get_threat_detail(ip: str):
        """
        Get detailed information about a specific IP threat.
        
        Args:
            ip: IP address to look up.
            
        Returns:
            JSON object with threat details.
        """
        geoip = db.get_geoip_data(ip)
        attack_history = db.get_attack_history(ip)
        is_blocked = db.is_ip_blocked(ip)

        return jsonify({
            "status": "success",
            "ip": ip,
            "blocked": is_blocked,
            "geoip": geoip,
            "attack_history": attack_history
        })

    @app.route('/api/files', methods=['GET'])
    def get_file_integrity():
        """
        Get status of all monitored files.
        
        Returns:
            JSON array of file integrity status.
        """
        files = db.get_file_integrity_status()
        return jsonify({
            "status": "success",
            "count": len(files),
            "data": files
        })

    @app.route('/api/stats', methods=['GET'])
    def get_statistics():
        """
        Get overall security statistics.
        
        Returns:
            JSON object with threat counts and metrics.
        """
        all_threats = db.get_all_threats()
        blocked_count = len(all_threats)

        # Count threats by country
        countries = {}
        for threat in all_threats:
            country = threat.get('country', 'Unknown')
            countries[country] = countries.get(country, 0) + 1

        return jsonify({
            "status": "success",
            "total_blocked": blocked_count,
            "threats_by_country": countries,
            "monitored_files": len(db.get_file_integrity_status())
        })

    @app.route('/api/unblock/<ip>', methods=['POST'])
    def unblock_ip(ip: str):
        """
        Unblock an IP address (Admin only).
        
        Args:
            ip: IP address to unblock.
            
        Returns:
            JSON response with result.
        """
        # In production, add authentication here
        try:
            import sqlite3
            conn = sqlite3.connect(db.db_path)
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE blocked_ips SET status = 'inactive' WHERE ip_address = ?",
                (ip,)
            )
            conn.commit()
            conn.close()

            return jsonify({
                "status": "success",
                "message": f"IP {ip} unblocked"
            })
        except Exception as e:
            return jsonify({
                "status": "error",
                "message": str(e)
            }), 500

    # HTML Dashboard Route

    @app.route('/', methods=['GET'])
    def dashboard():
        """
        Serve the main dashboard HTML page.
        
        Returns:
            Rendered HTML dashboard.
        """
        return render_template('dashboard.html')

    @app.route('/api/map-data', methods=['GET'])
    def get_map_data():
        """
        Get threat data formatted for map display.
        
        Returns:
            JSON array of marker objects for Leaflet.js.
        """
        threats = db.get_all_threats()
        markers = []

        for threat in threats:
            # Skip threats without location data
            if threat.get('latitude') is None or threat.get('longitude') is None:
                continue

            marker = {
                "ip": threat['ip'],
                "lat": threat['latitude'],
                "lon": threat['longitude'],
                "country": threat.get('country', 'Unknown'),
                "city": threat.get('city', 'Unknown'),
                "reason": threat.get('reason', 'Security threat'),
                "timestamp": threat.get('ban_timestamp', '')
            }
            markers.append(marker)

        return jsonify({
            "status": "success",
            "markers": markers
        })

    return app


def create_dashboard_html() -> str:
    """
    Create the dashboard HTML template.
    
    Returns:
        HTML string for dashboard page.
    """
    return '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Sentinel-V Security Dashboard</title>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/bootstrap/5.3.0/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
    <style>
        :root {
            --primary-color: #1a1a2e;
            --secondary-color: #16213e;
            --accent-color: #e94560;
            --success-color: #2ecc71;
        }

        body {
            background: linear-gradient(135deg, var(--primary-color) 0%, var(--secondary-color) 100%);
            color: #e0e0e0;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            min-height: 100vh;
        }

        .navbar {
            background: var(--secondary-color);
            border-bottom: 2px solid var(--accent-color);
            padding: 1.5rem;
        }

        .navbar-brand {
            font-weight: bold;
            font-size: 1.5rem;
            color: var(--accent-color) !important;
        }

        .card {
            background: rgba(22, 33, 62, 0.8);
            border: 1px solid var(--accent-color);
            border-radius: 0.5rem;
            box-shadow: 0 4px 15px rgba(233, 69, 96, 0.2);
        }

        .card-header {
            background: var(--secondary-color);
            border-bottom: 2px solid var(--accent-color);
            color: var(--accent-color);
            font-weight: bold;
        }

        .stat-box {
            text-align: center;
            padding: 2rem;
        }

        .stat-number {
            font-size: 2.5rem;
            font-weight: bold;
            color: var(--accent-color);
        }

        .stat-label {
            color: #a0a0a0;
            margin-top: 0.5rem;
        }

        #map {
            height: 500px;
            border-radius: 0.5rem;
            border: 1px solid var(--accent-color);
        }

        .leaflet-container {
            background: linear-gradient(135deg, #1a1f35 0%, #16213e 100%);
        }

        .table {
            color: #e0e0e0;
        }

        .table thead {
            background: var(--secondary-color);
            border-bottom: 2px solid var(--accent-color);
        }

        .table-hover tbody tr:hover {
            background: rgba(233, 69, 96, 0.1);
        }

        .badge-danger {
            background: var(--accent-color);
        }

        .badge-success {
            background: var(--success-color);
        }

        .badge-warning {
            background: #f39c12;
        }

        .btn-primary {
            background: var(--accent-color);
            border: none;
        }

        .btn-primary:hover {
            background: #d93450;
            color: white;
        }

        .refresh-btn {
            color: var(--accent-color);
            cursor: pointer;
            transition: transform 0.3s;
        }

        .refresh-btn:hover {
            transform: rotate(180deg);
        }

        .marker-icon {
            background: var(--accent-color);
            border-radius: 50%;
            width: 30px;
            height: 30px;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-weight: bold;
            border: 2px solid #fff;
        }

        .section-title {
            color: var(--accent-color);
            font-weight: bold;
            margin-top: 2rem;
            margin-bottom: 1rem;
            border-bottom: 2px solid var(--accent-color);
            padding-bottom: 0.5rem;
        }

        .loading {
            display: inline-block;
            width: 20px;
            height: 20px;
            border: 3px solid rgba(233, 69, 96, 0.3);
            border-radius: 50%;
            border-top-color: var(--accent-color);
            animation: spin 1s ease-in-out infinite;
        }

        @keyframes spin {
            to { transform: rotate(360deg); }
        }
    </style>
</head>
<body>
    <!-- Navigation -->
    <nav class="navbar navbar-dark">
        <div class="container-fluid">
            <span class="navbar-brand">
                <i class="fas fa-shield-alt" style="color: var(--accent-color); margin-right: 0.5rem;"></i>
                Sentinel-V Security Dashboard
            </span>
            <div>
                <button class="btn btn-sm btn-outline-danger" onclick="refreshData()">
                    <i class="fas fa-sync"></i> Refresh
                </button>
            </div>
        </div>
    </nav>

    <!-- Main Container -->
    <div class="container-fluid p-4">
        <!-- Statistics Row -->
        <div class="row mb-4">
            <div class="col-md-3">
                <div class="card stat-box">
                    <div class="stat-number" id="stat-blocked">0</div>
                    <div class="stat-label">Blocked IPs</div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="card stat-box">
                    <div class="stat-number" id="stat-countries">0</div>
                    <div class="stat-label">Countries</div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="card stat-box">
                    <div class="stat-number" id="stat-files">0</div>
                    <div class="stat-label">Monitored Files</div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="card stat-box">
                    <div class="stat-number" id="stat-status">
                        <span class="loading"></span>
                    </div>
                    <div class="stat-label">System Status</div>
                </div>
            </div>
        </div>

        <!-- Map Section -->
        <div class="card mb-4">
            <div class="card-header">
                <i class="fas fa-map"></i> Attack Map (Live Threats)
            </div>
            <div class="card-body p-0">
                <div id="map"></div>
            </div>
        </div>

        <!-- Threats Table -->
        <div class="card mb-4">
            <div class="card-header">
                <i class="fas fa-exclamation-triangle"></i> Blocked Threats
            </div>
            <div class="card-body">
                <div class="table-responsive">
                    <table class="table table-hover">
                        <thead>
                            <tr>
                                <th>IP Address</th>
                                <th>Country</th>
                                <th>City</th>
                                <th>Reason</th>
                                <th>Blocked At</th>
                                <th>Action</th>
                            </tr>
                        </thead>
                        <tbody id="threats-table">
                            <tr>
                                <td colspan="6" class="text-center">Loading...</td>
                            </tr>
                        </tbody>
                    </table>
                </div>
            </div>
        </div>

        <!-- File Integrity Section -->
        <div class="card">
            <div class="card-header">
                <i class="fas fa-lock"></i> File Integrity Status
            </div>
            <div class="card-body">
                <div class="table-responsive">
                    <table class="table table-hover">
                        <thead>
                            <tr>
                                <th>File Path</th>
                                <th>Status</th>
                                <th>Last Checked</th>
                            </tr>
                        </thead>
                        <tbody id="files-table">
                            <tr>
                                <td colspan="3" class="text-center">Loading...</td>
                            </tr>
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    </div>

    <!-- Scripts -->
    <script src="https://cdnjs.cloudflare.com/ajax/libs/bootstrap/5.3.0/js/bootstrap.bundle.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.min.js"></script>
    <script>
        let map = null;
        let markers = {};

        // Initialize map
        function initMap() {
            map = L.map('map').setView([20, 0], 2);
            
            // Dark mode tile layer
            L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
                attribution: '&copy; CartoDB',
                maxZoom: 19
            }).addTo(map);

            // Close non-existent markers on map
            map.on('load', loadMapMarkers);
        }

        // Load markers from API
        function loadMapMarkers() {
            fetch('/api/map-data')
                .then(res => res.json())
                .then(data => {
                    if (data.status === 'success') {
                        // Clear old markers
                        Object.values(markers).forEach(marker => map.removeLayer(marker));
                        markers = {};

                        // Add new markers
                        data.markers.forEach(threat => {
                            const marker = L.marker([threat.lat, threat.lon], {
                                title: threat.ip
                            }).addTo(map);

                            const popup = `
                                <div style="color: #000;">
                                    <strong>IP:</strong> ${threat.ip}<br>
                                    <strong>Location:</strong> ${threat.city}, ${threat.country}<br>
                                    <strong>Threat:</strong> ${threat.reason}<br>
                                    <strong>Blocked:</strong> ${threat.timestamp}
                                </div>
                            `;
                            marker.bindPopup(popup);
                            markers[threat.ip] = marker;
                        });
                    }
                })
                .catch(err => console.error('Map load error:', err));
        }

        // Refresh all data
        function refreshData() {
            loadStats();
            loadThreats();
            loadFiles();
            if (map) loadMapMarkers();
        }

        // Load statistics
        function loadStats() {
            fetch('/api/stats')
                .then(res => res.json())
                .then(data => {
                    if (data.status === 'success') {
                        document.getElementById('stat-blocked').textContent = data.total_blocked;
                        document.getElementById('stat-countries').textContent = Object.keys(data.threats_by_country).length;
                        document.getElementById('stat-files').textContent = data.monitored_files;
                        document.getElementById('stat-status').innerHTML = '🟢 ACTIVE';
                    }
                })
                .catch(err => {
                    document.getElementById('stat-status').innerHTML = '🔴 OFFLINE';
                });
        }

        // Load threats table
        function loadThreats() {
            fetch('/api/threats')
                .then(res => res.json())
                .then(data => {
                    if (data.status === 'success') {
                        const tbody = document.getElementById('threats-table');
                        if (data.count === 0) {
                            tbody.innerHTML = '<tr><td colspan="6" class="text-center"><span class="badge badge-success">No active threats</span></td></tr>';
                            return;
                        }

                        tbody.innerHTML = data.data.map(threat => `
                            <tr>
                                <td><code>${threat.ip}</code></td>
                                <td>${threat.country || 'Unknown'}</td>
                                <td>${threat.city || 'Unknown'}</td>
                                <td>${threat.reason || 'Security threat'}</td>
                                <td>${new Date(threat.ban_timestamp).toLocaleString()}</td>
                                <td>
                                    <button class="btn btn-sm btn-outline-warning" onclick="unblockIP('${threat.ip}')">
                                        Unblock
                                    </button>
                                </td>
                            </tr>
                        `).join('');
                    }
                })
                .catch(err => console.error('Threats load error:', err));
        }

        // Load files table
        function loadFiles() {
            fetch('/api/files')
                .then(res => res.json())
                .then(data => {
                    if (data.status === 'success') {
                        const tbody = document.getElementById('files-table');
                        tbody.innerHTML = data.data.map(file => `
                            <tr>
                                <td><code>${file.file_path}</code></td>
                                <td>
                                    <span class="badge ${file.status === 'ok' ? 'badge-success' : 'badge-danger'}">
                                        ${file.status.toUpperCase()}
                                    </span>
                                </td>
                                <td>${new Date(file.last_checked).toLocaleString()}</td>
                            </tr>
                        `).join('');
                    }
                })
                .catch(err => console.error('Files load error:', err));
        }

        // Unblock IP
        function unblockIP(ip) {
            if (!confirm(`Unblock IP ${ip}?`)) return;
            
            fetch(`/api/unblock/${ip}`, {method: 'POST'})
                .then(res => res.json())
                .then(data => {
                    alert(data.message);
                    refreshData();
                })
                .catch(err => alert('Error: ' + err));
        }

        // Initialize on load
        document.addEventListener('DOMContentLoaded', () => {
            initMap();
            refreshData();
            
            // Auto-refresh every 30 seconds
            setInterval(refreshData, 30000);
        });
    </script>
</body>
</html>
'''


# Create templates directory and HTML file
def setup_templates(app: Flask) -> None:
    """
    Set up template files for Flask app.
    
    Args:
        app: Flask application instance.
    """
    templates_dir = Path(app.instance_path) / 'templates'
    templates_dir.mkdir(parents=True, exist_ok=True)

    dashboard_html = templates_dir / 'dashboard.html'
    dashboard_html.write_text(create_dashboard_html())
