"""
Smart Farming Drones - Flask Web Dashboard
==========================================

Real-time web dashboard for monitoring drone operations, crop health analysis,
and precision agriculture data visualization.

Author: Smart Farming AI Team
Date: 2024
"""

import os
import sys
import json
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from flask import Flask, render_template, jsonify, request, send_file
import plotly.graph_objs as go
import plotly.utils
from plotly.offline import plot
import logging
import threading
import time
import random

# Import our custom modules
# Ensure project root is on sys.path so top-level imports (scripts.*) work
# even when this file is executed from inside the dashboard folder.
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# Import our custom modules
from scripts.drone_simulation import DroneSimulator
try:
    from scripts.image_processing import ImageProcessor  # optional, not required for dashboard runtime
except Exception as _import_err:
    ImageProcessor = None
    logger = logging.getLogger(__name__) if 'logging' in globals() else None
    if logger:
        logger.warning(f"ImageProcessor not available: {_import_err}")
from scripts.ai_reporting import AIReportGenerator

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.secret_key = 'smart_farming_drones_2024'

# Global variables for simulation
drone_simulator = None
simulation_thread = None
dashboard_data = {
    'drone_status': {},
    'field_data': [],
    'mission_stats': {},
    'real_time_alerts': [],
    'last_update': datetime.now()
}

# Simple persistence for missions
MISSIONS_PATH = os.path.join(PROJECT_ROOT, 'data', 'missions.json')
os.makedirs(os.path.dirname(MISSIONS_PATH), exist_ok=True)

def _load_missions():
    if os.path.exists(MISSIONS_PATH):
        try:
            with open(MISSIONS_PATH, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def _save_missions(missions):
    try:
        with open(MISSIONS_PATH, 'w', encoding='utf-8') as f:
            json.dump(missions, f, indent=2)
    except Exception as e:
        logger.error(f"Failed to save missions: {e}")

missions_store = _load_missions()

# --- Simple session auth (demo) ---
DEMO_USERS = {
    'admin@farm.local': {'password': 'admin123', 'role': 'admin'},
    'farmer@farm.local': {'password': 'farmer123', 'role': 'farmer'},
    'agronomist@farm.local': {'password': 'agro123', 'role': 'agronomist'}
}

@app.route('/auth/login', methods=['POST'])
def auth_login():
    try:
        payload = request.get_json(force=True) or {}
        email = (payload.get('email') or '').strip().lower()
        pwd = payload.get('password') or ''
        user = DEMO_USERS.get(email)
        if not user or user['password'] != pwd:
            return jsonify({'success': False, 'message': 'Invalid credentials'}), 401
        session = {
            'email': email,
            'role': user['role'],
            'login_at': datetime.utcnow().isoformat() + 'Z'
        }
        return jsonify({'success': True, 'session': session})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 400

@app.route('/auth/logout', methods=['POST'])
def auth_logout():
    return jsonify({'success': True})

class DashboardDataManager:
    """
    Manages dashboard data and real-time updates
    """
    
    def __init__(self):
        self.data_lock = threading.Lock()
        self.update_interval = 5  # seconds
        
    def update_dashboard_data(self):
        """
        Update dashboard data from drone simulation
        """
        global dashboard_data
        
        with self.data_lock:
            if drone_simulator:
                # Update drone status
                dashboard_data['drone_status'] = drone_simulator.get_status()
            else:
                # Provide mock drone status when simulator is not initialized
                dashboard_data['drone_status'] = {
                    'battery_level': 87.5,
                    'spray_level': 8.5,
                    'is_flying': False,
                    'position': {'x': 0, 'y': 0, 'z': 0},
                    'status': 'Ready'
                }
            
            # Update field data
            dashboard_data['field_data'] = self._prepare_field_data()
            
            # Update mission stats
            dashboard_data['mission_stats'] = self._prepare_mission_stats()
            
            # Update alerts
            dashboard_data['real_time_alerts'] = self._generate_alerts()
            
            dashboard_data['last_update'] = datetime.now()
    
    def _prepare_field_data(self):
        """
        Prepare field zone data for visualization
        """
        if not drone_simulator:
            # Return mock data when simulator is not initialized
            mock_data = []
            for i in range(15):
                health_statuses = ['Healthy', 'Healthy', 'Healthy', 'Diseased', 'Pest-affected']
                mock_data.append({
                    'zone_id': f'Z{i+1:03d}',
                    'x': random.uniform(50, 450),
                    'y': random.uniform(50, 450),
                    'health_status': random.choice(health_statuses),
                    'ndvi_value': random.uniform(0.3, 0.9),
                    'moisture_level': random.uniform(40, 90),
                    'last_sprayed': None
                })
            return mock_data
        
        field_data = []
        for zone in drone_simulator.field_zones:
            field_data.append({
                'zone_id': zone.zone_id,
                'x': zone.center_x,
                'y': zone.center_y,
                'health_status': zone.health_status,
                'ndvi_value': zone.ndvi_value,
                'moisture_level': zone.moisture_level,
                'last_sprayed': zone.last_sprayed.isoformat() if zone.last_sprayed else None
            })
        
        return field_data
    
    def _prepare_mission_stats(self):
        """
        Prepare mission statistics
        """
        if not drone_simulator:
            # Return mock stats when simulator is not initialized
            return {
                'zones_scanned': 0,
                'actions_taken': 0,
                'battery_level': 87.5,
                'spray_level': 8.5,
                'flight_time': 0,
                'success_rate': 0
            }
        
        stats = {
            'zones_scanned': len(drone_simulator.scan_data),
            'actions_taken': len(drone_simulator.action_history),
            'battery_level': drone_simulator.battery_level,
            'spray_level': drone_simulator.current_spray_level,
            'flight_time': len(drone_simulator.flight_log),
            'success_rate': self._calculate_success_rate()
        }
        
        return stats
    
    def _calculate_success_rate(self):
        """
        Calculate mission success rate
        """
        if not drone_simulator or not drone_simulator.action_history:
            return 0
        
        successful_actions = sum(1 for action in drone_simulator.action_history if action.success)
        total_actions = len(drone_simulator.action_history)
        
        return (successful_actions / total_actions * 100) if total_actions > 0 else 0
    
    def _generate_alerts(self):
        """
        Generate real-time alerts
        """
        alerts = []
        
        if drone_simulator:
            # Battery alert
            if drone_simulator.battery_level < 20:
                alerts.append({
                    'type': 'warning',
                    'message': f'Low battery: {drone_simulator.battery_level:.1f}%',
                    'timestamp': datetime.now().isoformat()
                })
            
            # Spray level alert
            if drone_simulator.current_spray_level < 2:
                alerts.append({
                    'type': 'warning',
                    'message': f'Low spray capacity: {drone_simulator.current_spray_level:.1f}L',
                    'timestamp': datetime.now().isoformat()
                })
            
            # Health alerts
            if drone_simulator.scan_data:
                recent_scans = drone_simulator.scan_data[-10:]  # Last 10 scans
                diseased_count = sum(1 for scan in recent_scans if scan['health_status'] == 'Diseased')
                
                if diseased_count > 3:
                    alerts.append({
                        'type': 'critical',
                        'message': f'High disease prevalence: {diseased_count} diseased zones',
                        'timestamp': datetime.now().isoformat()
                    })
        
        return alerts[-5:]  # Keep last 5 alerts

# Initialize data manager
data_manager = DashboardDataManager()

@app.after_request
def add_security_headers(response):
    """
    Add basic security and caching headers to API responses
    """
    response.headers.setdefault('X-Content-Type-Options', 'nosniff')
    response.headers.setdefault('X-Frame-Options', 'SAMEORIGIN')
    response.headers.setdefault('Referrer-Policy', 'no-referrer-when-downgrade')
    response.headers.setdefault('Cache-Control', 'no-store')
    return response

@app.route('/health')
def health():
    """
    Simple health check endpoint
    """
    return jsonify({
        'status': 'ok',
        'service': 'smart-farming-dashboard',
        'timestamp': datetime.utcnow().isoformat() + 'Z'
    })

@app.route('/')
def index():
    """
    Landing page
    """
    return render_template('index.html')

@app.route('/features')
def features():
    """
    Features page
    """
    return render_template('features.html')

@app.route('/technology')
def technology():
    """
    Technology page
    """
    return render_template('technology.html')

@app.route('/about')
def about():
    """
    About page
    """
    return render_template('about.html')

@app.route('/contact')
def contact():
    """
    Contact page
    """
    return render_template('contact.html')

@app.route('/dashboard')
def dashboard():
    """
    Main dashboard page
    """
    return render_template('dashboard.html')

@app.route('/dashboard_enhanced')
def dashboard_enhanced():
    """
    Enhanced real-time dashboard with crop status and spray analysis
    """
    return render_template('dashboard_enhanced.html')

# ---- Missions API ----
@app.route('/api/missions', methods=['GET', 'POST'])
def missions():
    try:
        if request.method == 'POST':
            payload = request.get_json(force=True) or {}
            mission_id = payload.get('id') or f"mis_{int(time.time())}_{random.randint(1000,9999)}"
            mission = {
                'id': mission_id,
                'name': payload.get('name') or f"Mission {mission_id[-4:]}",
                'origin': {
                    'lat': float(payload.get('origin', {}).get('lat', 28.6139)),
                    'lng': float(payload.get('origin', {}).get('lng', 77.2090))
                },
                'created_at': datetime.utcnow().isoformat() + 'Z',
                'track': []
            }
            missions_store[mission_id] = mission
            _save_missions(missions_store)
            return jsonify({'success': True, 'mission': mission}), 201
        else:
            return jsonify({'missions': list(missions_store.values())})
    except Exception as e:
        logger.error(f"missions API error: {e}")
        return jsonify({'success': False, 'message': str(e)}), 400

@app.route('/api/missions/<mission_id>', methods=['GET'])
def get_mission(mission_id: str):
    mission = missions_store.get(mission_id)
    if not mission:
        return jsonify({'error': 'Not found'}), 404
    return jsonify(mission)

@app.route('/api/missions/<mission_id>/track', methods=['GET', 'POST'])
def mission_track(mission_id: str):
    mission = missions_store.get(mission_id)
    if not mission:
        return jsonify({'error': 'Not found'}), 404
    if request.method == 'POST':
        try:
            payload = request.get_json(force=True) or {}
            point = {
                'lat': float(payload.get('lat')),
                'lng': float(payload.get('lng')),
                'timestamp': payload.get('timestamp') or datetime.utcnow().isoformat() + 'Z',
                'status': payload.get('status') or 'ok'
            }
            mission['track'].append(point)
            _save_missions(missions_store)
            return jsonify({'success': True})
        except Exception as e:
            return jsonify({'success': False, 'message': str(e)}), 400
    else:
        return jsonify({'track': mission.get('track', [])})

@app.route('/api/drone_status')
def get_drone_status():
    """
    Get current drone status
    """
    data_manager.update_dashboard_data()
    return jsonify(dashboard_data['drone_status'])

@app.route('/api/field_data')
def get_field_data():
    """
    Get field zone data
    """
    data_manager.update_dashboard_data()
    return jsonify(dashboard_data['field_data'])

@app.route('/api/mission_stats')
def get_mission_stats():
    """
    Get mission statistics
    """
    data_manager.update_dashboard_data()
    return jsonify(dashboard_data['mission_stats'])

@app.route('/api/alerts')
def get_alerts():
    """
    Get real-time alerts
    """
    data_manager.update_dashboard_data()
    return jsonify(dashboard_data['real_time_alerts'])

@app.route('/api/crop_status')
def get_crop_status():
    """
    Get real-time crop status summary - GOOD or NOT GOOD with percentages
    """
    data_manager.update_dashboard_data()
    field_data = dashboard_data['field_data']
    
    if not field_data:
        return jsonify({
            'status': 'no_data',
            'message': 'No scan data available',
            'good_crops': 0,
            'bad_crops': 0,
            'total_zones': 0,
            'good_percentage': 0,
            'bad_percentage': 0,
            'spray_percentage': 0
        })
    
    total_zones = len(field_data)
    
    # Count good vs not good crops
    good_crops = sum(1 for zone in field_data if zone.get('health_status') in ['Healthy', 'healthy'])
    bad_crops = total_zones - good_crops
    
    # Calculate zones needing spray
    needs_spray = sum(1 for zone in field_data 
                     if zone.get('health_status') in ['Diseased', 'diseased', 'Pest-affected', 'critical'])
    
    # Calculate percentages
    good_percentage = (good_crops / total_zones * 100) if total_zones > 0 else 0
    bad_percentage = (bad_crops / total_zones * 100) if total_zones > 0 else 0
    spray_percentage = (needs_spray / total_zones * 100) if total_zones > 0 else 0
    
    # Determine overall status
    if good_percentage >= 70:
        overall_status = 'GOOD'
        status_message = '✅ Most crops are healthy!'
    elif good_percentage >= 50:
        overall_status = 'MODERATE'
        status_message = '⚠️ Some crops need attention'
    else:
        overall_status = 'NOT GOOD'
        status_message = '❌ Urgent attention required!'
    
    return jsonify({
        'status': overall_status,
        'message': status_message,
        'good_crops': good_crops,
        'bad_crops': bad_crops,
        'total_zones': total_zones,
        'good_percentage': round(good_percentage, 1),
        'bad_percentage': round(bad_percentage, 1),
        'spray_percentage': round(spray_percentage, 1),
        'zones_need_spray': needs_spray,
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/spray_analysis')
def get_spray_analysis():
    """
    Get detailed spray requirement analysis
    """
    data_manager.update_dashboard_data()
    field_data = dashboard_data['field_data']
    
    if not field_data:
        return jsonify({
            'total_zones': 0,
            'spray_required': 0,
            'spray_percentage': 0,
            'critical_zones': 0,
            'high_priority': 0,
            'medium_priority': 0,
            'low_priority': 0
        })
    
    total_zones = len(field_data)
    
    # Categorize zones by spray priority
    critical = sum(1 for zone in field_data if zone.get('health_status') == 'critical')
    diseased = sum(1 for zone in field_data if zone.get('health_status') in ['Diseased', 'diseased'])
    pest_affected = sum(1 for zone in field_data if zone.get('health_status') == 'Pest-affected')
    borderline = sum(1 for zone in field_data if zone.get('health_status') == 'borderline')
    
    spray_required = critical + diseased + pest_affected
    spray_percentage = (spray_required / total_zones * 100) if total_zones > 0 else 0
    
    return jsonify({
        'total_zones': total_zones,
        'spray_required': spray_required,
        'spray_percentage': round(spray_percentage, 1),
        'critical_zones': critical,
        'high_priority': diseased,
        'medium_priority': pest_affected,
        'low_priority': borderline,
        'estimated_spray_amount': f"{spray_required * 2}L",  # 2L per zone average
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/start_mission', methods=['POST'])
def start_mission():
    """
    Start drone mission
    """
    global drone_simulator, simulation_thread
    
    try:
        if drone_simulator and drone_simulator.is_flying:
            return jsonify({'success': False, 'message': 'Mission already in progress'})
        
        # Initialize drone simulator
        drone_simulator = DroneSimulator(field_width=500, field_height=500)
        
        # Start mission in background thread
        def run_mission():
            drone_simulator.autonomous_mission(mission_duration=300)  # 5 minutes
        
        simulation_thread = threading.Thread(target=run_mission)
        simulation_thread.daemon = True
        simulation_thread.start()
        
        return jsonify({'success': True, 'message': 'Mission started successfully'})
    
    except Exception as e:
        logger.error(f"Error starting mission: {str(e)}")
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/stop_mission', methods=['POST'])
def stop_mission():
    """
    Stop drone mission
    """
    global drone_simulator
    
    try:
        if drone_simulator and drone_simulator.is_flying:
            drone_simulator.land()
            return jsonify({'success': True, 'message': 'Mission stopped successfully'})
        else:
            return jsonify({'success': False, 'message': 'No active mission to stop'})
    
    except Exception as e:
        logger.error(f"Error stopping mission: {str(e)}")
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/health_chart')
def get_health_chart():
    """
    Generate crop health distribution chart
    """
    try:
        data_manager.update_dashboard_data()
        field_data = dashboard_data['field_data']
        
        if not field_data:
            return jsonify({'error': 'No field data available'})
        
        # Count health status
        health_counts = {}
        for zone in field_data:
            status = zone['health_status']
            health_counts[status] = health_counts.get(status, 0) + 1
        
        # Create pie chart
        fig = go.Figure(data=[go.Pie(
            labels=list(health_counts.keys()),
            values=list(health_counts.values()),
            hole=0.3
        )])
        
        fig.update_layout(
            title="Crop Health Distribution",
            showlegend=True,
            height=400
        )
        
        return jsonify(plot(fig, output_type='div', include_plotlyjs=False))
    
    except Exception as e:
        logger.error(f"Error generating health chart: {str(e)}")
        return jsonify({'error': str(e)})

@app.route('/api/ndvi_chart')
def get_ndvi_chart():
    """
    Generate NDVI distribution chart
    """
    try:
        data_manager.update_dashboard_data()
        field_data = dashboard_data['field_data']
        
        if not field_data:
            return jsonify({'error': 'No field data available'})
        
        ndvi_values = [zone['ndvi_value'] for zone in field_data]
        
        # Create histogram
        fig = go.Figure(data=[go.Histogram(
            x=ndvi_values,
            nbinsx=20,
            marker_color='green',
            opacity=0.7
        )])
        
        fig.update_layout(
            title="NDVI Distribution",
            xaxis_title="NDVI Value",
            yaxis_title="Frequency",
            height=400
        )
        
        return jsonify(plot(fig, output_type='div', include_plotlyjs=False))
    
    except Exception as e:
        logger.error(f"Error generating NDVI chart: {str(e)}")
        return jsonify({'error': str(e)})

@app.route('/api/moisture_chart')
def get_moisture_chart():
    """
    Generate moisture level chart
    """
    try:
        data_manager.update_dashboard_data()
        field_data = dashboard_data['field_data']
        
        if not field_data:
            return jsonify({'error': 'No field data available'})
        
        moisture_values = [zone['moisture_level'] for zone in field_data]
        
        # Create bar chart
        fig = go.Figure(data=[go.Bar(
            x=list(range(len(moisture_values))),
            y=moisture_values,
            marker_color='blue',
            opacity=0.7
        )])
        
        fig.update_layout(
            title="Moisture Levels by Zone",
            xaxis_title="Zone Index",
            yaxis_title="Moisture Level (%)",
            height=400
        )
        
        return jsonify(plot(fig, output_type='div', include_plotlyjs=False))
    
    except Exception as e:
        logger.error(f"Error generating moisture chart: {str(e)}")
        return jsonify({'error': str(e)})

@app.route('/api/generate_report', methods=['POST'])
def generate_report():
    """
    Generate AI report
    """
    try:
        if not drone_simulator:
            return jsonify({'success': False, 'message': 'No drone data available'})
        
        # Save current simulation data
        os.makedirs('data/mock_data', exist_ok=True)
        
        # Save scan data
        if drone_simulator.scan_data:
            scan_df = pd.DataFrame(drone_simulator.scan_data)
            scan_df.to_csv('data/mock_data/scan_data.csv', index=False)
        
        # Save spraying data
        if drone_simulator.spraying_data:
            spray_df = pd.DataFrame(drone_simulator.spraying_data)
            spray_df.to_csv('data/mock_data/spraying_data.csv', index=False)
        
        # Generate mission report
        mission_report = drone_simulator.generate_mission_report()
        with open('data/mock_data/mission_report.json', 'w') as f:
            json.dump(mission_report, f, indent=2, default=str)
        
        # Generate AI report
        report_generator = AIReportGenerator()
        report_generator.load_mission_data(
            'data/mock_data/scan_data.csv',
            'data/mock_data/spraying_data.csv',
            'data/mock_data/mission_report.json'
        )
        
        report = report_generator.generate_comprehensive_report()
        
        # Generate HTML report
        html_content = report_generator.generate_html_report(report)
        html_path = 'data/mock_data/ai_report.html'
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        return jsonify({
            'success': True,
            'message': 'Report generated successfully',
            'report_path': html_path,
            'insights': report['overall_insights'][:5],
            'recommendations': report['priority_recommendations'][:5]
        })
    
    except Exception as e:
        logger.error(f"Error generating report: {str(e)}")
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/download_report')
def download_report():
    """
    Download AI report
    """
    try:
        report_path = 'data/mock_data/ai_report.html'
        if os.path.exists(report_path):
            return send_file(report_path, as_attachment=True, download_name='smart_farming_report.html')
        else:
            return jsonify({'error': 'Report not found'})
    
    except Exception as e:
        logger.error(f"Error downloading report: {str(e)}")
        return jsonify({'error': str(e)})

def background_data_updater():
    """
    Background thread for updating dashboard data
    """
    while True:
        try:
            data_manager.update_dashboard_data()
            time.sleep(data_manager.update_interval)
        except Exception as e:
            logger.error(f"Error in background data updater: {str(e)}")
            time.sleep(5)

def main():
    """
    Main function to run the Flask dashboard
    """
    logger.info("Starting Smart Farming Drones Dashboard")
    
    # Start background data updater
    updater_thread = threading.Thread(target=background_data_updater)
    updater_thread.daemon = True
    updater_thread.start()
    
    # Run Flask app
    print("\n" + "="*60)
    print("🚁 SMART FARMING DRONES DASHBOARD")
    print("="*60)
    print("Dashboard URL: http://localhost:5000")
    print("API Endpoints:")
    print("  - /api/drone_status - Current drone status")
    print("  - /api/field_data - Field zone data")
    print("  - /api/mission_stats - Mission statistics")
    print("  - /api/alerts - Real-time alerts")
    print("  - /api/start_mission - Start drone mission")
    print("  - /api/stop_mission - Stop drone mission")
    print("  - /api/generate_report - Generate AI report")
    print("="*60)
    
    app.run(debug=True, host='0.0.0.0', port=5000)

if __name__ == "__main__":
    main()
