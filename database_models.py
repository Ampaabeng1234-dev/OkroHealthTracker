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