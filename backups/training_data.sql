-- CREATE TABLE query for training_data
-- OkroHealthDetector Database Schema

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
