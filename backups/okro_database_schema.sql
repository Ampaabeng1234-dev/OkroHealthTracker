-- OkroHealthDetector Database Schema Creation Script
-- Created: 2025-07-26
-- Application: OkroHealthDetector v1.0
-- Database: PostgreSQL
-- 
-- This script creates all tables required for the OkroHealthDetector application
-- Run this script on a fresh PostgreSQL database to set up the complete schema

-- Enable extensions if needed
-- CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 1. Users table - stores user account information
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(64) UNIQUE NOT NULL,
    email VARCHAR(120) UNIQUE NOT NULL,
    password_hash VARCHAR(256) NOT NULL,
    role VARCHAR(20) DEFAULT 'user' NOT NULL,
    active BOOLEAN DEFAULT true NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP
);

-- 2. Disease classes table - stores disease information and treatments
CREATE TABLE disease_classes (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    treatment TEXT,
    severity_level INTEGER DEFAULT 1,
    active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 3. Predictions table - stores all disease prediction results
CREATE TABLE predictions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    filename VARCHAR(255) NOT NULL,
    original_filename VARCHAR(255),
    prediction VARCHAR(100),
    confidence FLOAT DEFAULT 0.0,
    method VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    all_probabilities TEXT, -- JSON string
    dl_confidence FLOAT,
    rule_confidence FLOAT,
    processing_time FLOAT
);

-- 4. User feedback table - stores user feedback on predictions
CREATE TABLE user_feedback (
    id SERIAL PRIMARY KEY,
    prediction_id INTEGER NOT NULL REFERENCES predictions(id) ON DELETE CASCADE,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    feedback_type VARCHAR(50) NOT NULL,
    feedback_text TEXT,
    rating INTEGER CHECK (rating >= 1 AND rating <= 5),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 5. System logs table - stores application events and audit trail
CREATE TABLE system_logs (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    event_type VARCHAR(100) NOT NULL,
    event_data TEXT, -- JSON string
    ip_address VARCHAR(45),
    user_agent TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 6. User profiles table - stores additional user information
CREATE TABLE user_profiles (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    full_name VARCHAR(200),
    phone VARCHAR(20),
    location VARCHAR(100),
    occupation VARCHAR(100),
    bio TEXT,
    profile_image VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 7. Training data table - stores custom training images
CREATE TABLE training_data (
    id SERIAL PRIMARY KEY,
    disease_class VARCHAR(100) NOT NULL,
    filename VARCHAR(255) NOT NULL,
    original_filename VARCHAR(255),
    uploaded_by INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    file_path VARCHAR(500),
    file_size INTEGER,
    image_width INTEGER,
    image_height INTEGER,
    validation_status VARCHAR(50) DEFAULT 'pending',
    validation_notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    processed_at TIMESTAMP
);

-- 8. Model training table - tracks training sessions
CREATE TABLE model_training (
    id SERIAL PRIMARY KEY,
    initiated_by INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    training_status VARCHAR(50) DEFAULT 'pending',
    training_progress FLOAT DEFAULT 0.0,
    total_epochs INTEGER DEFAULT 50,
    current_epoch INTEGER DEFAULT 0,
    training_loss FLOAT,
    validation_loss FLOAT,
    training_accuracy FLOAT,
    validation_accuracy FLOAT,
    model_path VARCHAR(500),
    training_data_count INTEGER DEFAULT 0,
    error_message TEXT,
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    training_duration FLOAT
);

-- 9. Chatbot configuration table - stores AI chatbot settings
CREATE TABLE chatbot_config (
    id SERIAL PRIMARY KEY,
    config_key VARCHAR(100) UNIQUE NOT NULL,
    config_value TEXT,
    description TEXT,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 10. Chat conversations table - stores user chat sessions
CREATE TABLE chat_conversations (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title VARCHAR(255) DEFAULT 'New Conversation',
    status VARCHAR(50) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 11. Chat messages table - stores individual chat messages
CREATE TABLE chat_messages (
    id SERIAL PRIMARY KEY,
    conversation_id INTEGER NOT NULL REFERENCES chat_conversations(id) ON DELETE CASCADE,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    message_type VARCHAR(20) DEFAULT 'user', -- 'user' or 'assistant'
    message_content TEXT NOT NULL,
    message_metadata TEXT, -- JSON string for additional data
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for better performance
CREATE INDEX idx_predictions_user_id ON predictions(user_id);
CREATE INDEX idx_predictions_created_at ON predictions(created_at);
CREATE INDEX idx_system_logs_user_id ON system_logs(user_id);
CREATE INDEX idx_system_logs_event_type ON system_logs(event_type);
CREATE INDEX idx_system_logs_created_at ON system_logs(created_at);
CREATE INDEX idx_training_data_disease_class ON training_data(disease_class);
CREATE INDEX idx_training_data_uploaded_by ON training_data(uploaded_by);
CREATE INDEX idx_chat_conversations_user_id ON chat_conversations(user_id);
CREATE INDEX idx_chat_messages_conversation_id ON chat_messages(conversation_id);
CREATE INDEX idx_chat_messages_created_at ON chat_messages(created_at);

-- Insert default disease classes
INSERT INTO disease_classes (name, description, treatment, severity_level, active) VALUES
('Healthy', 'Plant appears healthy with no visible signs of disease', 'Continue regular care. Monitor plant health regularly.', 1, true),
('Bacterial Blight', 'Bacterial infection causing leaf spots and wilting', 'Remove infected leaves. Apply copper-based bactericide. Ensure good drainage.', 4, true),
('Leaf Spot', 'Fungal infection causing circular spots on leaves', 'Remove affected leaves. Apply fungicide. Avoid overhead watering.', 3, true),
('Mosaic Virus', 'Viral infection causing mottled yellow and green patterns', 'Remove infected plants. Control aphid vectors. Use resistant varieties.', 5, true),
('Powdery Mildew', 'Fungal infection causing white powdery coating on leaves', 'Apply sulfur-based fungicide. Improve air circulation. Reduce humidity.', 3, true);

-- Insert default admin user (password: admin123)
INSERT INTO users (username, email, password_hash, role, active) VALUES
('admin', 'admin@okrohealth.com', 'scrypt:32768:8:1$m67aMQ8fvqgG54Yl$267870a6d8967414d9a9e67ee1d263db081ac99137997ed0dc88796aef4622faa4d9a71cbf820767a7249b9c5f05aa0807689abf7f08f3d20b72190a5210fd1d', 'admin', true);

-- Insert demo user (password: user123)  
INSERT INTO users (username, email, password_hash, role, active) VALUES
('demo_user', 'user@okrohealth.com', 'scrypt:32768:8:1$NEfmzpyrMmBfnJmR$1485e321e8c222b06ee28b9839c4e67f7c6bfedd57f43ed6a5d062426f6d55b6a9bdebae97f7121b1d328a9af237490b4cd560898043b1ae0172c31aa0215b12', 'user', true);

-- Insert basic chatbot configuration
INSERT INTO chatbot_config (config_key, config_value, description, is_active) VALUES
('welcome_message', 'Welcome to OkroHealthDetector! I can help you with questions about okra plant diseases and treatments.', 'Default welcome message for new chat sessions', true),
('max_conversation_length', '50', 'Maximum number of messages per conversation', true),
('response_timeout', '30', 'Timeout in seconds for AI responses', true);

-- Schema creation completed
-- Total tables created: 11
-- Default data inserted: 5 disease classes, 2 users, 3 chatbot configs