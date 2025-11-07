"""
Camera Integration Module for Smart Farming Drones
Supports multiple camera inputs: webcam, IP camera, uploaded files
"""

import numpy as np
import base64
from datetime import datetime
from typing import Optional, Tuple, Dict
import os
import logging

# OpenCV is optional
try:
    import cv2
    CV2_AVAILABLE = True
except Exception:
    CV2_AVAILABLE = False
    cv2 = None

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CameraManager:
    """Manages camera capture and image processing"""
    
    def __init__(self, save_directory: str = "data/captured_images"):
        """
        Initialize camera manager
        
        Args:
            save_directory: Directory to save captured images
        """
        self.save_directory = save_directory
        os.makedirs(save_directory, exist_ok=True)
        self.active_camera = None
        self.camera_settings = {
            'width': 1280,
            'height': 720,
            'fps': 30,
            'brightness': 128,
            'contrast': 128
        }
    
    def list_available_cameras(self) -> list:
        """List all available camera devices"""
        available_cameras = []
        
        # Check up to 10 camera indices
        for index in range(10):
            cap = cv2.VideoCapture(index)
            if cap.isOpened():
                ret, _ = cap.read()
                if ret:
                    available_cameras.append({
                        'index': index,
                        'name': f'Camera {index}',
                        'type': 'webcam'
                    })
                cap.release()
        
        logger.info(f"Found {len(available_cameras)} available cameras")
        return available_cameras
    
    def initialize_camera(self, camera_id: int = 0, ip_address: str = None) -> bool:
        """
        Initialize camera for capture
        
        Args:
            camera_id: Camera device index
            ip_address: IP camera URL (optional)
            
        Returns:
            Success status
        """
        try:
            if ip_address:
                # IP Camera connection
                self.active_camera = cv2.VideoCapture(ip_address)
                logger.info(f"Connected to IP camera: {ip_address}")
            else:
                # Webcam connection
                self.active_camera = cv2.VideoCapture(camera_id)
                
                # Apply settings
                self.active_camera.set(cv2.CAP_PROP_FRAME_WIDTH, self.camera_settings['width'])
                self.active_camera.set(cv2.CAP_PROP_FRAME_HEIGHT, self.camera_settings['height'])
                self.active_camera.set(cv2.CAP_PROP_FPS, self.camera_settings['fps'])
                
                logger.info(f"Initialized camera {camera_id}")
            
            # Test if camera is working
            if not self.active_camera.isOpened():
                logger.error("Failed to open camera")
                return False
            
            ret, _ = self.active_camera.read()
            if not ret:
                logger.error("Failed to read from camera")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error initializing camera: {e}")
            return False
    
    def capture_image(self, zone_id: str = None) -> Tuple[bool, Optional[np.ndarray], Optional[str]]:
        """
        Capture image from active camera
        
        Args:
            zone_id: Optional zone identifier
            
        Returns:
            (success, image_array, file_path)
        """
        if not self.active_camera or not self.active_camera.isOpened():
            logger.error("No active camera")
            return False, None, None
        
        try:
            ret, frame = self.active_camera.read()
            
            if not ret:
                logger.error("Failed to capture frame")
                return False, None, None
            
            # Generate filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            zone_str = f"_zone_{zone_id}" if zone_id else ""
            filename = f"capture_{timestamp}{zone_str}.jpg"
            file_path = os.path.join(self.save_directory, filename)
            
            # Save image
            cv2.imwrite(file_path, frame)
            logger.info(f"Image captured: {file_path}")
            
            return True, frame, file_path
            
        except Exception as e:
            logger.error(f"Error capturing image: {e}")
            return False, None, None
    
    def capture_and_encode(self, zone_id: str = None) -> Tuple[bool, Optional[str]]:
        """
        Capture image and return base64 encoded string
        
        Args:
            zone_id: Optional zone identifier
            
        Returns:
            (success, base64_image_string)
        """
        success, frame, file_path = self.capture_image(zone_id)
        
        if not success or frame is None:
            return False, None
        
        # Encode to base64
        _, buffer = cv2.imencode('.jpg', frame)
        base64_image = base64.b64encode(buffer).decode('utf-8')
        
        return True, base64_image
    
    def save_uploaded_image(self, file_data, filename: str, zone_id: str = None) -> Tuple[bool, Optional[str]]:
        """
        Save uploaded image file
        
        Args:
            file_data: Uploaded file data
            filename: Original filename
            zone_id: Optional zone identifier
            
        Returns:
            (success, file_path)
        """
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            zone_str = f"_zone_{zone_id}" if zone_id else ""
            ext = os.path.splitext(filename)[1]
            new_filename = f"upload_{timestamp}{zone_str}{ext}"
            file_path = os.path.join(self.save_directory, new_filename)
            
            # Save file
            with open(file_path, 'wb') as f:
                f.write(file_data)
            
            logger.info(f"Uploaded image saved: {file_path}")
            return True, file_path
            
        except Exception as e:
            logger.error(f"Error saving uploaded image: {e}")
            return False, None
    
    def process_image_for_analysis(self, image_path: str) -> Tuple[bool, Optional[Dict]]:
        """
        Preprocess image for AI analysis
        
        Args:
            image_path: Path to image file
            
        Returns:
            (success, preprocessed_data)
        """
        try:
            # Read image
            image = cv2.imread(image_path)
            if image is None:
                logger.error(f"Failed to read image: {image_path}")
                return False, None
            
            # Get image properties
            height, width, channels = image.shape
            
            # Resize if too large (for faster processing)
            max_dimension = 1024
            if max(height, width) > max_dimension:
                scale = max_dimension / max(height, width)
                new_width = int(width * scale)
                new_height = int(height * scale)
                image = cv2.resize(image, (new_width, new_height))
                logger.info(f"Resized image to {new_width}x{new_height}")
            
            # Convert to RGB (OpenCV loads as BGR)
            image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            
            # Calculate basic image statistics
            brightness = np.mean(image_rgb)
            contrast = np.std(image_rgb)
            
            # Create thumbnail
            thumbnail = cv2.resize(image, (256, 256))
            thumbnail_path = image_path.replace('.jpg', '_thumb.jpg')
            cv2.imwrite(thumbnail_path, thumbnail)
            
            return True, {
                'original_path': image_path,
                'thumbnail_path': thumbnail_path,
                'width': width,
                'height': height,
                'channels': channels,
                'brightness': float(brightness),
                'contrast': float(contrast),
                'processed_image': image_rgb
            }
            
        except Exception as e:
            logger.error(f"Error processing image: {e}")
            return False, None
    
    def get_camera_settings(self) -> Dict:
        """Get current camera settings"""
        if self.active_camera and self.active_camera.isOpened():
            actual_settings = {
                'width': int(self.active_camera.get(cv2.CAP_PROP_FRAME_WIDTH)),
                'height': int(self.active_camera.get(cv2.CAP_PROP_FRAME_HEIGHT)),
                'fps': int(self.active_camera.get(cv2.CAP_PROP_FPS)),
                'brightness': int(self.active_camera.get(cv2.CAP_PROP_BRIGHTNESS)),
                'contrast': int(self.active_camera.get(cv2.CAP_PROP_CONTRAST))
            }
            return actual_settings
        return self.camera_settings
    
    def update_camera_settings(self, settings: Dict) -> bool:
        """
        Update camera settings
        
        Args:
            settings: Dictionary of settings to update
            
        Returns:
            Success status
        """
        if not self.active_camera or not self.active_camera.isOpened():
            self.camera_settings.update(settings)
            return True
        
        try:
            if 'width' in settings:
                self.active_camera.set(cv2.CAP_PROP_FRAME_WIDTH, settings['width'])
            if 'height' in settings:
                self.active_camera.set(cv2.CAP_PROP_FRAME_HEIGHT, settings['height'])
            if 'fps' in settings:
                self.active_camera.set(cv2.CAP_PROP_FPS, settings['fps'])
            if 'brightness' in settings:
                self.active_camera.set(cv2.CAP_PROP_BRIGHTNESS, settings['brightness'])
            if 'contrast' in settings:
                self.active_camera.set(cv2.CAP_PROP_CONTRAST, settings['contrast'])
            
            self.camera_settings.update(settings)
            logger.info("Camera settings updated")
            return True
            
        except Exception as e:
            logger.error(f"Error updating camera settings: {e}")
            return False
    
    def get_live_frame(self) -> Tuple[bool, Optional[str]]:
        """
        Get current camera frame as base64 string (for live preview)
        
        Returns:
            (success, base64_image_string)
        """
        if not self.active_camera or not self.active_camera.isOpened():
            return False, None
        
        try:
            ret, frame = self.active_camera.read()
            if not ret:
                return False, None
            
            # Reduce size for faster transmission
            frame = cv2.resize(frame, (640, 480))
            
            # Encode to JPEG
            _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
            base64_image = base64.b64encode(buffer).decode('utf-8')
            
            return True, base64_image
            
        except Exception as e:
            logger.error(f"Error getting live frame: {e}")
            return False, None
    
    def release_camera(self):
        """Release camera resources"""
        if self.active_camera:
            self.active_camera.release()
            self.active_camera = None
            logger.info("Camera released")
    
    def __del__(self):
        """Cleanup on deletion"""
        self.release_camera()


# Global camera manager instance
camera_manager = CameraManager()
