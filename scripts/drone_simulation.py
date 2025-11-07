"""
Smart Farming Drones - Drone Control Simulation
===============================================

This module simulates drone operations including automated scanning,
crop health analysis, and intelligent spraying decisions for precision agriculture.

Author: Smart Farming AI Team
Date: 2024
"""

import os
import time
import random
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import json
import logging
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
import threading
import queue

# Import our custom modules
from scripts.image_processing import ImageProcessor, NDVIAnalyzer

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class DronePosition:
    """Drone position coordinates"""
    x: float
    y: float
    altitude: float
    timestamp: datetime

@dataclass
class FieldZone:
    """Agricultural field zone"""
    zone_id: str
    center_x: float
    center_y: float
    width: float
    height: float
    crop_type: str
    health_status: str
    ndvi_value: float
    moisture_level: float
    last_sprayed: Optional[datetime] = None

@dataclass
class SprayingAction:
    """Spraying action record"""
    action_id: str
    zone_id: str
    timestamp: datetime
    action_type: str  # 'pesticide', 'fertilizer', 'water'
    quantity: float
    success: bool
    reason: str

class DroneSimulator:
    """
    Main drone simulation class
    """
    
    def __init__(self, field_width: float = 1000, field_height: float = 1000):
        self.field_width = field_width
        self.field_height = field_height
        self.current_position = DronePosition(0, 0, 50, datetime.now())
        self.battery_level = 100.0
        self.spray_tank_capacity = 10.0  # liters
        self.current_spray_level = 10.0
        self.flight_speed = 5.0  # m/s
        self.scanning_altitude = 30.0
        self.spraying_altitude = 5.0
        
        # Initialize components
        self.image_processor = ImageProcessor()
        self.ndvi_analyzer = NDVIAnalyzer()
        
        # Field zones
        self.field_zones = self._create_field_zones()
        
        # Action history
        self.action_history = []
        self.flight_log = []
        
        # Simulation state
        self.is_flying = False
        self.is_scanning = False
        self.is_spraying = False
        self.simulation_running = False
        
        # Data collection
        self.scan_data = []
        self.spraying_data = []
        
        logger.info("Drone simulator initialized")
    
    def _create_field_zones(self) -> List[FieldZone]:
        """
        Create field zones for simulation
        """
        zones = []
        zone_size = 100  # 100x100 meter zones
        zones_x = int(self.field_width / zone_size)
        zones_y = int(self.field_height / zone_size)
        
        crop_types = ['Wheat', 'Rice', 'Corn', 'Soybean', 'Cotton']
        
        for i in range(zones_x):
            for j in range(zones_y):
                zone_id = f"Zone_{i}_{j}"
                center_x = i * zone_size + zone_size / 2
                center_y = j * zone_size + zone_size / 2
                
                # Randomize initial conditions
                health_status = random.choice(['Healthy', 'Diseased', 'Pest-affected'])
                ndvi_value = random.uniform(0.2, 0.8)
                moisture_level = random.uniform(30, 80)
                
                zone = FieldZone(
                    zone_id=zone_id,
                    center_x=center_x,
                    center_y=center_y,
                    width=zone_size,
                    height=zone_size,
                    crop_type=random.choice(crop_types),
                    health_status=health_status,
                    ndvi_value=ndvi_value,
                    moisture_level=moisture_level
                )
                zones.append(zone)
        
        logger.info(f"Created {len(zones)} field zones")
        return zones
    
    def takeoff(self) -> bool:
        """
        Simulate drone takeoff
        """
        if self.is_flying:
            logger.warning("Drone is already flying")
            return False
        
        logger.info("Drone taking off...")
        time.sleep(1)  # Simulate takeoff time
        
        self.is_flying = True
        self.current_position.altitude = self.scanning_altitude
        self.current_position.timestamp = datetime.now()
        
        self._log_flight_event("TAKEOFF", "Drone took off successfully")
        logger.info("Drone is now airborne")
        return True
    
    def land(self) -> bool:
        """
        Simulate drone landing
        """
        if not self.is_flying:
            logger.warning("Drone is not flying")
            return False
        
        logger.info("Drone landing...")
        time.sleep(2)  # Simulate landing time
        
        self.is_flying = False
        self.is_scanning = False
        self.is_spraying = False
        self.current_position.altitude = 0
        
        self._log_flight_event("LANDING", "Drone landed successfully")
        logger.info("Drone has landed")
        return True
    
    def fly_to_position(self, target_x: float, target_y: float, altitude: float = None) -> bool:
        """
        Fly to a specific position
        """
        if not self.is_flying:
            logger.warning("Drone must be flying to move")
            return False
        
        if altitude is None:
            altitude = self.current_position.altitude
        
        # Calculate distance and flight time
        distance = np.sqrt((target_x - self.current_position.x)**2 + 
                          (target_y - self.current_position.y)**2)
        flight_time = distance / self.flight_speed
        
        logger.info(f"Flying to position ({target_x:.1f}, {target_y:.1f}) - Distance: {distance:.1f}m")
        
        # Simulate flight time
        time.sleep(min(flight_time, 2))  # Cap simulation time
        
        # Update position
        self.current_position.x = target_x
        self.current_position.y = target_y
        self.current_position.altitude = altitude
        self.current_position.timestamp = datetime.now()
        
        # Consume battery
        self.battery_level -= distance * 0.01  # 1% per 100m
        self.battery_level = max(0, self.battery_level)
        
        self._log_flight_event("MOVEMENT", f"Moved to ({target_x:.1f}, {target_y:.1f})")
        return True
    
    def scan_zone(self, zone: FieldZone) -> Dict:
        """
        Scan a field zone for crop health analysis
        """
        if not self.is_flying:
            logger.warning("Drone must be flying to scan")
            return {}
        
        logger.info(f"Scanning zone {zone.zone_id}...")
        
        # Fly to zone center
        self.fly_to_position(zone.center_x, zone.center_y, self.scanning_altitude)
        
        # Simulate scanning time
        time.sleep(1)
        
        # Generate mock image data for analysis
        scan_result = self._simulate_zone_scanning(zone)
        
        # Update zone data
        zone.health_status = scan_result['crop_health']['status']
        zone.ndvi_value = scan_result['ndvi_analysis']['mean_ndvi']
        zone.moisture_level = random.uniform(30, 80)  # Simulate moisture sensor
        
        # Store scan data
        scan_data = {
            'zone_id': zone.zone_id,
            'timestamp': datetime.now(),
            'position': (zone.center_x, zone.center_y),
            'health_status': zone.health_status,
            'ndvi_value': zone.ndvi_value,
            'moisture_level': zone.moisture_level,
            'scan_result': scan_result
        }
        self.scan_data.append(scan_data)
        
        self._log_flight_event("SCAN", f"Scanned zone {zone.zone_id} - Status: {zone.health_status}")
        
        return scan_result
    
    def _simulate_zone_scanning(self, zone: FieldZone) -> Dict:
        """
        Simulate scanning process with realistic data
        """
        # Simulate some randomness in health detection
        health_variation = random.uniform(-0.2, 0.2)
        
        # Generate mock scan result
        scan_result = {
            'crop_health': {
                'status': zone.health_status,
                'confidence': random.uniform(0.7, 0.95),
                'health_score': max(0, min(1, zone.ndvi_value + health_variation)),
                'recommendations': self._get_scan_recommendations(zone)
            },
            'ndvi_analysis': {
                'mean_ndvi': zone.ndvi_value,
                'health_status': 'Good' if zone.ndvi_value > 0.5 else 'Fair',
                'vegetation_percentage': zone.ndvi_value * 100,
                'recommendations': []
            },
            'overall_assessment': {
                'overall_score': zone.ndvi_value,
                'status': 'Good' if zone.ndvi_value > 0.5 else 'Fair',
                'priority_actions': []
            }
        }
        
        return scan_result
    
    def _get_scan_recommendations(self, zone: FieldZone) -> List[str]:
        """
        Get recommendations based on zone analysis
        """
        recommendations = []
        
        if zone.health_status == 'Diseased':
            recommendations.append("Apply fungicide treatment")
        elif zone.health_status == 'Pest-affected':
            recommendations.append("Apply pesticide treatment")
        
        if zone.ndvi_value < 0.4:
            recommendations.append("Increase irrigation")
        
        if zone.moisture_level < 40:
            recommendations.append("Water stress detected")
        
        return recommendations
    
    def decide_spraying_action(self, zone: FieldZone) -> Optional[SprayingAction]:
        """
        AI-powered decision making for spraying actions
        """
        # Check if spraying is needed
        needs_spraying = False
        action_type = None
        quantity = 0.0
        reason = ""
        
        # Decision logic based on health status and conditions
        if zone.health_status == 'Diseased':
            needs_spraying = True
            action_type = 'pesticide'
            quantity = 0.5  # liters
            reason = "Disease detected"
        elif zone.health_status == 'Pest-affected':
            needs_spraying = True
            action_type = 'pesticide'
            quantity = 0.3  # liters
            reason = "Pest infestation detected"
        elif zone.ndvi_value < 0.3 and zone.moisture_level > 50:
            needs_spraying = True
            action_type = 'fertilizer'
            quantity = 0.2  # liters
            reason = "Nutrient deficiency detected"
        elif zone.moisture_level < 30:
            needs_spraying = True
            action_type = 'water'
            quantity = 1.0  # liters
            reason = "Water stress detected"
        
        # Check if enough spray capacity
        if needs_spraying and self.current_spray_level < quantity:
            logger.warning(f"Insufficient spray capacity: {self.current_spray_level:.1f}L < {quantity:.1f}L")
            return None
        
        # Check if recently sprayed (avoid over-spraying)
        if zone.last_sprayed and (datetime.now() - zone.last_sprayed) < timedelta(hours=24):
            logger.info(f"Zone {zone.zone_id} recently sprayed, skipping")
            return None
        
        if needs_spraying:
            action = SprayingAction(
                action_id=f"SPRAY_{zone.zone_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                zone_id=zone.zone_id,
                timestamp=datetime.now(),
                action_type=action_type,
                quantity=quantity,
                success=False,
                reason=reason
            )
            return action
        
        return None
    
    def execute_spraying(self, action: SprayingAction) -> bool:
        """
        Execute spraying action
        """
        if not self.is_flying:
            logger.warning("Drone must be flying to spray")
            return False
        
        # Find the zone
        zone = next((z for z in self.field_zones if z.zone_id == action.zone_id), None)
        if not zone:
            logger.error(f"Zone {action.zone_id} not found")
            return False
        
        logger.info(f"Executing spraying action: {action.action_type} ({action.quantity}L) in {action.zone_id}")
        
        # Fly to zone
        self.fly_to_position(zone.center_x, zone.center_y, self.spraying_altitude)
        
        # Simulate spraying time
        spraying_time = action.quantity * 2  # 2 seconds per liter
        time.sleep(min(spraying_time, 3))  # Cap simulation time
        
        # Update spray tank level
        self.current_spray_level -= action.quantity
        self.current_spray_level = max(0, self.current_spray_level)
        
        # Update zone
        zone.last_sprayed = datetime.now()
        
        # Mark action as successful
        action.success = True
        
        # Store spraying data
        self.spraying_data.append({
            'action_id': action.action_id,
            'zone_id': action.zone_id,
            'timestamp': action.timestamp,
            'action_type': action.action_type,
            'quantity': action.quantity,
            'position': (zone.center_x, zone.center_y),
            'success': action.success
        })
        
        self.action_history.append(action)
        
        self._log_flight_event("SPRAYING", f"Sprayed {action.action_type} in {action.zone_id}")
        
        logger.info(f"Spraying completed successfully")
        return True
    
    def autonomous_mission(self, mission_duration: int = 300) -> Dict:
        """
        Run autonomous mission for specified duration (seconds)
        """
        logger.info(f"Starting autonomous mission for {mission_duration} seconds")
        
        start_time = datetime.now()
        end_time = start_time + timedelta(seconds=mission_duration)
        
        mission_stats = {
            'start_time': start_time,
            'end_time': end_time,
            'zones_scanned': 0,
            'zones_sprayed': 0,
            'total_spray_used': 0.0,
            'battery_consumed': 0.0,
            'actions_taken': []
        }
        
        initial_battery = self.battery_level
        initial_spray = self.current_spray_level
        
        # Takeoff
        if not self.takeoff():
            return mission_stats
        
        try:
            while datetime.now() < end_time and self.battery_level > 20:
                # Select random zone for scanning
                zone = random.choice(self.field_zones)
                
                # Scan zone
                scan_result = self.scan_zone(zone)
                mission_stats['zones_scanned'] += 1
                
                # Decide on spraying action
                action = self.decide_spraying_action(zone)
                
                if action:
                    # Execute spraying
                    if self.execute_spraying(action):
                        mission_stats['zones_sprayed'] += 1
                        mission_stats['total_spray_used'] += action.quantity
                        mission_stats['actions_taken'].append({
                            'action_id': action.action_id,
                            'zone_id': action.zone_id,
                            'action_type': action.action_type,
                            'quantity': action.quantity,
                            'reason': action.reason
                        })
                
                # Check if need to return for refill
                if self.current_spray_level < 1.0:
                    logger.info("Low spray capacity, returning to base")
                    break
                
                # Small delay between actions
                time.sleep(0.5)
        
        except KeyboardInterrupt:
            logger.info("Mission interrupted by user")
        
        finally:
            # Land
            self.land()
        
        # Calculate final stats
        mission_stats['battery_consumed'] = initial_battery - self.battery_level
        mission_stats['spray_remaining'] = self.current_spray_level
        mission_stats['mission_duration'] = (datetime.now() - start_time).total_seconds()
        
        logger.info("Autonomous mission completed")
        logger.info(f"Zones scanned: {mission_stats['zones_scanned']}")
        logger.info(f"Zones sprayed: {mission_stats['zones_sprayed']}")
        logger.info(f"Spray used: {mission_stats['total_spray_used']:.1f}L")
        
        return mission_stats
    
    def _log_flight_event(self, event_type: str, description: str):
        """
        Log flight events
        """
        event = {
            'timestamp': datetime.now(),
            'event_type': event_type,
            'description': description,
            'position': (self.current_position.x, self.current_position.y),
            'altitude': self.current_position.altitude,
            'battery_level': self.battery_level,
            'spray_level': self.current_spray_level
        }
        self.flight_log.append(event)
    
    def get_status(self) -> Dict:
        """
        Get current drone status
        """
        return {
            'position': {
                'x': self.current_position.x,
                'y': self.current_position.y,
                'altitude': self.current_position.altitude
            },
            'battery_level': self.battery_level,
            'spray_level': self.current_spray_level,
            'is_flying': self.is_flying,
            'is_scanning': self.is_scanning,
            'is_spraying': self.is_spraying,
            'field_zones': len(self.field_zones),
            'zones_scanned': len(self.scan_data),
            'actions_taken': len(self.action_history)
        }
    
    def generate_mission_report(self) -> Dict:
        """
        Generate comprehensive mission report
        """
        # Analyze scan data
        health_distribution = {}
        ndvi_values = []
        
        for scan in self.scan_data:
            status = scan['health_status']
            health_distribution[status] = health_distribution.get(status, 0) + 1
            ndvi_values.append(scan['ndvi_value'])
        
        # Analyze spraying data
        spray_summary = {}
        for spray in self.spraying_data:
            action_type = spray['action_type']
            if action_type not in spray_summary:
                spray_summary[action_type] = {'count': 0, 'total_quantity': 0}
            spray_summary[action_type]['count'] += 1
            spray_summary[action_type]['total_quantity'] += spray['quantity']
        
        report = {
            'mission_summary': {
                'total_zones_scanned': len(self.scan_data),
                'total_actions_taken': len(self.spraying_data),
                'mission_duration': len(self.flight_log),
                'battery_consumed': 100 - self.battery_level,
                'spray_consumed': 10 - self.current_spray_level
            },
            'crop_health_analysis': {
                'health_distribution': health_distribution,
                'average_ndvi': np.mean(ndvi_values) if ndvi_values else 0,
                'healthy_percentage': (health_distribution.get('Healthy', 0) / len(self.scan_data) * 100) if self.scan_data else 0
            },
            'spraying_analysis': spray_summary,
            'recommendations': self._generate_recommendations(health_distribution, ndvi_values),
            'timestamp': datetime.now()
        }
        
        return report
    
    def _generate_recommendations(self, health_distribution: Dict, ndvi_values: List[float]) -> List[str]:
        """
        Generate recommendations based on mission data
        """
        recommendations = []
        
        total_scanned = sum(health_distribution.values())
        if total_scanned > 0:
            diseased_percentage = (health_distribution.get('Diseased', 0) / total_scanned) * 100
            pest_percentage = (health_distribution.get('Pest-affected', 0) / total_scanned) * 100
            
            if diseased_percentage > 30:
                recommendations.append("High disease prevalence detected - consider field-wide fungicide treatment")
            
            if pest_percentage > 20:
                recommendations.append("Significant pest activity - implement integrated pest management")
            
            if ndvi_values:
                avg_ndvi = np.mean(ndvi_values)
                if avg_ndvi < 0.4:
                    recommendations.append("Low vegetation health - improve irrigation and fertilization")
        
        return recommendations

def main():
    """
    Main function for testing drone simulation
    """
    logger.info("Starting Smart Farming Drones - Drone Simulation")
    
    # Initialize drone simulator
    drone = DroneSimulator(field_width=500, field_height=500)
    
    print("\n" + "="*60)
    print("SMART FARMING DRONE SIMULATION")
    print("="*60)
    
    # Show initial status
    status = drone.get_status()
    print(f"Initial Status:")
    print(f"  Position: ({status['position']['x']:.1f}, {status['position']['y']:.1f})")
    print(f"  Battery: {status['battery_level']:.1f}%")
    print(f"  Spray Tank: {status['spray_level']:.1f}L")
    print(f"  Field Zones: {status['field_zones']}")
    
    # Run autonomous mission
    print(f"\nStarting autonomous mission...")
    mission_stats = drone.autonomous_mission(mission_duration=60)  # 1 minute mission
    
    # Show mission results
    print(f"\nMission Results:")
    print(f"  Zones Scanned: {mission_stats['zones_scanned']}")
    print(f"  Zones Sprayed: {mission_stats['zones_sprayed']}")
    print(f"  Spray Used: {mission_stats['total_spray_used']:.1f}L")
    print(f"  Battery Consumed: {mission_stats['battery_consumed']:.1f}%")
    print(f"  Mission Duration: {mission_stats['mission_duration']:.1f}s")
    
    # Generate and show report
    report = drone.generate_mission_report()
    print(f"\nMission Report:")
    print(f"  Healthy Crops: {report['crop_health_analysis']['healthy_percentage']:.1f}%")
    print(f"  Average NDVI: {report['crop_health_analysis']['average_ndvi']:.2f}")
    
    print(f"\nRecommendations:")
    for rec in report['recommendations']:
        print(f"  - {rec}")
    
    # Save mission data
    os.makedirs('data/mock_data', exist_ok=True)
    
    # Save scan data
    scan_df = pd.DataFrame(drone.scan_data)
    scan_df.to_csv('data/mock_data/scan_data.csv', index=False)
    
    # Save spraying data
    spray_df = pd.DataFrame(drone.spraying_data)
    spray_df.to_csv('data/mock_data/spraying_data.csv', index=False)
    
    # Save mission report
    with open('data/mock_data/mission_report.json', 'w') as f:
        json.dump(report, f, indent=2, default=str)
    
    print(f"\nMission data saved to data/mock_data/")
    print("Drone simulation completed successfully!")

if __name__ == "__main__":
    main()
