-- CREATE TABLE query for chat_messages
-- OkroHealthDetector Database Schema

CREATE TABLE chat_messages (
    id SERIAL PRIMARY KEY,
    conversation_id INTEGER NOT NULL REFERENCES chat_conversations(id) ON DELETE CASCADE,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    message_type VARCHAR(20) DEFAULT 'user',
    message_content TEXT NOT NULL,
    message_metadata TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
