"""
Smart Farming Drones - Image Processing Module
==============================================

This module handles image preprocessing, crop health detection, and NDVI calculation
for drone-captured agricultural images using OpenCV and TensorFlow.

Author: Smart Farming AI Team
Date: 2024
"""

import os
import cv2
import numpy as np
import pandas as pd
# TensorFlow is optional. Attempt to import, otherwise fall back to rule-based logic.
try:
    import tensorflow as tf
    from tensorflow import keras
    TF_AVAILABLE = True
except Exception:
    TF_AVAILABLE = False
import matplotlib.pyplot as plt
from PIL import Image
import json
import logging
from typing import Dict, List, Tuple, Optional

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CropHealthDetector:
    """
    Crop Health Detection using trained CNN model
    """
    
    def __init__(self, model_path: str = 'model/crop_health_model.h5'):
        self.model_path = model_path
        self.model = None
        self.class_names = ['Healthy', 'Diseased', 'Pest-affected']
        self.img_size = (224, 224)
        self.load_model()
    
    def load_model(self):
        """
        Load the trained CNN model
        """
        try:
            if TF_AVAILABLE and os.path.exists(self.model_path):
                self.model = keras.models.load_model(self.model_path)
                logger.info(f"Model loaded from {self.model_path}")
            else:
                if not TF_AVAILABLE:
                    logger.warning("TensorFlow not available. Using rule-based fallback for crop health.")
                else:
                    logger.warning(f"Model not found at {self.model_path}. Using rule-based fallback.")
                self.model = None
        except Exception as e:
            logger.error(f"Error loading model: {str(e)}")
            self.model = None
    
    def _rule_based_health(self, image_rgb: np.ndarray) -> dict:
        """
        Simple rule-based crop health estimation using vegetation indices.
        Returns a structure similar to model output.
        """
        # Compute Excess Green (ExG = 2G - R - B)
        r = image_rgb[:, :, 0].astype(np.float32)
        g = image_rgb[:, :, 1].astype(np.float32)
        b = image_rgb[:, :, 2].astype(np.float32)
        exg = 2 * g - r - b
        exg_norm = cv2.normalize(exg, None, 0.0, 1.0, cv2.NORM_MINMAX)

        # VARI = (G - R) / (G + R - B)
        denom = (g + r - b)
        vari = (g - r) / (denom + 1e-6)
        vari = np.clip(vari, -1.0, 1.0)
        vari_norm = (vari + 1.0) / 2.0

        score = 0.5 * exg_norm + 0.5 * vari_norm
        mean_score = float(np.mean(score))

        # Thresholds can be tuned per crop/lighting
        if mean_score > 0.6:
            status = 'Healthy'
        elif mean_score > 0.45:
            status = 'Pest-affected'
        else:
            status = 'Diseased'

        # Construct a pseudo "all_predictions"
        if status == 'Healthy':
            preds = [0.8, 0.1, 0.1]
        elif status == 'Diseased':
            preds = [0.1, 0.8, 0.1]
        else:
            preds = [0.15, 0.15, 0.7]

        confidence = max(preds)
        return {
            'status': status,
            'confidence': float(confidence),
            'all_predictions': {name: float(p) for name, p in zip(self.class_names, preds)},
            'health_score': float(mean_score),
            'recommendations': self._get_recommendations(
                [0,1,2][['Healthy','Diseased','Pest-affected'].index(status)], confidence
            )
        }
    
    def preprocess_image(self, image_path: str) -> np.ndarray:
        """
        Preprocess image for model input
        """
        try:
            # Load image
            img = cv2.imread(image_path)
            if img is None:
                raise ValueError(f"Could not load image from {image_path}")
            
            # Convert BGR to RGB
            img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            
            # Resize image
            img = cv2.resize(img, self.img_size)
            
            # Normalize pixel values
            img = img.astype(np.float32) / 255.0
            
            # Add batch dimension
            img = np.expand_dims(img, axis=0)
            
            return img
        
        except Exception as e:
            logger.error(f"Error preprocessing image: {str(e)}")
            # Return dummy image if preprocessing fails
            return np.random.random((1, *self.img_size, 3)).astype(np.float32)
    
    def analyze_crop_health(self, image_path: str) -> Dict:
        """
        Analyze crop health from image
        """
        try:
            # If model is available, use it; otherwise use rule-based fallback
            if self.model is not None:
                processed_img = self.preprocess_image(image_path)
                predictions = self.model.predict(processed_img, verbose=0)
                predicted_class_idx = np.argmax(predictions[0])
                confidence = float(predictions[0][predicted_class_idx])
                result = {
                    'status': self.class_names[predicted_class_idx],
                    'confidence': confidence,
                    'all_predictions': {
                        class_name: float(pred)
                        for class_name, pred in zip(self.class_names, predictions[0])
                    },
                    'health_score': self._calculate_health_score(predictions[0]),
                    'recommendations': self._get_recommendations(predicted_class_idx, confidence)
                }
                logger.info(f"Crop health analysis (model): {result['status']} (confidence: {confidence:.2f})")
                return result
            else:
                # Rule-based path reads the raw image at original size
                img_bgr = cv2.imread(image_path)
                if img_bgr is None:
                    raise ValueError(f"Could not load image from {image_path}")
                img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
                result = self._rule_based_health(img_rgb)
                logger.info(f"Crop health analysis (rule-based): {result['status']} (confidence: {result['confidence']:.2f})")
                return result
        
        except Exception as e:
            logger.error(f"Error analyzing crop health: {str(e)}")
            return {
                'status': 'Unknown',
                'confidence': 0.0,
                'all_predictions': {name: 0.33 for name in self.class_names},
                'health_score': 0.5,
                'recommendations': ['Manual inspection required']
            }
    
    def _calculate_health_score(self, predictions: np.ndarray) -> float:
        """
        Calculate overall health score (0-1, where 1 is healthy)
        """
        healthy_weight = predictions[0]  # Healthy class
        diseased_weight = predictions[1]  # Diseased class
        pest_weight = predictions[2]     # Pest-affected class
        
        # Health score: healthy gets full weight, diseased/pest get reduced weight
        health_score = healthy_weight + (diseased_weight * 0.3) + (pest_weight * 0.2)
        return float(health_score)
    
    def _get_recommendations(self, predicted_class: int, confidence: float) -> List[str]:
        """
        Get recommendations based on prediction
        """
        recommendations = []
        
        if predicted_class == 0:  # Healthy
            recommendations.extend([
                "Continue current farming practices",
                "Monitor regularly for early signs of disease",
                "Maintain proper irrigation and nutrition"
            ])
        elif predicted_class == 1:  # Diseased
            recommendations.extend([
                "Apply appropriate fungicide treatment",
                "Improve air circulation around plants",
                "Remove infected plant parts",
                "Consider crop rotation for next season"
            ])
        else:  # Pest-affected
            recommendations.extend([
                "Apply targeted pesticide treatment",
                "Introduce beneficial insects",
                "Use physical barriers or traps",
                "Monitor pest population levels"
            ])
        
        if confidence < 0.7:
            recommendations.append("Manual inspection recommended due to low confidence")
        
        return recommendations

class NDVIAnalyzer:
    """
    NDVI (Normalized Difference Vegetation Index) Analysis
    """
    
    def __init__(self):
        self.ndvi_ranges = {
            'water': (-1.0, 0.0),
            'soil': (0.0, 0.2),
            'sparse_vegetation': (0.2, 0.5),
            'moderate_vegetation': (0.5, 0.7),
            'dense_vegetation': (0.7, 1.0)
        }
    
    def calculate_ndvi(self, nir_band: np.ndarray, red_band: np.ndarray) -> np.ndarray:
        """
        Calculate NDVI from NIR and Red bands
        
        NDVI = (NIR - RED) / (NIR + RED)
        """
        try:
            # Ensure arrays are float to avoid integer division
            nir = nir_band.astype(np.float32)
            red = red_band.astype(np.float32)
            
            # Avoid division by zero
            denominator = nir + red
            denominator[denominator == 0] = 1e-10
            
            # Calculate NDVI
            ndvi = (nir - red) / denominator
            
            # Clip values to valid range [-1, 1]
            ndvi = np.clip(ndvi, -1.0, 1.0)
            
            return ndvi
        
        except Exception as e:
            logger.error(f"Error calculating NDVI: {str(e)}")
            return np.zeros_like(nir_band)
    
    def generate_mock_ndvi_data(self, width: int = 100, height: int = 100) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Generate mock NIR and Red band data for demonstration
        """
        # Create realistic vegetation patterns
        x = np.linspace(0, 10, width)
        y = np.linspace(0, 10, height)
        X, Y = np.meshgrid(x, y)
        
        # Simulate different vegetation zones
        vegetation_pattern = (
            0.8 * np.exp(-((X-3)**2 + (Y-3)**2) / 2) +  # Dense vegetation area
            0.6 * np.exp(-((X-7)**2 + (Y-7)**2) / 3) +  # Moderate vegetation
            0.3 * np.exp(-((X-5)**2 + (Y-2)**2) / 4)    # Sparse vegetation
        )
        
        # Add noise
        noise = np.random.normal(0, 0.1, (height, width))
        vegetation_pattern += noise
        
        # Generate NIR and Red bands
        # NIR is typically higher for vegetation
        nir_band = np.clip(vegetation_pattern * 255, 0, 255).astype(np.uint8)
        
        # Red band is typically lower for vegetation
        red_band = np.clip((1 - vegetation_pattern * 0.7) * 255, 0, 255).astype(np.uint8)
        
        # Calculate NDVI
        ndvi = self.calculate_ndvi(nir_band, red_band)
        
        return nir_band, red_band, ndvi
    
    def classify_ndvi(self, ndvi: np.ndarray) -> np.ndarray:
        """
        Classify NDVI values into vegetation categories
        """
        classification = np.zeros_like(ndvi, dtype=int)
        
        for i, (category, (min_val, max_val)) in enumerate(self.ndvi_ranges.items()):
            mask = (ndvi >= min_val) & (ndvi < max_val)
            classification[mask] = i
        
        return classification
    
    def analyze_vegetation_health(self, ndvi: np.ndarray) -> Dict:
        """
        Analyze vegetation health from NDVI data
        """
        # Calculate statistics
        mean_ndvi = np.mean(ndvi)
        std_ndvi = np.std(ndvi)
        min_ndvi = np.min(ndvi)
        max_ndvi = np.max(ndvi)
        
        # Classify vegetation
        classification = self.classify_ndvi(ndvi)
        
        # Count pixels in each category
        category_counts = {}
        for i, category in enumerate(self.ndvi_ranges.keys()):
            count = np.sum(classification == i)
            category_counts[category] = int(count)
        
        # Calculate vegetation percentage
        total_pixels = ndvi.size
        vegetation_pixels = category_counts['moderate_vegetation'] + category_counts['dense_vegetation']
        vegetation_percentage = (vegetation_pixels / total_pixels) * 100
        
        # Health assessment
        if mean_ndvi > 0.6:
            health_status = "Excellent"
        elif mean_ndvi > 0.4:
            health_status = "Good"
        elif mean_ndvi > 0.2:
            health_status = "Fair"
        else:
            health_status = "Poor"
        
        result = {
            'mean_ndvi': float(mean_ndvi),
            'std_ndvi': float(std_ndvi),
            'min_ndvi': float(min_ndvi),
            'max_ndvi': float(max_ndvi),
            'vegetation_percentage': float(vegetation_percentage),
            'health_status': health_status,
            'category_distribution': category_counts,
            'recommendations': self._get_ndvi_recommendations(mean_ndvi, vegetation_percentage)
        }
        
        return result
    
    def _get_ndvi_recommendations(self, mean_ndvi: float, vegetation_percentage: float) -> List[str]:
        """
        Get recommendations based on NDVI analysis
        """
        recommendations = []
        
        if mean_ndvi < 0.2:
            recommendations.extend([
                "Consider irrigation to improve soil moisture",
                "Apply organic matter to enhance soil quality",
                "Check for soil compaction issues"
            ])
        elif mean_ndvi < 0.4:
            recommendations.extend([
                "Monitor soil moisture levels",
                "Consider fertilizer application",
                "Check for pest or disease issues"
            ])
        elif mean_ndvi < 0.6:
            recommendations.extend([
                "Maintain current practices",
                "Monitor for early signs of stress",
                "Consider precision irrigation"
            ])
        else:
            recommendations.extend([
                "Excellent vegetation health",
                "Continue current management practices",
                "Monitor for overgrowth if applicable"
            ])
        
        if vegetation_percentage < 30:
            recommendations.append("Consider increasing plant density")
        
        return recommendations

class ImageProcessor:
    """
    Main image processing class that combines all functionalities
    """
    
    def __init__(self):
        self.health_detector = CropHealthDetector()
        self.ndvi_analyzer = NDVIAnalyzer()
    
    def process_drone_image(self, image_path: str) -> Dict:
        """
        Process drone image for comprehensive analysis
        """
        logger.info(f"Processing drone image: {image_path}")
        
        try:
            # Crop health analysis
            health_analysis = self.health_detector.analyze_crop_health(image_path)
            
            # Generate mock NDVI data (in real scenario, this would come from multispectral camera)
            nir_band, red_band, ndvi = self.ndvi_analyzer.generate_mock_ndvi_data()
            
            # NDVI analysis
            ndvi_analysis = self.ndvi_analyzer.analyze_vegetation_health(ndvi)
            
            # Combine results
            result = {
                'image_path': image_path,
                'crop_health': health_analysis,
                'ndvi_analysis': ndvi_analysis,
                'processing_timestamp': str(pd.Timestamp.now()),
                'overall_assessment': self._get_overall_assessment(health_analysis, ndvi_analysis)
            }
            
            return result
        
        except Exception as e:
            logger.error(f"Error processing drone image: {str(e)}")
            return {
                'image_path': image_path,
                'error': str(e),
                'processing_timestamp': str(pd.Timestamp.now())
            }
    
    def _get_overall_assessment(self, health_analysis: Dict, ndvi_analysis: Dict) -> Dict:
        """
        Get overall assessment combining crop health and NDVI
        """
        health_score = health_analysis.get('health_score', 0.5)
        ndvi_score = ndvi_analysis.get('mean_ndvi', 0.5)
        
        # Weighted average
        overall_score = (health_score * 0.6) + (ndvi_score * 0.4)
        
        if overall_score > 0.7:
            status = "Excellent"
        elif overall_score > 0.5:
            status = "Good"
        elif overall_score > 0.3:
            status = "Fair"
        else:
            status = "Poor"
        
        return {
            'overall_score': float(overall_score),
            'status': status,
            'priority_actions': self._get_priority_actions(health_analysis, ndvi_analysis)
        }
    
    def _get_priority_actions(self, health_analysis: Dict, ndvi_analysis: Dict) -> List[str]:
        """
        Get priority actions based on analysis
        """
        actions = []
        
        # Add health-based actions
        health_status = health_analysis.get('status', 'Unknown')
        if health_status == 'Diseased':
            actions.append("URGENT: Apply disease treatment")
        elif health_status == 'Pest-affected':
            actions.append("HIGH: Apply pest control measures")
        
        # Add NDVI-based actions
        ndvi_status = ndvi_analysis.get('health_status', 'Unknown')
        if ndvi_status == 'Poor':
            actions.append("HIGH: Improve irrigation and soil conditions")
        elif ndvi_status == 'Fair':
            actions.append("MEDIUM: Monitor and optimize growing conditions")
        
        return actions

def main():
    """
    Main function for testing image processing
    """
    logger.info("Starting Smart Farming Drones - Image Processing Module")
    
    # Initialize processor
    processor = ImageProcessor()
    
    # Create sample image for testing
    sample_image_path = "data/sample_images/test_crop.jpg"
    os.makedirs(os.path.dirname(sample_image_path), exist_ok=True)
    
    # Generate a sample crop image
    sample_img = np.random.randint(0, 255, (224, 224, 3), dtype=np.uint8)
    # Make it more green (healthy looking)
    sample_img[:, :, 1] = np.clip(sample_img[:, :, 1] + 50, 0, 255)
    
    cv2.imwrite(sample_image_path, cv2.cvtColor(sample_img, cv2.COLOR_RGB2BGR))
    
    # Process the image
    result = processor.process_drone_image(sample_image_path)
    
    # Print results
    print("\n" + "="*50)
    print("DRONE IMAGE PROCESSING RESULTS")
    print("="*50)
    print(f"Image: {result['image_path']}")
    print(f"Crop Health: {result['crop_health']['status']}")
    print(f"Health Confidence: {result['crop_health']['confidence']:.2f}")
    print(f"NDVI Status: {result['ndvi_analysis']['health_status']}")
    print(f"Vegetation %: {result['ndvi_analysis']['vegetation_percentage']:.1f}%")
    print(f"Overall Status: {result['overall_assessment']['status']}")
    print(f"Overall Score: {result['overall_assessment']['overall_score']:.2f}")
    
    print("\nPriority Actions:")
    for action in result['overall_assessment']['priority_actions']:
        print(f"  - {action}")
    
    print("\nRecommendations:")
    for rec in result['crop_health']['recommendations']:
        print(f"  - {rec}")

if __name__ == "__main__":
    main()
