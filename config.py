"""
Configuration settings for Smart Farming Drones application
"""
import os
from datetime import timedelta

class Config:
    """Base configuration"""
    
    # Flask
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    FLASK_APP = os.environ.get('FLASK_APP') or 'dashboard.app'
    
    # Server
    HOST = os.environ.get('HOST') or '0.0.0.0'
    PORT = int(os.environ.get('PORT') or 5000)
    
    # Database
    DATABASE_URL = os.environ.get('DATABASE_URL') or 'sqlite:///data/farming_drones.db'
    SQLALCHEMY_DATABASE_URI = DATABASE_URL
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # File Upload
    UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER') or 'data/captured_images'
    MAX_CONTENT_LENGTH = int(os.environ.get('MAX_UPLOAD_SIZE') or 16 * 1024 * 1024)  # 16MB
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp'}
    
    # Session
    PERMANENT_SESSION_LIFETIME = timedelta(hours=24)
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # Security
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = None
    
    # Logging
    LOG_LEVEL = os.environ.get('LOG_LEVEL') or 'INFO'
    LOG_FILE = os.environ.get('LOG_FILE') or 'logs/app.log'
    
    # Camera
    DEFAULT_CAMERA_INDEX = int(os.environ.get('DEFAULT_CAMERA_INDEX') or 0)
    ENABLE_CAMERA = os.environ.get('ENABLE_CAMERA', 'true').lower() == 'true'
    
    # AI Model
    MODEL_PATH = os.environ.get('MODEL_PATH') or 'models/crop_disease_model.h5'
    CONFIDENCE_THRESHOLD = float(os.environ.get('CONFIDENCE_THRESHOLD') or 0.75)
    
    # Features
    ENABLE_DEMO_MODE = os.environ.get('ENABLE_DEMO_MODE', 'false').lower() == 'true'
    ENABLE_MOCK_DATA = os.environ.get('ENABLE_MOCK_DATA', 'true').lower() == 'true'
    AUTO_REFRESH_INTERVAL = int(os.environ.get('AUTO_REFRESH_INTERVAL') or 5000)
    
    # Email (Optional)
    ENABLE_EMAIL = os.environ.get('ENABLE_EMAIL', 'false').lower() == 'true'
    MAIL_SERVER = os.environ.get('SMTP_SERVER') or 'smtp.gmail.com'
    MAIL_PORT = int(os.environ.get('SMTP_PORT') or 587)
    MAIL_USE_TLS = True
    MAIL_USERNAME = os.environ.get('SMTP_USER')
    MAIL_PASSWORD = os.environ.get('SMTP_PASSWORD')
    
    # SMS (Optional)
    ENABLE_SMS = os.environ.get('ENABLE_SMS', 'false').lower() == 'true'
    TWILIO_ACCOUNT_SID = os.environ.get('TWILIO_ACCOUNT_SID')
    TWILIO_AUTH_TOKEN = os.environ.get('TWILIO_AUTH_TOKEN')
    TWILIO_PHONE_NUMBER = os.environ.get('TWILIO_PHONE_NUMBER')


class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    TESTING = False
    ENV = 'development'


class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    TESTING = False
    ENV = 'production'
    
    # Override security settings for production
    SESSION_COOKIE_SECURE = True
    PREFERRED_URL_SCHEME = 'https'


class TestingConfig(Config):
    """Testing configuration"""
    DEBUG = True
    TESTING = True
    ENV = 'testing'
    DATABASE_URL = 'sqlite:///:memory:'


# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}


def get_config():
    """Get configuration based on environment"""
    env = os.environ.get('FLASK_ENV', 'development')
    return config.get(env, config['default'])
