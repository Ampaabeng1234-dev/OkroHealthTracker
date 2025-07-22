from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class User(db.Model):
    """User model for authentication and role management"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(10), nullable=False, default='user')
    active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    last_login = db.Column(db.DateTime)
    
    # Relationships
    predictions = db.relationship('Prediction', foreign_keys='Prediction.user_id', backref='user', lazy=True, cascade='all, delete-orphan')
    feedback_given = db.relationship('UserFeedback', foreign_keys='UserFeedback.user_id', backref='feedback_user', lazy=True, cascade='all, delete-orphan')
    logs = db.relationship('SystemLog', foreign_keys='SystemLog.user_id', backref='user', lazy=True, cascade='all, delete-orphan')
    
    def set_password(self, password):
        """Set password hash"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Check password against hash"""
        return check_password_hash(self.password_hash, password)
    
    def update_last_login(self):
        """Update last login timestamp"""
        self.last_login = datetime.utcnow()
        db.session.commit()
    
    def to_dict(self):
        """Convert user to dictionary for API responses"""
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'role': self.role,
            'active': self.active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_login': self.last_login.isoformat() if self.last_login else None
        }
    
    def __repr__(self):
        return f'<User {self.username}>'

class Prediction(db.Model):
    """Model for storing disease prediction results"""
    __tablename__ = 'predictions'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    original_filename = db.Column(db.String(255))
    prediction = db.Column(db.String(50), nullable=False)
    confidence = db.Column(db.Float, nullable=False)
    method = db.Column(db.String(20), nullable=False)  # 'deep_learning', 'hybrid', 'rule_based'
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    # Additional prediction details (JSON format)
    all_probabilities = db.Column(db.Text)  # JSON string of all class probabilities
    dl_confidence = db.Column(db.Float)  # Deep learning confidence if hybrid
    rule_confidence = db.Column(db.Float)  # Rule engine confidence if hybrid
    processing_time = db.Column(db.Float)  # Time taken for processing
    
    # Relationships
    feedback_entries = db.relationship('UserFeedback', backref='prediction', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self):
        """Convert prediction to dictionary"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'username': self.user.username if self.user else None,
            'filename': self.filename,
            'original_filename': self.original_filename,
            'prediction': self.prediction,
            'confidence': self.confidence,
            'method': self.method,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'all_probabilities': self.all_probabilities,
            'dl_confidence': self.dl_confidence,
            'rule_confidence': self.rule_confidence,
            'processing_time': self.processing_time,
            'has_feedback': len(self.feedback_entries) > 0
        }
    
    def __repr__(self):
        return f'<Prediction {self.id}: {self.prediction} ({self.confidence:.2f})>'

class UserFeedback(db.Model):
    """Model for storing user feedback on predictions"""
    __tablename__ = 'user_feedback'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    prediction_id = db.Column(db.Integer, db.ForeignKey('predictions.id'), nullable=False)
    feedback_type = db.Column(db.String(20), nullable=False)  # 'incorrect', 'correct', 'uncertain'
    correct_diagnosis = db.Column(db.String(50))  # What the user thinks is correct
    comments = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    resolved = db.Column(db.Boolean, default=False, nullable=False)
    resolved_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    resolved_at = db.Column(db.DateTime)
    
    # Relationships
    resolver = db.relationship('User', foreign_keys=[resolved_by], backref='resolved_feedback')
    
    def to_dict(self):
        """Convert feedback to dictionary"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'username': self.user.username if self.user else None,
            'prediction_id': self.prediction_id,
            'feedback_type': self.feedback_type,
            'correct_diagnosis': self.correct_diagnosis,
            'comments': self.comments,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'resolved': self.resolved,
            'resolved_by': self.resolved_by,
            'resolved_at': self.resolved_at.isoformat() if self.resolved_at else None
        }
    
    def __repr__(self):
        return f'<UserFeedback {self.id}: {self.feedback_type}>'

class SystemLog(db.Model):
    """Model for storing system logs and events"""
    __tablename__ = 'system_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    event_type = db.Column(db.String(50), nullable=False)  # 'login', 'logout', 'prediction', 'error', etc.
    event_data = db.Column(db.Text)  # JSON string with additional event data
    ip_address = db.Column(db.String(45))  # IPv4 or IPv6
    user_agent = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    def to_dict(self):
        """Convert log to dictionary"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'username': self.user.username if self.user else None,
            'event_type': self.event_type,
            'event_data': self.event_data,
            'ip_address': self.ip_address,
            'user_agent': self.user_agent,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    def __repr__(self):
        return f'<SystemLog {self.id}: {self.event_type}>'

class DiseaseClass(db.Model):
    """Model for storing disease class information and treatments"""
    __tablename__ = 'disease_classes'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.Text)
    treatment = db.Column(db.Text, nullable=False)
    severity_level = db.Column(db.Integer, default=1)  # 1-5 scale
    active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        """Convert disease class to dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'treatment': self.treatment,
            'severity_level': self.severity_level,
            'active': self.active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def __repr__(self):
        return f'<DiseaseClass {self.name}>'

class UserProfile(db.Model):
    """Model for storing user profile information"""
    __tablename__ = 'user_profiles'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), unique=True, nullable=False)
    first_name = db.Column(db.String(50))
    last_name = db.Column(db.String(50))
    phone = db.Column(db.String(20))
    location = db.Column(db.String(100))
    bio = db.Column(db.Text)
    avatar_filename = db.Column(db.String(255))
    date_of_birth = db.Column(db.Date)
    organization = db.Column(db.String(100))
    expertise_level = db.Column(db.String(20), default='beginner')  # beginner, intermediate, expert
    preferred_language = db.Column(db.String(10), default='en')
    notification_preferences = db.Column(db.Text)  # JSON string
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship
    user = db.relationship('User', backref=db.backref('profile', uselist=False, cascade='all, delete-orphan'))
    
    def to_dict(self):
        """Convert profile to dictionary"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'phone': self.phone,
            'location': self.location,
            'bio': self.bio,
            'avatar_filename': self.avatar_filename,
            'date_of_birth': self.date_of_birth.isoformat() if self.date_of_birth else None,
            'organization': self.organization,
            'expertise_level': self.expertise_level,
            'preferred_language': self.preferred_language,
            'notification_preferences': self.notification_preferences,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def __repr__(self):
        return f'<UserProfile {self.user.username if self.user else self.user_id}>'

class ChatbotConfig(db.Model):
    """Model for storing chatbot configuration managed by admin"""
    __tablename__ = 'chatbot_config'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    system_prompt = db.Column(db.Text, nullable=False)
    greeting_message = db.Column(db.Text, default="Hello! I'm here to help you with okra plant health questions.")
    max_conversation_length = db.Column(db.Integer, default=20)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    response_tone = db.Column(db.String(20), default='helpful')  # helpful, formal, friendly, technical
    supported_languages = db.Column(db.Text, default='["en"]')  # JSON array
    knowledge_base = db.Column(db.Text)  # JSON string with FAQ and responses
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    creator = db.relationship('User', backref='created_chatbots')
    conversations = db.relationship('ChatConversation', backref='chatbot_config', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self):
        """Convert chatbot config to dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'system_prompt': self.system_prompt,
            'greeting_message': self.greeting_message,
            'max_conversation_length': self.max_conversation_length,
            'is_active': self.is_active,
            'response_tone': self.response_tone,
            'supported_languages': self.supported_languages,
            'knowledge_base': self.knowledge_base,
            'created_by': self.created_by,
            'creator_name': self.creator.username if self.creator else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def __repr__(self):
        return f'<ChatbotConfig {self.name}>'

class ChatConversation(db.Model):
    """Model for storing chat conversations"""
    __tablename__ = 'chat_conversations'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    chatbot_config_id = db.Column(db.Integer, db.ForeignKey('chatbot_config.id'), nullable=False)
    session_id = db.Column(db.String(255), nullable=False, index=True)
    title = db.Column(db.String(200))
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    started_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    last_message_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    user = db.relationship('User', backref='chat_conversations')
    messages = db.relationship('ChatMessage', backref='conversation', lazy=True, cascade='all, delete-orphan', order_by='ChatMessage.created_at')
    
    def to_dict(self):
        """Convert conversation to dictionary"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'username': self.user.username if self.user else None,
            'chatbot_config_id': self.chatbot_config_id,
            'chatbot_name': self.chatbot_config.name if self.chatbot_config else None,
            'session_id': self.session_id,
            'title': self.title,
            'is_active': self.is_active,
            'message_count': len(self.messages),
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'last_message_at': self.last_message_at.isoformat() if self.last_message_at else None
        }
    
    def __repr__(self):
        return f'<ChatConversation {self.id}: {self.title or "Untitled"}>'

class ChatMessage(db.Model):
    """Model for storing individual chat messages"""
    __tablename__ = 'chat_messages'
    
    id = db.Column(db.Integer, primary_key=True)
    conversation_id = db.Column(db.Integer, db.ForeignKey('chat_conversations.id'), nullable=False)
    message_type = db.Column(db.String(20), nullable=False)  # 'user', 'bot', 'system'
    content = db.Column(db.Text, nullable=False)
    extra_data = db.Column(db.Text)  # JSON string for additional data
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    def to_dict(self):
        """Convert message to dictionary"""
        return {
            'id': self.id,
            'conversation_id': self.conversation_id,
            'message_type': self.message_type,
            'content': self.content,
            'extra_data': self.extra_data,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    def __repr__(self):
        return f'<ChatMessage {self.id}: {self.message_type}>'

class TrainingData(db.Model):
    """Model for storing training images and data"""
    __tablename__ = 'training_data'
    
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    original_filename = db.Column(db.String(255), nullable=False)
    disease_class = db.Column(db.String(100), nullable=False)
    file_path = db.Column(db.String(500), nullable=False)
    file_size = db.Column(db.Integer)
    image_width = db.Column(db.Integer)
    image_height = db.Column(db.Integer)
    uploaded_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    upload_date = db.Column(db.DateTime, default=datetime.utcnow)
    is_validated = db.Column(db.Boolean, default=False)
    validation_notes = db.Column(db.Text)
    
    # Relationship
    uploader = db.relationship('User', backref='training_uploads')
    
    def to_dict(self):
        """Convert training data to dictionary"""
        return {
            'id': self.id,
            'filename': self.filename,
            'original_filename': self.original_filename,
            'disease_class': self.disease_class,
            'file_size': self.file_size,
            'image_width': self.image_width,
            'image_height': self.image_height,
            'uploaded_by': self.uploaded_by,
            'uploader_name': self.uploader.username if self.uploader else None,
            'upload_date': self.upload_date.isoformat() if self.upload_date else None,
            'is_validated': self.is_validated,
            'validation_notes': self.validation_notes
        }
    
    def __repr__(self):
        return f'<TrainingData {self.id}: {self.disease_class}>'

class ModelTraining(db.Model):
    """Model for storing model training sessions"""
    __tablename__ = 'model_training'
    
    id = db.Column(db.Integer, primary_key=True)
    training_name = db.Column(db.String(200), nullable=False)
    model_version = db.Column(db.String(100), nullable=False)
    training_status = db.Column(db.String(50), default='pending')
    training_start = db.Column(db.DateTime)
    training_end = db.Column(db.DateTime)
    total_images = db.Column(db.Integer, default=0)
    training_accuracy = db.Column(db.Float)
    validation_accuracy = db.Column(db.Float)
    epochs_completed = db.Column(db.Integer, default=0)
    total_epochs = db.Column(db.Integer, default=10)
    model_file_path = db.Column(db.String(500))
    training_log = db.Column(db.Text)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship
    trainer = db.relationship('User', backref='model_trainings')
    
    def to_dict(self):
        """Convert model training to dictionary"""
        return {
            'id': self.id,
            'training_name': self.training_name,
            'model_version': self.model_version,
            'training_status': self.training_status,
            'training_start': self.training_start.isoformat() if self.training_start else None,
            'training_end': self.training_end.isoformat() if self.training_end else None,
            'total_images': self.total_images,
            'training_accuracy': self.training_accuracy,
            'validation_accuracy': self.validation_accuracy,
            'epochs_completed': self.epochs_completed,
            'total_epochs': self.total_epochs,
            'created_by': self.created_by,
            'trainer_name': self.trainer.username if self.trainer else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    def __repr__(self):
        return f'<ModelTraining {self.id}: {self.training_name}>'