#!/usr/bin/env python3
"""
Database table creation script for OkroHealthDetector
This script generates individual CREATE TABLE statements for each table
"""

def generate_table_queries():
    """Generate CREATE TABLE queries for all database tables"""
    
    tables = {
        "users": """
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(64) UNIQUE NOT NULL,
    email VARCHAR(120) UNIQUE NOT NULL,
    password_hash VARCHAR(256) NOT NULL,
    role VARCHAR(20) DEFAULT 'user' NOT NULL,
    active BOOLEAN DEFAULT true NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP
);""",
        
        "disease_classes": """
CREATE TABLE disease_classes (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    treatment TEXT,
    severity_level INTEGER DEFAULT 1,
    active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);""",
        
        "predictions": """
CREATE TABLE predictions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    filename VARCHAR(255) NOT NULL,
    original_filename VARCHAR(255),
    prediction VARCHAR(100),
    confidence FLOAT DEFAULT 0.0,
    method VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    all_probabilities TEXT,
    dl_confidence FLOAT,
    rule_confidence FLOAT,
    processing_time FLOAT
);""",
        
        "user_feedback": """
CREATE TABLE user_feedback (
    id SERIAL PRIMARY KEY,
    prediction_id INTEGER NOT NULL REFERENCES predictions(id) ON DELETE CASCADE,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    feedback_type VARCHAR(50) NOT NULL,
    feedback_text TEXT,
    rating INTEGER CHECK (rating >= 1 AND rating <= 5),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);""",
        
        "system_logs": """
CREATE TABLE system_logs (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    event_type VARCHAR(100) NOT NULL,
    event_data TEXT,
    ip_address VARCHAR(45),
    user_agent TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);""",
        
        "user_profiles": """
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
);""",
        
        "training_data": """
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
);""",
        
        "model_training": """
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
);""",
        
        "chatbot_config": """
CREATE TABLE chatbot_config (
    id SERIAL PRIMARY KEY,
    config_key VARCHAR(100) UNIQUE NOT NULL,
    config_value TEXT,
    description TEXT,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);""",
        
        "chat_conversations": """
CREATE TABLE chat_conversations (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title VARCHAR(255) DEFAULT 'New Conversation',
    status VARCHAR(50) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);""",
        
        "chat_messages": """
CREATE TABLE chat_messages (
    id SERIAL PRIMARY KEY,
    conversation_id INTEGER NOT NULL REFERENCES chat_conversations(id) ON DELETE CASCADE,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    message_type VARCHAR(20) DEFAULT 'user',
    message_content TEXT NOT NULL,
    message_metadata TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);"""
    }
    
    return tables

def save_individual_queries():
    """Save each table creation query to separate files"""
    import os
    
    # Create directory for individual queries
    queries_dir = "backups/table_queries"
    os.makedirs(queries_dir, exist_ok=True)
    
    tables = generate_table_queries()
    
    for table_name, query in tables.items():
        filename = f"{queries_dir}/{table_name}.sql"
        with open(filename, 'w') as f:
            f.write(f"-- CREATE TABLE query for {table_name}\n")
            f.write(f"-- OkroHealthDetector Database Schema\n\n")
            f.write(query.strip())
            f.write("\n")
        print(f"Created: {filename}")
    
    print(f"\nTotal {len(tables)} table creation queries saved to {queries_dir}/")

if __name__ == "__main__":
    print("OkroHealthDetector - Database Table Creation Queries")
    print("=" * 55)
    
    # Generate and save individual queries
    save_individual_queries()
    
    print("\nTable creation queries generated successfully!")
    print("\nFiles created:")
    print("- backups/okro_database_schema.sql (Complete schema)")
    print("- backups/table_queries/*.sql (Individual table queries)")