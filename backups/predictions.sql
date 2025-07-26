-- CREATE TABLE query for predictions
-- OkroHealthDetector Database Schema

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
);
