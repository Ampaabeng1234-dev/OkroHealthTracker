-- CREATE TABLE query for model_training
-- OkroHealthDetector Database Schema

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
