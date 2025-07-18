import os
import logging
import re
import json
import time
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from werkzeug.utils import secure_filename
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime
import uuid
from utils.preprocessing import preprocess_image
from utils.prediction import predict_disease
from utils.access_control import login_required, admin_required
import cv2
import numpy as np
from PIL import Image
from database_models import db, User, Prediction, UserFeedback, SystemLog, DiseaseClass

# Configure logging
logging.basicConfig(level=logging.DEBUG)

app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "okro_health_detector_secret_key")

# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize database
db.init_app(app)

# Create database tables and initialize data
def initialize_database():
    """Initialize database tables and populate with default data"""
    with app.app_context():
        try:
            # Create all tables
            db.create_all()
            
            # Check if disease classes exist, if not, populate them
            if DiseaseClass.query.count() == 0:
                disease_classes = [
                    {
                        'name': 'Healthy',
                        'description': 'Plant appears healthy with no visible signs of disease',
                        'treatment': 'Continue regular care. Monitor plant health regularly.',
                        'severity_level': 1
                    },
                    {
                        'name': 'Bacterial Blight',
                        'description': 'Bacterial infection causing leaf spots and wilting',
                        'treatment': 'Remove infected leaves. Apply copper-based bactericide. Ensure good drainage.',
                        'severity_level': 4
                    },
                    {
                        'name': 'Leaf Spot',
                        'description': 'Fungal infection causing circular spots on leaves',
                        'treatment': 'Remove affected leaves. Apply fungicide. Avoid overhead watering.',
                        'severity_level': 3
                    },
                    {
                        'name': 'Mosaic Virus',
                        'description': 'Viral infection causing mottled yellow and green patterns',
                        'treatment': 'Remove infected plants. Control aphid vectors. Use resistant varieties.',
                        'severity_level': 5
                    },
                    {
                        'name': 'Powdery Mildew',
                        'description': 'Fungal infection causing white powdery coating on leaves',
                        'treatment': 'Apply sulfur-based fungicide. Improve air circulation. Reduce humidity.',
                        'severity_level': 3
                    }
                ]
                
                for disease_data in disease_classes:
                    disease_class = DiseaseClass(**disease_data)
                    db.session.add(disease_class)
                
                db.session.commit()
                logging.info("Disease classes initialized successfully")
            
            # Check if demo users exist, if not, create them
            if User.query.count() == 0:
                demo_users = [
                    {
                        'username': 'admin',
                        'email': 'admin@okrohealth.com',
                        'password': 'admin123',
                        'role': 'admin'
                    },
                    {
                        'username': 'demo_user',
                        'email': 'user@okrohealth.com',
                        'password': 'user123',
                        'role': 'user'
                    }
                ]
                
                for user_data in demo_users:
                    user = User(
                        username=user_data['username'],
                        email=user_data['email'],
                        role=user_data['role']
                    )
                    user.set_password(user_data['password'])
                    db.session.add(user)
                
                db.session.commit()
                logging.info("Demo users created successfully")
                
        except Exception as e:
            logging.error(f"Error initializing database: {str(e)}")
            db.session.rollback()
            raise

# Configuration
UPLOAD_FOLDER = 'static/uploads'
FEEDBACK_FOLDER = 'static/feedback'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Ensure directories exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(FEEDBACK_FOLDER, exist_ok=True)
os.makedirs('logs', exist_ok=True)
os.makedirs('models', exist_ok=True)

# Initialize database on startup
initialize_database()

def log_system_event(event_type, event_data=None, user_id=None):
    """Log system events to database"""
    try:
        ip_address = request.environ.get('HTTP_X_FORWARDED_FOR', request.environ.get('REMOTE_ADDR'))
        user_agent = request.environ.get('HTTP_USER_AGENT')
        
        log_entry = SystemLog(
            user_id=user_id,
            event_type=event_type,
            event_data=json.dumps(event_data) if event_data else None,
            ip_address=ip_address,
            user_agent=user_agent
        )
        db.session.add(log_entry)
        db.session.commit()
    except Exception as e:
        logging.error(f"Error logging system event: {str(e)}")
        db.session.rollback()

def get_disease_treatment(disease_name):
    """Get treatment for a specific disease"""
    disease = DiseaseClass.query.filter_by(name=disease_name, active=True).first()
    if disease:
        return disease.treatment
    return "Treatment information not available. Please consult an agricultural expert."

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def log_prediction(user_id, filename, original_filename, prediction, confidence, method, processing_time=None, all_probabilities=None, dl_confidence=None, rule_confidence=None):
    """Log prediction results to database"""
    try:
        prediction_record = Prediction(
            user_id=user_id,
            filename=filename,
            original_filename=original_filename,
            prediction=prediction,
            confidence=confidence,
            method=method,
            processing_time=processing_time,
            all_probabilities=json.dumps(all_probabilities) if all_probabilities else None,
            dl_confidence=dl_confidence,
            rule_confidence=rule_confidence
        )
        
        db.session.add(prediction_record)
        db.session.commit()
        
        return prediction_record.id
    except Exception as e:
        logging.error(f"Error logging prediction: {str(e)}")
        db.session.rollback()
        return None

@app.route('/')
def index():
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('index.html', username=session['username'], role=session['role'])

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        action = request.form.get('action', 'login')
        
        if action == 'login':
            username = request.form['username']
            password = request.form['password']
            
            user = User.query.filter_by(username=username, active=True).first()
            if user and user.check_password(password):
                session['username'] = username
                session['user_id'] = user.id
                session['role'] = user.role
                
                # Update last login
                user.update_last_login()
                
                # Log the login event
                log_system_event('login', {'username': username}, user.id)
                
                flash('Login successful!', 'success')
                return redirect(url_for('index'))
            
            # Log failed login attempt
            log_system_event('failed_login', {'username': username})
            flash('Invalid username or password!', 'error')
    
    return render_template('login.html')

@app.route('/register', methods=['POST'])
def register():
    try:
        username = request.form['username'].strip()
        email = request.form['email'].strip()
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        role = request.form['role']
        
        # Validation
        if not username or len(username) < 3 or len(username) > 20:
            flash('Username must be between 3 and 20 characters!', 'error')
            return redirect(url_for('login'))
        
        if not re.match(r'^[a-zA-Z0-9_]+$', username):
            flash('Username can only contain letters, numbers, and underscores!', 'error')
            return redirect(url_for('login'))
        
        # Check if username already exists
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash('Username already exists! Please choose a different username.', 'error')
            return redirect(url_for('login'))
        
        if not email or '@' not in email:
            flash('Please enter a valid email address!', 'error')
            return redirect(url_for('login'))
        
        # Check if email already exists
        existing_email = User.query.filter_by(email=email).first()
        if existing_email:
            flash('Email address already registered! Please use a different email.', 'error')
            return redirect(url_for('login'))
        
        if len(password) < 6:
            flash('Password must be at least 6 characters long!', 'error')
            return redirect(url_for('login'))
        
        if password != confirm_password:
            flash('Passwords do not match!', 'error')
            return redirect(url_for('login'))
        
        if role not in ['user', 'admin']:
            flash('Invalid account type selected!', 'error')
            return redirect(url_for('login'))
        
        # Create new user
        new_user = User(
            username=username,
            email=email,
            role=role
        )
        new_user.set_password(password)
        
        db.session.add(new_user)
        db.session.commit()
        
        # Log the registration
        log_system_event('registration', {
            'username': username,
            'email': email,
            'role': role
        }, new_user.id)
        
        logging.info(f"New user registered: {username} ({role}) with email {email}")
        
        # Auto-login the user
        session['username'] = username
        session['user_id'] = new_user.id
        session['role'] = role
        
        flash(f'Account created successfully! Welcome, {username}!', 'success')
        return redirect(url_for('index'))
        
    except Exception as e:
        logging.error(f"Error during registration: {str(e)}")
        db.session.rollback()
        flash('An error occurred during registration. Please try again.', 'error')
        return redirect(url_for('login'))

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

@app.route('/upload', methods=['POST'])
@login_required
def upload_file():
    if 'file' not in request.files:
        flash('No file selected!', 'error')
        return redirect(url_for('index'))
    
    file = request.files['file']
    if file.filename == '':
        flash('No file selected!', 'error')
        return redirect(url_for('index'))
    
    if file and allowed_file(file.filename):
        # Generate unique filename
        filename = str(uuid.uuid4()) + '_' + secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        try:
            # Process image and get prediction
            processed_image = preprocess_image(filepath)
            prediction_result = predict_disease(processed_image, filepath)
            
            # Log the prediction
            start_time = time.time()
            processing_time = time.time() - start_time
            
            prediction_id = log_prediction(
                session['user_id'],
                filename,
                file.filename,
                prediction_result['prediction'], 
                prediction_result['confidence'], 
                prediction_result['method'],
                processing_time,
                prediction_result.get('all_probabilities'),
                prediction_result.get('dl_confidence'),
                prediction_result.get('rule_confidence')
            )
            
            # Add treatment suggestion
            prediction_result['treatment'] = get_disease_treatment(prediction_result['prediction'])
            prediction_result['prediction_id'] = prediction_id
            
            return render_template('result.html', 
                                 result=prediction_result, 
                                 filename=filename,
                                 username=session['username'])
            
        except Exception as e:
            logging.error(f"Error processing image: {str(e)}")
            flash(f'Error processing image: {str(e)}', 'error')
            return redirect(url_for('index'))
    
    flash('Invalid file type! Please upload PNG, JPG, JPEG, or GIF files.', 'error')
    return redirect(url_for('index'))

@app.route('/admin')
@admin_required
def admin_dashboard():
    # Get prediction logs from database
    predictions = Prediction.query.order_by(Prediction.created_at.desc()).limit(100).all()
    logs = [pred.to_dict() for pred in predictions]
    
    # Get user statistics
    total_users = User.query.count()
    active_users = User.query.filter_by(active=True).count()
    total_predictions = Prediction.query.count()
    
    # Get recent system logs
    recent_logs = SystemLog.query.order_by(SystemLog.created_at.desc()).limit(50).all()
    system_logs = [log.to_dict() for log in recent_logs]
    
    # Get feedback statistics
    feedback_count = UserFeedback.query.count()
    unresolved_feedback = UserFeedback.query.filter_by(resolved=False).count()
    
    # Get disease statistics
    disease_stats = {}
    for disease in DiseaseClass.query.filter_by(active=True).all():
        count = Prediction.query.filter_by(prediction=disease.name).count()
        disease_stats[disease.name] = count
    
    stats = {
        'total_users': total_users,
        'active_users': active_users,
        'total_predictions': total_predictions,
        'feedback_count': feedback_count,
        'unresolved_feedback': unresolved_feedback,
        'disease_stats': disease_stats,
        'accuracy_rate': round((total_predictions - unresolved_feedback) / max(total_predictions, 1) * 100, 1) if total_predictions > 0 else 100
    }
    
    return render_template('admin.html', logs=logs, stats=stats, system_logs=system_logs)

@app.route('/flag_prediction', methods=['POST'])
@login_required
def flag_prediction():
    prediction_id = request.form.get('prediction_id')
    feedback_type = request.form.get('feedback_type', 'incorrect')
    correct_diagnosis = request.form.get('correct_diagnosis', '')
    comments = request.form.get('comments', '')
    
    if prediction_id:
        try:
            # Create feedback record
            feedback = UserFeedback(
                user_id=session['user_id'],
                prediction_id=prediction_id,
                feedback_type=feedback_type,
                correct_diagnosis=correct_diagnosis if correct_diagnosis else None,
                comments=comments if comments else None
            )
            
            db.session.add(feedback)
            db.session.commit()
            
            # Log the feedback event
            log_system_event('feedback_submitted', {
                'prediction_id': prediction_id,
                'feedback_type': feedback_type,
                'correct_diagnosis': correct_diagnosis
            }, session['user_id'])
            
            flash('Thank you for your feedback! This prediction has been flagged for review.', 'success')
        except Exception as e:
            logging.error(f"Error submitting feedback: {str(e)}")
            db.session.rollback()
            flash('Error submitting feedback. Please try again.', 'error')
    else:
        flash('Invalid prediction reference.', 'error')
    
    return redirect(url_for('index'))

@app.route('/retrain_model', methods=['POST'])
@admin_required
def retrain_model():
    try:
        # This is a placeholder for model retraining functionality
        # In a real implementation, this would trigger the retraining process
        flash('Model retraining initiated. This process may take several minutes.', 'info')
        logging.info("Model retraining requested by admin")
        
        # Here you would implement the actual retraining logic
        # For now, we'll just simulate it
        
    except Exception as e:
        logging.error(f"Error during model retraining: {str(e)}")
        flash(f'Error during model retraining: {str(e)}', 'error')
    
    return redirect(url_for('admin_dashboard'))

@app.route('/clear_logs', methods=['POST'])
@admin_required
def clear_logs():
    try:
        log_type = request.form.get('log_type', 'predictions')
        
        if log_type == 'predictions':
            # Clear prediction logs
            Prediction.query.delete()
            db.session.commit()
            flash('Prediction logs cleared successfully.', 'success')
        elif log_type == 'system':
            # Clear system logs
            SystemLog.query.delete()
            db.session.commit()
            flash('System logs cleared successfully.', 'success')
        elif log_type == 'feedback':
            # Clear feedback logs
            UserFeedback.query.delete()
            db.session.commit()
            flash('Feedback logs cleared successfully.', 'success')
        else:
            flash('Invalid log type specified.', 'error')
            
        # Log the clear action
        log_system_event('logs_cleared', {'log_type': log_type}, session['user_id'])
    except Exception as e:
        logging.error(f"Error clearing logs: {str(e)}")
        flash(f'Error clearing logs: {str(e)}', 'error')
    
    return redirect(url_for('admin_dashboard'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
