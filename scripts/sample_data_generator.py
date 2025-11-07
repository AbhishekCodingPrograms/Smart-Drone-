"""
Smart Farming Drones - Sample Data Generator
============================================

This script generates sample datasets for testing and demonstration purposes.
Creates mock NDVI data, crop images, and sensor readings.

Author: Smart Farming AI Team
Date: 2024
"""

import os
import numpy as np
import pandas as pd
import cv2
import json
import random
from datetime import datetime, timedelta
from PIL import Image, ImageDraw
import matplotlib.pyplot as plt
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SampleDataGenerator:
    """
    Generate sample data for Smart Farming Drones project
    """
    
    def __init__(self):
        self.data_dir = "data"
        self.sample_images_dir = os.path.join(self.data_dir, "sample_images")
        self.mock_data_dir = os.path.join(self.data_dir, "mock_data")
        
        # Create directories
        os.makedirs(self.sample_images_dir, exist_ok=True)
        os.makedirs(self.mock_data_dir, exist_ok=True)
        
        logger.info("Sample Data Generator initialized")
    
    def generate_crop_images(self, num_images: int = 20):
        """
        Generate sample crop images with different health conditions
        """
        logger.info(f"Generating {num_images} sample crop images...")
        
        image_size = (224, 224)
        crop_types = ['Wheat', 'Rice', 'Corn', 'Soybean', 'Cotton']
        health_conditions = ['Healthy', 'Diseased', 'Pest-affected']
        
        for i in range(num_images):
            # Create base image
            img = np.random.randint(50, 200, (*image_size, 3), dtype=np.uint8)
            
            # Select random crop type and health condition
            crop_type = random.choice(crop_types)
            health_condition = random.choice(health_conditions)
            
            # Modify image based on health condition
            if health_condition == 'Healthy':
                # Make it more green (healthy)
                img[:, :, 1] = np.clip(img[:, :, 1] + 60, 0, 255)
                img[:, :, 0] = np.clip(img[:, :, 0] - 20, 0, 255)
                img[:, :, 2] = np.clip(img[:, :, 2] - 20, 0, 255)
                
                # Add some texture
                for _ in range(5):
                    x, y = random.randint(0, image_size[0]-20), random.randint(0, image_size[1]-20)
                    img[x:x+20, y:y+20] = np.clip(img[x:x+20, y:y+20] + 30, 0, 255)
            
            elif health_condition == 'Diseased':
                # Add brown/yellow spots (disease)
                img[:, :, 1] = np.clip(img[:, :, 1] + 30, 0, 255)
                img[:, :, 0] = np.clip(img[:, :, 0] + 40, 0, 255)
                
                # Add disease spots
                for _ in range(8):
                    x, y = random.randint(0, image_size[0]-15), random.randint(0, image_size[1]-15)
                    spot_color = [139, 69, 19]  # Brown
                    img[x:x+15, y:y+15] = spot_color
            
            else:  # Pest-affected
                # Add irregular patterns (pest damage)
                img[:, :, 1] = np.clip(img[:, :, 1] + 20, 0, 255)
                
                # Add irregular holes/patterns
                for _ in range(6):
                    x, y = random.randint(0, image_size[0]-25), random.randint(0, image_size[1]-25)
                    mask = np.random.random((25, 25)) > 0.7
                    img[x:x+25, y:y+25][mask] = [50, 50, 50]  # Dark spots
            
            # Add some noise for realism
            noise = np.random.normal(0, 10, img.shape)
            img = np.clip(img + noise, 0, 255).astype(np.uint8)
            
            # Save image
            filename = f"{crop_type.lower()}_{health_condition.lower()}_{i:02d}.jpg"
            filepath = os.path.join(self.sample_images_dir, filename)
            
            # Convert RGB to BGR for OpenCV
            img_bgr = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
            cv2.imwrite(filepath, img_bgr)
        
        logger.info(f"Generated {num_images} crop images in {self.sample_images_dir}")
    
    def generate_ndvi_data(self, width: int = 100, height: int = 100):
        """
        Generate mock NDVI data with realistic patterns
        """
        logger.info("Generating mock NDVI data...")
        
        # Create coordinate grids
        x = np.linspace(0, 10, width)
        y = np.linspace(0, 10, height)
        X, Y = np.meshgrid(x, y)
        
        # Create realistic vegetation patterns
        vegetation_pattern = (
            0.8 * np.exp(-((X-2)**2 + (Y-2)**2) / 1.5) +  # Dense vegetation area
            0.6 * np.exp(-((X-8)**2 + (Y-8)**2) / 2) +    # Moderate vegetation
            0.4 * np.exp(-((X-5)**2 + (Y-3)**2) / 3) +     # Sparse vegetation
            0.3 * np.exp(-((X-1)**2 + (Y-8)**2) / 4)      # Another sparse area
        )
        
        # Add some variation
        variation = np.random.normal(0, 0.1, (height, width))
        vegetation_pattern += variation
        
        # Generate NIR and Red bands
        # NIR is typically higher for vegetation
        nir_band = np.clip(vegetation_pattern * 255, 0, 255).astype(np.uint8)
        
        # Red band is typically lower for vegetation
        red_band = np.clip((1 - vegetation_pattern * 0.7) * 255, 0, 255).astype(np.uint8)
        
        # Calculate NDVI
        ndvi = (nir_band.astype(np.float32) - red_band.astype(np.float32)) / \
               (nir_band.astype(np.float32) + red_band.astype(np.float32) + 1e-10)
        ndvi = np.clip(ndvi, -1.0, 1.0)
        
        # Save NDVI data
        ndvi_data = {
            'nir_band': nir_band.tolist(),
            'red_band': red_band.tolist(),
            'ndvi': ndvi.tolist(),
            'metadata': {
                'width': width,
                'height': height,
                'generated_at': datetime.now().isoformat(),
                'description': 'Mock NDVI data for Smart Farming Drones'
            }
        }
        
        with open(os.path.join(self.mock_data_dir, 'ndvi_data.json'), 'w') as f:
            json.dump(ndvi_data, f, indent=2)
        
        # Create NDVI visualization
        plt.figure(figsize=(12, 4))
        
        plt.subplot(1, 3, 1)
        plt.imshow(nir_band, cmap='gray')
        plt.title('NIR Band')
        plt.colorbar()
        
        plt.subplot(1, 3, 2)
        plt.imshow(red_band, cmap='gray')
        plt.title('Red Band')
        plt.colorbar()
        
        plt.subplot(1, 3, 3)
        plt.imshow(ndvi, cmap='RdYlGn', vmin=-1, vmax=1)
        plt.title('NDVI Map')
        plt.colorbar()
        
        plt.tight_layout()
        plt.savefig(os.path.join(self.mock_data_dir, 'ndvi_visualization.png'), 
                   dpi=300, bbox_inches='tight')
        plt.close()
        
        logger.info("NDVI data generated and saved")
    
    def generate_sensor_data(self, num_readings: int = 1000):
        """
        Generate mock sensor data (temperature, humidity, soil moisture, etc.)
        """
        logger.info(f"Generating {num_readings} sensor readings...")
        
        # Generate time series
        start_time = datetime.now() - timedelta(days=7)
        timestamps = [start_time + timedelta(hours=i) for i in range(num_readings)]
        
        sensor_data = []
        
        for i, timestamp in enumerate(timestamps):
            # Simulate realistic sensor readings
            temperature = 25 + 10 * np.sin(i * 0.1) + np.random.normal(0, 2)
            humidity = 60 + 20 * np.sin(i * 0.05) + np.random.normal(0, 5)
            soil_moisture = 50 + 30 * np.sin(i * 0.03) + np.random.normal(0, 8)
            ph_level = 6.5 + 0.5 * np.sin(i * 0.02) + np.random.normal(0, 0.3)
            light_intensity = 500 + 300 * np.sin(i * 0.08) + np.random.normal(0, 50)
            
            # Add some correlation between sensors
            if soil_moisture < 30:
                temperature += 2  # Higher temp when soil is dry
                humidity -= 5    # Lower humidity when soil is dry
            
            reading = {
                'timestamp': timestamp.isoformat(),
                'temperature_c': round(temperature, 2),
                'humidity_percent': round(humidity, 2),
                'soil_moisture_percent': round(soil_moisture, 2),
                'ph_level': round(ph_level, 2),
                'light_intensity_lux': round(light_intensity, 2),
                'location': f"Zone_{i%25:02d}"  # 25 different zones
            }
            
            sensor_data.append(reading)
        
        # Save sensor data
        sensor_df = pd.DataFrame(sensor_data)
        sensor_df.to_csv(os.path.join(self.mock_data_dir, 'sensor_data.csv'), index=False)
        
        # Create sensor data visualization
        plt.figure(figsize=(15, 10))
        
        plt.subplot(2, 3, 1)
        plt.plot(sensor_df['temperature_c'])
        plt.title('Temperature Over Time')
        plt.ylabel('Temperature (°C)')
        
        plt.subplot(2, 3, 2)
        plt.plot(sensor_df['humidity_percent'])
        plt.title('Humidity Over Time')
        plt.ylabel('Humidity (%)')
        
        plt.subplot(2, 3, 3)
        plt.plot(sensor_df['soil_moisture_percent'])
        plt.title('Soil Moisture Over Time')
        plt.ylabel('Soil Moisture (%)')
        
        plt.subplot(2, 3, 4)
        plt.plot(sensor_df['ph_level'])
        plt.title('pH Level Over Time')
        plt.ylabel('pH Level')
        
        plt.subplot(2, 3, 5)
        plt.plot(sensor_df['light_intensity_lux'])
        plt.title('Light Intensity Over Time')
        plt.ylabel('Light Intensity (lux)')
        
        plt.subplot(2, 3, 6)
        plt.scatter(sensor_df['soil_moisture_percent'], sensor_df['temperature_c'], alpha=0.5)
        plt.title('Soil Moisture vs Temperature')
        plt.xlabel('Soil Moisture (%)')
        plt.ylabel('Temperature (°C)')
        
        plt.tight_layout()
        plt.savefig(os.path.join(self.mock_data_dir, 'sensor_data_visualization.png'), 
                   dpi=300, bbox_inches='tight')
        plt.close()
        
        logger.info("Sensor data generated and saved")
    
    def generate_weather_data(self, num_days: int = 30):
        """
        Generate mock weather data
        """
        logger.info(f"Generating {num_days} days of weather data...")
        
        weather_data = []
        
        for day in range(num_days):
            date = datetime.now() - timedelta(days=num_days-day)
            
            # Simulate seasonal patterns
            day_of_year = date.timetuple().tm_yday
            seasonal_temp = 20 + 15 * np.sin(2 * np.pi * day_of_year / 365)
            seasonal_rain = 5 + 10 * np.sin(2 * np.pi * (day_of_year - 100) / 365)
            
            # Daily weather
            daily_temp = seasonal_temp + np.random.normal(0, 3)
            daily_rainfall = max(0, seasonal_rain + np.random.normal(0, 2))
            daily_humidity = 60 + 20 * np.sin(day * 0.1) + np.random.normal(0, 5)
            wind_speed = 5 + 3 * np.random.random()
            
            weather_entry = {
                'date': date.strftime('%Y-%m-%d'),
                'temperature_avg': round(daily_temp, 1),
                'temperature_min': round(daily_temp - 5, 1),
                'temperature_max': round(daily_temp + 5, 1),
                'rainfall_mm': round(daily_rainfall, 1),
                'humidity_percent': round(daily_humidity, 1),
                'wind_speed_kmh': round(wind_speed, 1),
                'sunshine_hours': round(8 + 4 * np.random.random(), 1)
            }
            
            weather_data.append(weather_entry)
        
        # Save weather data
        weather_df = pd.DataFrame(weather_data)
        weather_df.to_csv(os.path.join(self.mock_data_dir, 'weather_data.csv'), index=False)
        
        logger.info("Weather data generated and saved")
    
    def generate_field_zones_data(self, num_zones: int = 25):
        """
        Generate field zones data with different crop types and conditions
        """
        logger.info(f"Generating {num_zones} field zones...")
        
        crop_types = ['Wheat', 'Rice', 'Corn', 'Soybean', 'Cotton', 'Tomato', 'Potato']
        health_statuses = ['Healthy', 'Diseased', 'Pest-affected']
        
        zones_data = []
        
        for i in range(num_zones):
            zone_id = f"Zone_{i:02d}"
            
            # Generate zone coordinates (assuming 500x500 meter field)
            x = random.uniform(0, 500)
            y = random.uniform(0, 500)
            
            zone_data = {
                'zone_id': zone_id,
                'center_x': round(x, 2),
                'center_y': round(y, 2),
                'width': 100.0,
                'height': 100.0,
                'crop_type': random.choice(crop_types),
                'health_status': random.choice(health_statuses),
                'ndvi_value': round(random.uniform(0.2, 0.8), 3),
                'moisture_level': round(random.uniform(30, 80), 1),
                'soil_ph': round(random.uniform(5.5, 7.5), 2),
                'nutrient_nitrogen': round(random.uniform(20, 80), 1),
                'nutrient_phosphorus': round(random.uniform(15, 60), 1),
                'nutrient_potassium': round(random.uniform(25, 70), 1),
                'last_sprayed': None,
                'planting_date': (datetime.now() - timedelta(days=random.randint(30, 120))).strftime('%Y-%m-%d'),
                'expected_harvest': (datetime.now() + timedelta(days=random.randint(30, 90))).strftime('%Y-%m-%d')
            }
            
            zones_data.append(zone_data)
        
        # Save zones data
        zones_df = pd.DataFrame(zones_data)
        zones_df.to_csv(os.path.join(self.mock_data_dir, 'field_zones.csv'), index=False)
        
        logger.info("Field zones data generated and saved")
    
    def generate_all_sample_data(self):
        """
        Generate all sample data
        """
        logger.info("Generating all sample data...")
        
        # Generate different types of sample data
        self.generate_crop_images(30)
        self.generate_ndvi_data(100, 100)
        self.generate_sensor_data(500)
        self.generate_weather_data(30)
        self.generate_field_zones_data(25)
        
        # Create a summary file
        summary = {
            'generated_at': datetime.now().isoformat(),
            'data_files': {
                'crop_images': f"{len(os.listdir(self.sample_images_dir))} images in {self.sample_images_dir}",
                'ndvi_data': f"NDVI data in {self.mock_data_dir}/ndvi_data.json",
                'sensor_data': f"Sensor readings in {self.mock_data_dir}/sensor_data.csv",
                'weather_data': f"Weather data in {self.mock_data_dir}/weather_data.csv",
                'field_zones': f"Field zones in {self.mock_data_dir}/field_zones.csv"
            },
            'description': 'Sample data for Smart Farming Drones AI project demonstration'
        }
        
        with open(os.path.join(self.mock_data_dir, 'data_summary.json'), 'w') as f:
            json.dump(summary, f, indent=2)
        
        logger.info("All sample data generated successfully!")
        logger.info(f"Data saved in: {self.data_dir}")
        
        return summary

def main():
    """
    Main function to generate sample data
    """
    logger.info("Starting Smart Farming Drones - Sample Data Generation")
    
    # Initialize generator
    generator = SampleDataGenerator()
    
    # Generate all sample data
    summary = generator.generate_all_sample_data()
    
    print("\n" + "="*60)
    print("SAMPLE DATA GENERATION COMPLETED")
    print("="*60)
    print(f"Generated at: {summary['generated_at']}")
    print("\nData Files:")
    for file_type, description in summary['data_files'].items():
        print(f"  - {file_type}: {description}")
    
    print(f"\nData directory: {generator.data_dir}")
    print("Sample data ready for testing and demonstration!")

if __name__ == "__main__":
    main()
