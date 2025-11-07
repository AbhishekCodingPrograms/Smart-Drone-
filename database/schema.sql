-- Smart Farming Drones Database Schema
-- Store all historical data, scans, missions, and analytics

-- Missions Table: Store all drone missions
CREATE TABLE IF NOT EXISTS missions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    mission_name VARCHAR(255) NOT NULL,
    start_time DATETIME NOT NULL,
    end_time DATETIME,
    status VARCHAR(50) DEFAULT 'in_progress',
    field_area FLOAT,
    total_zones_scanned INTEGER DEFAULT 0,
    battery_consumed FLOAT,
    spray_used FLOAT,
    success_rate FLOAT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Field Zones Table: Store individual zone data
CREATE TABLE IF NOT EXISTS field_zones (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    mission_id INTEGER,
    zone_id VARCHAR(50) NOT NULL,
    latitude FLOAT,
    longitude FLOAT,
    x_coordinate FLOAT,
    y_coordinate FLOAT,
    scan_time DATETIME NOT NULL,
    
    -- Health Status
    health_status VARCHAR(50) NOT NULL, -- 'healthy', 'borderline', 'diseased', 'critical'
    health_score FLOAT, -- 0-100 score
    
    -- NDVI Analysis
    ndvi_value FLOAT,
    ndvi_category VARCHAR(50), -- 'very_low', 'low', 'moderate', 'high', 'very_high'
    
    -- Moisture
    moisture_level FLOAT,
    moisture_status VARCHAR(50), -- 'dry', 'optimal', 'wet'
    
    -- Disease Detection
    disease_detected BOOLEAN DEFAULT 0,
    disease_type VARCHAR(100),
    disease_severity VARCHAR(50), -- 'mild', 'moderate', 'severe', 'critical'
    disease_confidence FLOAT,
    
    -- Pest Detection
    pest_detected BOOLEAN DEFAULT 0,
    pest_type VARCHAR(100),
    pest_severity VARCHAR(50),
    
    -- Spray Requirements
    spray_required BOOLEAN DEFAULT 0,
    spray_priority VARCHAR(50), -- 'low', 'medium', 'high', 'critical'
    spray_amount FLOAT,
    spray_applied BOOLEAN DEFAULT 0,
    spray_timestamp DATETIME,
    
    -- Image Data
    image_path VARCHAR(500),
    thumbnail_path VARCHAR(500),
    
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (mission_id) REFERENCES missions(id)
);

-- Scan Images Table: Store captured images
CREATE TABLE IF NOT EXISTS scan_images (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    zone_id INTEGER,
    mission_id INTEGER,
    image_type VARCHAR(50), -- 'rgb', 'thermal', 'multispectral'
    file_path VARCHAR(500) NOT NULL,
    file_size INTEGER,
    width INTEGER,
    height INTEGER,
    capture_time DATETIME NOT NULL,
    camera_settings TEXT, -- JSON format
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (zone_id) REFERENCES field_zones(id),
    FOREIGN KEY (mission_id) REFERENCES missions(id)
);

-- AI Analysis Results Table
CREATE TABLE IF NOT EXISTS ai_analysis (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    zone_id INTEGER,
    image_id INTEGER,
    model_name VARCHAR(100),
    model_version VARCHAR(50),
    
    -- Predictions
    prediction_class VARCHAR(100),
    confidence_score FLOAT,
    bounding_boxes TEXT, -- JSON format
    
    -- Disease Classification
    disease_probability FLOAT,
    healthy_probability FLOAT,
    pest_probability FLOAT,
    
    -- Processing Info
    processing_time FLOAT,
    analysis_timestamp DATETIME NOT NULL,
    
    -- Results
    recommendation TEXT,
    action_required VARCHAR(100),
    
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (zone_id) REFERENCES field_zones(id),
    FOREIGN KEY (image_id) REFERENCES scan_images(id)
);

-- Spray Actions Table: Track all spray operations
CREATE TABLE IF NOT EXISTS spray_actions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    mission_id INTEGER,
    zone_id INTEGER,
    spray_timestamp DATETIME NOT NULL,
    spray_amount FLOAT,
    spray_type VARCHAR(100),
    spray_duration FLOAT,
    success BOOLEAN DEFAULT 1,
    notes TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (mission_id) REFERENCES missions(id),
    FOREIGN KEY (zone_id) REFERENCES field_zones(id)
);

-- Drone Telemetry Table: Real-time drone data
CREATE TABLE IF NOT EXISTS drone_telemetry (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    mission_id INTEGER,
    timestamp DATETIME NOT NULL,
    battery_level FLOAT,
    altitude FLOAT,
    speed FLOAT,
    latitude FLOAT,
    longitude FLOAT,
    heading FLOAT,
    temperature FLOAT,
    signal_strength INTEGER,
    gps_satellites INTEGER,
    status VARCHAR(50),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (mission_id) REFERENCES missions(id)
);

-- Alerts Table: System alerts and warnings
CREATE TABLE IF NOT EXISTS alerts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    mission_id INTEGER,
    alert_type VARCHAR(50), -- 'battery', 'spray', 'disease', 'system'
    severity VARCHAR(50), -- 'info', 'warning', 'critical'
    message TEXT NOT NULL,
    alert_time DATETIME NOT NULL,
    acknowledged BOOLEAN DEFAULT 0,
    resolved BOOLEAN DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (mission_id) REFERENCES missions(id)
);

-- Analytics Summary Table: Daily/Mission summaries
CREATE TABLE IF NOT EXISTS analytics_summary (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    mission_id INTEGER,
    summary_date DATE NOT NULL,
    
    -- Coverage
    total_area_scanned FLOAT,
    zones_scanned INTEGER,
    zones_healthy INTEGER,
    zones_borderline INTEGER,
    zones_diseased INTEGER,
    zones_critical INTEGER,
    
    -- Spray Statistics
    total_spray_used FLOAT,
    zones_sprayed INTEGER,
    spray_efficiency FLOAT,
    
    -- Disease Statistics
    total_diseases_detected INTEGER,
    disease_types TEXT, -- JSON array
    avg_disease_severity FLOAT,
    
    -- Performance
    avg_battery_drain FLOAT,
    total_flight_time FLOAT,
    avg_ndvi FLOAT,
    avg_moisture FLOAT,
    
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (mission_id) REFERENCES missions(id)
);

-- User Preferences Table
CREATE TABLE IF NOT EXISTS user_preferences (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    preference_key VARCHAR(100) UNIQUE NOT NULL,
    preference_value TEXT,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Create Indexes for Performance
CREATE INDEX IF NOT EXISTS idx_missions_status ON missions(status);
CREATE INDEX IF NOT EXISTS idx_missions_start_time ON missions(start_time);
CREATE INDEX IF NOT EXISTS idx_field_zones_mission ON field_zones(mission_id);
CREATE INDEX IF NOT EXISTS idx_field_zones_health ON field_zones(health_status);
CREATE INDEX IF NOT EXISTS idx_field_zones_scan_time ON field_zones(scan_time);
CREATE INDEX IF NOT EXISTS idx_spray_actions_mission ON spray_actions(mission_id);
CREATE INDEX IF NOT EXISTS idx_drone_telemetry_mission ON drone_telemetry(mission_id);
CREATE INDEX IF NOT EXISTS idx_alerts_mission ON alerts(mission_id);
CREATE INDEX IF NOT EXISTS idx_analytics_date ON analytics_summary(summary_date);
