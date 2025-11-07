"""
Database Manager for Smart Farming Drones
Handles all database operations and data persistence
"""

import sqlite3
import json
import os
from datetime import datetime
from typing import List, Dict, Optional, Tuple
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DatabaseManager:
    """Manages all database operations for the smart farming system"""
    
    def __init__(self, db_path: str = "data/farming_drones.db"):
        """Initialize database connection"""
        self.db_path = db_path
        self.ensure_database_exists()
    
    def ensure_database_exists(self):
        """Create database and tables if they don't exist"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        # Read schema file
        schema_path = os.path.join(os.path.dirname(__file__), 'schema.sql')
        if os.path.exists(schema_path):
            with open(schema_path, 'r') as f:
                schema = f.read()
            
            conn = self.get_connection()
            try:
                conn.executescript(schema)
                conn.commit()
                logger.info("Database initialized successfully")
            except Exception as e:
                logger.error(f"Error initializing database: {e}")
            finally:
                conn.close()
    
    def get_connection(self) -> sqlite3.Connection:
        """Get database connection"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Return rows as dictionaries
        return conn
    
    # ============================================
    # MISSION OPERATIONS
    # ============================================
    
    def create_mission(self, mission_name: str, field_area: float = None) -> int:
        """Create a new mission"""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO missions (mission_name, start_time, field_area, status)
                VALUES (?, ?, ?, 'in_progress')
            """, (mission_name, datetime.now(), field_area))
            conn.commit()
            mission_id = cursor.lastrowid
            logger.info(f"Created mission {mission_id}: {mission_name}")
            return mission_id
        finally:
            conn.close()
    
    def update_mission(self, mission_id: int, **kwargs):
        """Update mission details"""
        conn = self.get_connection()
        try:
            set_clause = ", ".join([f"{k} = ?" for k in kwargs.keys()])
            values = list(kwargs.values()) + [mission_id]
            
            conn.execute(f"""
                UPDATE missions SET {set_clause} WHERE id = ?
            """, values)
            conn.commit()
            logger.info(f"Updated mission {mission_id}")
        finally:
            conn.close()
    
    def end_mission(self, mission_id: int, success_rate: float = None):
        """End a mission"""
        self.update_mission(
            mission_id,
            end_time=datetime.now(),
            status='completed',
            success_rate=success_rate
        )
    
    def get_mission(self, mission_id: int) -> Optional[Dict]:
        """Get mission details"""
        conn = self.get_connection()
        try:
            cursor = conn.execute("SELECT * FROM missions WHERE id = ?", (mission_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
        finally:
            conn.close()
    
    def get_recent_missions(self, limit: int = 10) -> List[Dict]:
        """Get recent missions"""
        conn = self.get_connection()
        try:
            cursor = conn.execute("""
                SELECT * FROM missions 
                ORDER BY start_time DESC 
                LIMIT ?
            """, (limit,))
            return [dict(row) for row in cursor.fetchall()]
        finally:
            conn.close()
    
    # ============================================
    # FIELD ZONE OPERATIONS
    # ============================================
    
    def save_zone_scan(self, mission_id: int, zone_data: Dict) -> int:
        """Save field zone scan data"""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO field_zones (
                    mission_id, zone_id, latitude, longitude, x_coordinate, y_coordinate,
                    scan_time, health_status, health_score, ndvi_value, ndvi_category,
                    moisture_level, moisture_status, disease_detected, disease_type,
                    disease_severity, disease_confidence, pest_detected, pest_type,
                    pest_severity, spray_required, spray_priority, spray_amount, image_path
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                mission_id,
                zone_data.get('zone_id'),
                zone_data.get('latitude'),
                zone_data.get('longitude'),
                zone_data.get('x_coordinate'),
                zone_data.get('y_coordinate'),
                zone_data.get('scan_time', datetime.now()),
                zone_data.get('health_status'),
                zone_data.get('health_score'),
                zone_data.get('ndvi_value'),
                zone_data.get('ndvi_category'),
                zone_data.get('moisture_level'),
                zone_data.get('moisture_status'),
                zone_data.get('disease_detected', False),
                zone_data.get('disease_type'),
                zone_data.get('disease_severity'),
                zone_data.get('disease_confidence'),
                zone_data.get('pest_detected', False),
                zone_data.get('pest_type'),
                zone_data.get('pest_severity'),
                zone_data.get('spray_required', False),
                zone_data.get('spray_priority'),
                zone_data.get('spray_amount'),
                zone_data.get('image_path')
            ))
            conn.commit()
            return cursor.lastrowid
        finally:
            conn.close()
    
    def get_mission_zones(self, mission_id: int) -> List[Dict]:
        """Get all zones for a mission"""
        conn = self.get_connection()
        try:
            cursor = conn.execute("""
                SELECT * FROM field_zones 
                WHERE mission_id = ? 
                ORDER BY scan_time DESC
            """, (mission_id,))
            return [dict(row) for row in cursor.fetchall()]
        finally:
            conn.close()
    
    def get_zones_by_health_status(self, mission_id: int, status: str) -> List[Dict]:
        """Get zones filtered by health status"""
        conn = self.get_connection()
        try:
            cursor = conn.execute("""
                SELECT * FROM field_zones 
                WHERE mission_id = ? AND health_status = ?
                ORDER BY scan_time DESC
            """, (mission_id, status))
            return [dict(row) for row in cursor.fetchall()]
        finally:
            conn.close()
    
    def get_zones_requiring_spray(self, mission_id: int) -> List[Dict]:
        """Get zones that require spraying"""
        conn = self.get_connection()
        try:
            cursor = conn.execute("""
                SELECT * FROM field_zones 
                WHERE mission_id = ? AND spray_required = 1 AND spray_applied = 0
                ORDER BY spray_priority DESC, scan_time DESC
            """, (mission_id,))
            return [dict(row) for row in cursor.fetchall()]
        finally:
            conn.close()
    
    # ============================================
    # IMAGE OPERATIONS
    # ============================================
    
    def save_scan_image(self, zone_id: int, mission_id: int, image_data: Dict) -> int:
        """Save scan image metadata"""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO scan_images (
                    zone_id, mission_id, image_type, file_path, file_size,
                    width, height, capture_time, camera_settings
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                zone_id,
                mission_id,
                image_data.get('image_type', 'rgb'),
                image_data['file_path'],
                image_data.get('file_size'),
                image_data.get('width'),
                image_data.get('height'),
                image_data.get('capture_time', datetime.now()),
                json.dumps(image_data.get('camera_settings', {}))
            ))
            conn.commit()
            return cursor.lastrowid
        finally:
            conn.close()
    
    # ============================================
    # AI ANALYSIS OPERATIONS
    # ============================================
    
    def save_ai_analysis(self, zone_id: int, analysis_data: Dict) -> int:
        """Save AI analysis results"""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO ai_analysis (
                    zone_id, image_id, model_name, model_version, prediction_class,
                    confidence_score, bounding_boxes, disease_probability,
                    healthy_probability, pest_probability, processing_time,
                    analysis_timestamp, recommendation, action_required
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                zone_id,
                analysis_data.get('image_id'),
                analysis_data.get('model_name'),
                analysis_data.get('model_version'),
                analysis_data.get('prediction_class'),
                analysis_data.get('confidence_score'),
                json.dumps(analysis_data.get('bounding_boxes', [])),
                analysis_data.get('disease_probability'),
                analysis_data.get('healthy_probability'),
                analysis_data.get('pest_probability'),
                analysis_data.get('processing_time'),
                analysis_data.get('analysis_timestamp', datetime.now()),
                analysis_data.get('recommendation'),
                analysis_data.get('action_required')
            ))
            conn.commit()
            return cursor.lastrowid
        finally:
            conn.close()
    
    # ============================================
    # SPRAY OPERATIONS
    # ============================================
    
    def record_spray_action(self, mission_id: int, zone_id: int, spray_data: Dict) -> int:
        """Record a spray action"""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO spray_actions (
                    mission_id, zone_id, spray_timestamp, spray_amount,
                    spray_type, spray_duration, success, notes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                mission_id,
                zone_id,
                spray_data.get('timestamp', datetime.now()),
                spray_data.get('amount'),
                spray_data.get('type'),
                spray_data.get('duration'),
                spray_data.get('success', True),
                spray_data.get('notes')
            ))
            conn.commit()
            
            # Update zone spray status
            conn.execute("""
                UPDATE field_zones 
                SET spray_applied = 1, spray_timestamp = ?
                WHERE id = ?
            """, (datetime.now(), zone_id))
            conn.commit()
            
            return cursor.lastrowid
        finally:
            conn.close()
    
    # ============================================
    # TELEMETRY OPERATIONS
    # ============================================
    
    def save_telemetry(self, mission_id: int, telemetry_data: Dict):
        """Save drone telemetry data"""
        conn = self.get_connection()
        try:
            conn.execute("""
                INSERT INTO drone_telemetry (
                    mission_id, timestamp, battery_level, altitude, speed,
                    latitude, longitude, heading, temperature, signal_strength,
                    gps_satellites, status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                mission_id,
                telemetry_data.get('timestamp', datetime.now()),
                telemetry_data.get('battery_level'),
                telemetry_data.get('altitude'),
                telemetry_data.get('speed'),
                telemetry_data.get('latitude'),
                telemetry_data.get('longitude'),
                telemetry_data.get('heading'),
                telemetry_data.get('temperature'),
                telemetry_data.get('signal_strength'),
                telemetry_data.get('gps_satellites'),
                telemetry_data.get('status')
            ))
            conn.commit()
        finally:
            conn.close()
    
    # ============================================
    # ALERT OPERATIONS
    # ============================================
    
    def create_alert(self, mission_id: int, alert_type: str, severity: str, message: str) -> int:
        """Create a system alert"""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO alerts (
                    mission_id, alert_type, severity, message, alert_time
                ) VALUES (?, ?, ?, ?, ?)
            """, (mission_id, alert_type, severity, message, datetime.now()))
            conn.commit()
            return cursor.lastrowid
        finally:
            conn.close()
    
    def get_active_alerts(self, mission_id: int = None) -> List[Dict]:
        """Get active alerts"""
        conn = self.get_connection()
        try:
            if mission_id:
                cursor = conn.execute("""
                    SELECT * FROM alerts 
                    WHERE mission_id = ? AND resolved = 0
                    ORDER BY alert_time DESC
                """, (mission_id,))
            else:
                cursor = conn.execute("""
                    SELECT * FROM alerts 
                    WHERE resolved = 0
                    ORDER BY alert_time DESC
                """)
            return [dict(row) for row in cursor.fetchall()]
        finally:
            conn.close()
    
    # ============================================
    # ANALYTICS OPERATIONS
    # ============================================
    
    def generate_mission_summary(self, mission_id: int) -> Dict:
        """Generate comprehensive mission summary"""
        conn = self.get_connection()
        try:
            # Get mission details
            mission = self.get_mission(mission_id)
            if not mission:
                return {}
            
            # Get zone statistics
            cursor = conn.execute("""
                SELECT 
                    COUNT(*) as total_zones,
                    SUM(CASE WHEN health_status = 'healthy' THEN 1 ELSE 0 END) as healthy,
                    SUM(CASE WHEN health_status = 'borderline' THEN 1 ELSE 0 END) as borderline,
                    SUM(CASE WHEN health_status = 'diseased' THEN 1 ELSE 0 END) as diseased,
                    SUM(CASE WHEN health_status = 'critical' THEN 1 ELSE 0 END) as critical,
                    SUM(CASE WHEN disease_detected = 1 THEN 1 ELSE 0 END) as disease_count,
                    SUM(CASE WHEN spray_required = 1 THEN 1 ELSE 0 END) as spray_required,
                    SUM(CASE WHEN spray_applied = 1 THEN 1 ELSE 0 END) as spray_applied,
                    AVG(ndvi_value) as avg_ndvi,
                    AVG(moisture_level) as avg_moisture,
                    AVG(health_score) as avg_health_score
                FROM field_zones
                WHERE mission_id = ?
            """, (mission_id,))
            
            stats = dict(cursor.fetchone())
            
            # Get spray statistics
            cursor = conn.execute("""
                SELECT 
                    COUNT(*) as total_sprays,
                    SUM(spray_amount) as total_spray_used,
                    AVG(spray_duration) as avg_duration
                FROM spray_actions
                WHERE mission_id = ?
            """, (mission_id,))
            
            spray_stats = dict(cursor.fetchone())
            
            return {
                'mission': mission,
                'zone_statistics': stats,
                'spray_statistics': spray_stats
            }
        finally:
            conn.close()
    
    def save_analytics_summary(self, mission_id: int, summary_data: Dict):
        """Save analytics summary"""
        conn = self.get_connection()
        try:
            conn.execute("""
                INSERT INTO analytics_summary (
                    mission_id, summary_date, total_area_scanned, zones_scanned,
                    zones_healthy, zones_borderline, zones_diseased, zones_critical,
                    total_spray_used, zones_sprayed, spray_efficiency,
                    total_diseases_detected, disease_types, avg_disease_severity,
                    avg_battery_drain, total_flight_time, avg_ndvi, avg_moisture
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                mission_id,
                summary_data.get('summary_date', datetime.now().date()),
                summary_data.get('total_area_scanned'),
                summary_data.get('zones_scanned'),
                summary_data.get('zones_healthy'),
                summary_data.get('zones_borderline'),
                summary_data.get('zones_diseased'),
                summary_data.get('zones_critical'),
                summary_data.get('total_spray_used'),
                summary_data.get('zones_sprayed'),
                summary_data.get('spray_efficiency'),
                summary_data.get('total_diseases_detected'),
                json.dumps(summary_data.get('disease_types', [])),
                summary_data.get('avg_disease_severity'),
                summary_data.get('avg_battery_drain'),
                summary_data.get('total_flight_time'),
                summary_data.get('avg_ndvi'),
                summary_data.get('avg_moisture')
            ))
            conn.commit()
        finally:
            conn.close()
    
    # ============================================
    # QUERY OPERATIONS
    # ============================================
    
    def get_dashboard_stats(self) -> Dict:
        """Get overall dashboard statistics"""
        conn = self.get_connection()
        try:
            stats = {}
            
            # Total missions
            cursor = conn.execute("SELECT COUNT(*) as total FROM missions")
            stats['total_missions'] = cursor.fetchone()['total']
            
            # Active missions
            cursor = conn.execute("SELECT COUNT(*) as active FROM missions WHERE status = 'in_progress'")
            stats['active_missions'] = cursor.fetchone()['active']
            
            # Total zones scanned
            cursor = conn.execute("SELECT COUNT(*) as total FROM field_zones")
            stats['total_zones'] = cursor.fetchone()['total']
            
            # Disease zones
            cursor = conn.execute("SELECT COUNT(*) as diseased FROM field_zones WHERE disease_detected = 1")
            stats['diseased_zones'] = cursor.fetchone()['diseased']
            
            # Today's statistics
            cursor = conn.execute("""
                SELECT COUNT(*) as today_scans 
                FROM field_zones 
                WHERE DATE(scan_time) = DATE('now')
            """)
            stats['today_scans'] = cursor.fetchone()['today_scans']
            
            return stats
        finally:
            conn.close()


# Global database instance
db = DatabaseManager()
