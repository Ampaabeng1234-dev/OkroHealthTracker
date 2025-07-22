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
from utils.chatbot import chatbot_service
import cv2
import numpy as np
from PIL import Image
from database_models import db, User, Prediction, UserFeedback, SystemLog, DiseaseClass, UserProfile, ChatbotConfig, ChatConversation, ChatMessage, TrainingData, ModelTraining

# Configure logging
logging.basicConfig(level=logging.DEBUG)

app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "okro_health_detector_secret_key")

# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
    "pool_reset_on_return": "commit",
    "connect_args": {"sslmode": "prefer"}
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
        try:
            db.session.rollback()
        except:
            pass  # If rollback fails, continue silently

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
        
        # Force role to be 'user' for all registrations - admins assign admin privileges
        role = 'user'
        
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

@app.route('/admin/users')
@admin_required
def manage_users():
    """Admin user management interface"""
    users = User.query.order_by(User.created_at.desc()).all()
    user_list = []
    
    for user in users:
        user_data = user.to_dict()
        # Add statistics for each user
        user_data['prediction_count'] = Prediction.query.filter_by(user_id=user.id).count()
        user_data['feedback_count'] = UserFeedback.query.filter_by(user_id=user.id).count()
        user_list.append(user_data)
    
    return render_template('admin_users.html', users=user_list)

@app.route('/admin/users/<int:user_id>/toggle_role', methods=['POST'])
@admin_required
def toggle_user_role(user_id):
    """Toggle user role between admin and user"""
    user = User.query.get_or_404(user_id)
    
    # Prevent admin from demoting themselves
    if user.id == session['user_id']:
        flash('You cannot change your own role!', 'error')
        return redirect(url_for('manage_users'))
    
    try:
        # Toggle role
        new_role = 'admin' if user.role == 'user' else 'user'
        user.role = new_role
        db.session.commit()
        
        # Log the role change
        log_system_event('role_changed', {
            'target_user': user.username,
            'old_role': 'user' if new_role == 'admin' else 'admin',
            'new_role': new_role
        }, session['user_id'])
        
        flash(f'User {user.username} role changed to {new_role}.', 'success')
    except Exception as e:
        logging.error(f"Error changing user role: {str(e)}")
        db.session.rollback()
        flash('Error changing user role.', 'error')
    
    return redirect(url_for('manage_users'))

@app.route('/admin/users/<int:user_id>/toggle_status', methods=['POST'])
@admin_required
def toggle_user_status(user_id):
    """Toggle user active status"""
    user = User.query.get_or_404(user_id)
    
    # Prevent admin from deactivating themselves
    if user.id == session['user_id']:
        flash('You cannot deactivate your own account!', 'error')
        return redirect(url_for('manage_users'))
    
    try:
        # Toggle active status
        user.active = not user.active
        db.session.commit()
        
        status = 'activated' if user.active else 'deactivated'
        
        # Log the status change
        log_system_event('user_status_changed', {
            'target_user': user.username,
            'new_status': status
        }, session['user_id'])
        
        flash(f'User {user.username} has been {status}.', 'success')
    except Exception as e:
        logging.error(f"Error changing user status: {str(e)}")
        db.session.rollback()
        flash('Error changing user status.', 'error')
    
    return redirect(url_for('manage_users'))

@app.route('/admin/users/<int:user_id>/delete', methods=['POST'])
@admin_required
def delete_user(user_id):
    """Delete a user and all associated data"""
    user = User.query.get_or_404(user_id)
    
    # Prevent admin from deleting themselves
    if user.id == session['user_id']:
        flash('You cannot delete your own account!', 'error')
        return redirect(url_for('manage_users'))
    
    try:
        username = user.username
        
        # Log the deletion before deleting
        log_system_event('user_deleted', {
            'deleted_user': username,
            'deleted_by': session['username']
        }, session['user_id'])
        
        # Delete user (cascade will handle related records)
        db.session.delete(user)
        db.session.commit()
        
        flash(f'User {username} has been permanently deleted.', 'success')
    except Exception as e:
        logging.error(f"Error deleting user: {str(e)}")
        db.session.rollback()
        flash('Error deleting user.', 'error')
    
    return redirect(url_for('manage_users'))

# ============ User Profile Routes ============

@app.route('/profile')
@login_required
def user_profile():
    """Display user profile page"""
    user = User.query.get(session['user_id'])
    profile = UserProfile.query.filter_by(user_id=session['user_id']).first()
    
    return render_template('profile.html', user=user, profile=profile)

@app.route('/profile/edit', methods=['GET', 'POST'])
@login_required
def edit_profile():
    """Edit user profile"""
    user = User.query.get(session['user_id'])
    profile = UserProfile.query.filter_by(user_id=session['user_id']).first()
    
    if request.method == 'POST':
        try:
            # Create profile if it doesn't exist
            if not profile:
                profile = UserProfile(user_id=session['user_id'])
                db.session.add(profile)
            
            # Update profile fields
            profile.first_name = request.form.get('first_name', '').strip()
            profile.last_name = request.form.get('last_name', '').strip()
            profile.phone = request.form.get('phone', '').strip()
            profile.location = request.form.get('location', '').strip()
            profile.bio = request.form.get('bio', '').strip()
            profile.organization = request.form.get('organization', '').strip()
            profile.expertise_level = request.form.get('expertise_level', 'beginner')
            profile.preferred_language = request.form.get('preferred_language', 'en')
            
            # Handle date of birth
            dob_str = request.form.get('date_of_birth', '').strip()
            if dob_str:
                try:
                    profile.date_of_birth = datetime.strptime(dob_str, '%Y-%m-%d').date()
                except ValueError:
                    profile.date_of_birth = None
            
            db.session.commit()
            flash('Profile updated successfully!', 'success')
            
            # Log the profile update
            log_system_event('profile_updated', {
                'user_id': session['user_id'],
                'changes': 'Profile information updated'
            }, session['user_id'])
            
            return redirect(url_for('user_profile'))
            
        except Exception as e:
            logging.error(f"Error updating profile: {str(e)}")
            db.session.rollback()
            flash('Error updating profile. Please try again.', 'error')
    
    return render_template('edit_profile.html', user=user, profile=profile)

# ============ Chatbot Routes ============

@app.route('/chat')
@login_required
def chat_interface():
    """Display chat interface for users"""
    # Get active chatbot config
    active_chatbot = ChatbotConfig.query.filter_by(is_active=True).first()
    
    if not active_chatbot:
        flash('Chat service is currently unavailable. Please contact an administrator.', 'warning')
        return redirect(url_for('index'))
    
    # Get user's recent conversations
    recent_conversations = ChatConversation.query.filter_by(
        user_id=session['user_id'], 
        chatbot_config_id=active_chatbot.id
    ).order_by(ChatConversation.last_message_at.desc()).limit(10).all()
    
    return render_template('chat.html', 
                         chatbot=active_chatbot, 
                         conversations=recent_conversations,
                         openai_available=chatbot_service.is_available())

@app.route('/chat/send', methods=['POST'])
@login_required
def send_chat_message():
    """Send a chat message and get response"""
    try:
        data = request.get_json()
        message = data.get('message', '').strip()
        conversation_id = data.get('conversation_id')
        
        if not message:
            return jsonify({'success': False, 'error': 'Message cannot be empty'})
        
        # Get active chatbot config
        active_chatbot = ChatbotConfig.query.filter_by(is_active=True).first()
        if not active_chatbot:
            return jsonify({'success': False, 'error': 'Chat service unavailable'})
        
        # Handle conversation
        if conversation_id:
            # Existing conversation
            conversation = ChatConversation.query.filter_by(
                id=conversation_id, 
                user_id=session['user_id']
            ).first()
            if not conversation:
                return jsonify({'success': False, 'error': 'Conversation not found'})
        else:
            # New conversation
            conversation = ChatConversation(
                user_id=session['user_id'],
                chatbot_config_id=active_chatbot.id,
                session_id=str(uuid.uuid4()),
                title=chatbot_service.generate_conversation_title(message),
                started_at=datetime.utcnow(),
                last_message_at=datetime.utcnow()
            )
            db.session.add(conversation)
            db.session.flush()  # Get conversation ID
        
        # Save user message
        user_message = ChatMessage(
            conversation_id=conversation.id,
            message_type='user',
            content=message,
            created_at=datetime.utcnow()
        )
        db.session.add(user_message)
        
        # Get conversation history for context
        history = ChatMessage.query.filter_by(
            conversation_id=conversation.id
        ).order_by(ChatMessage.created_at.asc()).all()
        
        history_dicts = [msg.to_dict() for msg in history]
        
        # Generate bot response
        bot_response, success = chatbot_service.generate_response(
            active_chatbot.to_dict(),
            history_dicts,
            message
        )
        
        # Save bot response
        bot_message = ChatMessage(
            conversation_id=conversation.id,
            message_type='bot',
            content=bot_response,
            extra_data=json.dumps({'openai_success': success}),
            created_at=datetime.utcnow()
        )
        db.session.add(bot_message)
        
        # Update conversation
        conversation.last_message_at = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'conversation_id': conversation.id,
            'bot_response': bot_response,
            'conversation_title': conversation.title,
            'openai_success': success
        })
        
    except Exception as e:
        logging.error(f"Error in chat message: {str(e)}")
        db.session.rollback()
        return jsonify({'success': False, 'error': 'An error occurred while processing your message'})

@app.route('/chat/conversations')
@login_required
def get_chat_conversations():
    """Get user's chat conversations"""
    try:
        conversations = ChatConversation.query.filter_by(
            user_id=session['user_id']
        ).order_by(ChatConversation.last_message_at.desc()).all()
        
        return jsonify({
            'success': True,
            'conversations': [conv.to_dict() for conv in conversations]
        })
        
    except Exception as e:
        logging.error(f"Error getting conversations: {str(e)}")
        return jsonify({'success': False, 'error': 'Failed to load conversations'})

@app.route('/chat/conversation/<int:conversation_id>')
@login_required
def get_conversation_messages(conversation_id):
    """Get messages for a specific conversation"""
    try:
        conversation = ChatConversation.query.filter_by(
            id=conversation_id, 
            user_id=session['user_id']
        ).first_or_404()
        
        messages = ChatMessage.query.filter_by(
            conversation_id=conversation_id
        ).order_by(ChatMessage.created_at.asc()).all()
        
        return jsonify({
            'success': True,
            'conversation': conversation.to_dict(),
            'messages': [msg.to_dict() for msg in messages]
        })
        
    except Exception as e:
        logging.error(f"Error getting conversation messages: {str(e)}")
        return jsonify({'success': False, 'error': 'Failed to load conversation'})

# ============ Admin Chatbot Management Routes ============

@app.route('/admin/chatbot')
@admin_required
def admin_chatbot():
    """Admin chatbot management page"""
    chatbots = ChatbotConfig.query.order_by(ChatbotConfig.created_at.desc()).all()
    conversations_count = ChatConversation.query.count()
    messages_count = ChatMessage.query.count()
    
    return render_template('admin_chatbot.html', 
                         chatbots=chatbots,
                         conversations_count=conversations_count,
                         messages_count=messages_count,
                         openai_available=chatbot_service.is_available())

@app.route('/admin/chatbot/create', methods=['GET', 'POST'])
@admin_required
def create_chatbot():
    """Create new chatbot configuration"""
    if request.method == 'POST':
        try:
            # Deactivate other chatbots if this one should be active
            if request.form.get('is_active') == 'on':
                ChatbotConfig.query.update({'is_active': False})
            
            chatbot = ChatbotConfig(
                name=request.form['name'],
                description=request.form.get('description', ''),
                system_prompt=request.form['system_prompt'],
                greeting_message=request.form.get('greeting_message', 'Hello! How can I help you?'),
                max_conversation_length=int(request.form.get('max_conversation_length', 20)),
                is_active=bool(request.form.get('is_active')),
                response_tone=request.form.get('response_tone', 'helpful'),
                supported_languages=json.dumps([request.form.get('supported_languages', 'en')]),
                knowledge_base=request.form.get('knowledge_base', ''),
                created_by=session['user_id']
            )
            
            db.session.add(chatbot)
            db.session.commit()
            
            flash('Chatbot created successfully!', 'success')
            
            # Log the creation
            log_system_event('chatbot_created', {
                'chatbot_name': chatbot.name,
                'created_by': session['username']
            }, session['user_id'])
            
            return redirect(url_for('admin_chatbot'))
            
        except Exception as e:
            logging.error(f"Error creating chatbot: {str(e)}")
            db.session.rollback()
            flash('Error creating chatbot. Please try again.', 'error')
    
    return render_template('create_chatbot.html')

@app.route('/admin/chatbot/<int:chatbot_id>/edit', methods=['GET', 'POST'])
@admin_required
def edit_chatbot(chatbot_id):
    """Edit chatbot configuration"""
    chatbot = ChatbotConfig.query.get_or_404(chatbot_id)
    
    if request.method == 'POST':
        try:
            # Deactivate other chatbots if this one should be active
            if request.form.get('is_active') == 'on' and not chatbot.is_active:
                ChatbotConfig.query.filter(ChatbotConfig.id != chatbot_id).update({'is_active': False})
            
            chatbot.name = request.form['name']
            chatbot.description = request.form.get('description', '')
            chatbot.system_prompt = request.form['system_prompt']
            chatbot.greeting_message = request.form.get('greeting_message', 'Hello! How can I help you?')
            chatbot.max_conversation_length = int(request.form.get('max_conversation_length', 20))
            chatbot.is_active = bool(request.form.get('is_active'))
            chatbot.response_tone = request.form.get('response_tone', 'helpful')
            chatbot.supported_languages = json.dumps([request.form.get('supported_languages', 'en')])
            chatbot.knowledge_base = request.form.get('knowledge_base', '')
            
            db.session.commit()
            
            flash('Chatbot updated successfully!', 'success')
            
            # Log the update
            log_system_event('chatbot_updated', {
                'chatbot_name': chatbot.name,
                'updated_by': session['username']
            }, session['user_id'])
            
            return redirect(url_for('admin_chatbot'))
            
        except Exception as e:
            logging.error(f"Error updating chatbot: {str(e)}")
            db.session.rollback()
            flash('Error updating chatbot. Please try again.', 'error')
    
    return render_template('edit_chatbot.html', chatbot=chatbot)

@app.route('/admin/chatbot/<int:chatbot_id>/delete', methods=['POST'])
@admin_required
def delete_chatbot(chatbot_id):
    """Delete chatbot configuration"""
    chatbot = ChatbotConfig.query.get_or_404(chatbot_id)
    
    try:
        chatbot_name = chatbot.name
        
        # Log before deletion
        log_system_event('chatbot_deleted', {
            'chatbot_name': chatbot_name,
            'deleted_by': session['username']
        }, session['user_id'])
        
        db.session.delete(chatbot)
        db.session.commit()
        
        flash(f'Chatbot "{chatbot_name}" has been deleted.', 'success')
        
    except Exception as e:
        logging.error(f"Error deleting chatbot: {str(e)}")
        db.session.rollback()
        flash('Error deleting chatbot.', 'error')
    
    return redirect(url_for('admin_chatbot'))

# ============ Model Training Routes ============

@app.route('/admin/training')
@admin_required
def admin_training():
    """Admin model training management page"""
    training_sessions = ModelTraining.query.order_by(ModelTraining.created_at.desc()).all()
    training_data = TrainingData.query.order_by(TrainingData.upload_date.desc()).limit(50).all()
    
    # Get statistics
    total_images = TrainingData.query.count()
    validated_images = TrainingData.query.filter_by(is_validated=True).count()
    class_counts = {}
    disease_classes = ['Healthy', 'Bacterial_Blight', 'Leaf_Spot', 'Mosaic_Virus', 'Powdery_Mildew']
    
    for disease_class in disease_classes:
        class_counts[disease_class] = TrainingData.query.filter_by(disease_class=disease_class).count()
    
    return render_template('admin_training.html',
                         training_sessions=training_sessions,
                         training_data=training_data,
                         total_images=total_images,
                         validated_images=validated_images,
                         class_counts=class_counts)

@app.route('/admin/training/upload', methods=['GET', 'POST'])
@admin_required
def upload_training_data():
    """Upload training images"""
    if request.method == 'POST':
        try:
            disease_class = request.form.get('disease_class')
            if not disease_class:
                flash('Please select a disease class.', 'error')
                return redirect(request.url)
            
            files = request.files.getlist('training_images')
            if not files or files[0].filename == '':
                flash('Please select images to upload.', 'error')
                return redirect(request.url)
            
            uploaded_count = 0
            failed_count = 0
            
            # Create training data directory if it doesn't exist
            training_dir = os.path.join('static', 'training_data', disease_class)
            os.makedirs(training_dir, exist_ok=True)
            
            for file in files:
                if file and allowed_file(file.filename):
                    try:
                        # Generate unique filename
                        filename = f"{disease_class}_{int(time.time())}_{secure_filename(file.filename)}"
                        file_path = os.path.join(training_dir, filename)
                        
                        # Save file
                        file.save(file_path)
                        
                        # Get image dimensions
                        with Image.open(file_path) as img:
                            width, height = img.size
                        
                        # Create training data record
                        training_data = TrainingData(
                            filename=filename,
                            original_filename=file.filename,
                            disease_class=disease_class,
                            file_path=file_path,
                            file_size=os.path.getsize(file_path),
                            image_width=width,
                            image_height=height,
                            uploaded_by=session['user_id']
                        )
                        
                        db.session.add(training_data)
                        uploaded_count += 1
                        
                    except Exception as e:
                        logging.error(f"Error uploading file {file.filename}: {str(e)}")
                        failed_count += 1
                else:
                    failed_count += 1
            
            db.session.commit()
            
            if uploaded_count > 0:
                flash(f'Successfully uploaded {uploaded_count} training images.', 'success')
            if failed_count > 0:
                flash(f'{failed_count} files failed to upload.', 'warning')
            
            return redirect(url_for('admin_training'))
            
        except Exception as e:
            logging.error(f"Error in training data upload: {str(e)}")
            db.session.rollback()
            flash('Error uploading training data. Please try again.', 'error')
    
    disease_classes = ['Healthy', 'Bacterial_Blight', 'Leaf_Spot', 'Mosaic_Virus', 'Powdery_Mildew']
    return render_template('upload_training.html', disease_classes=disease_classes)

@app.route('/admin/training/start', methods=['POST'])
@admin_required
def start_training():
    """Start model training"""
    try:
        training_name = request.form.get('training_name')
        epochs = int(request.form.get('epochs', 10))
        
        if not training_name:
            flash('Please provide a training name.', 'error')
            return redirect(url_for('admin_training'))
        
        # Check if we have enough training data
        total_images = TrainingData.query.filter_by(is_validated=True).count()
        if total_images < 10:
            flash('Need at least 10 validated training images to start training.', 'warning')
            return redirect(url_for('admin_training'))
        
        # Create training session
        model_version = f"v{int(time.time())}"
        training_session = ModelTraining(
            training_name=training_name,
            model_version=model_version,
            training_status='pending',
            total_epochs=epochs,
            total_images=total_images,
            created_by=session['user_id']
        )
        
        db.session.add(training_session)
        db.session.commit()
        
        # Start training simulation (simplified for demo)
        # In a real system, this would trigger background training
        training_session.training_status = 'training'
        training_session.epochs_completed = 5
        training_session.training_accuracy = 0.85
        training_session.validation_accuracy = 0.82
        db.session.commit()
        
        flash('Training session started! (Demo simulation completed)', 'success')
        
        return redirect(url_for('admin_training'))
        
    except Exception as e:
        logging.error(f"Error starting training: {str(e)}")
        db.session.rollback()
        flash('Error starting training. Please try again.', 'error')
        return redirect(url_for('admin_training'))

@app.route('/admin/training/validate/<int:data_id>', methods=['POST'])
@admin_required
def validate_training_data(data_id):
    """Validate or reject training data"""
    try:
        training_data = TrainingData.query.get_or_404(data_id)
        action = request.form.get('action')
        notes = request.form.get('notes', '')
        
        if action == 'validate':
            training_data.is_validated = True
            training_data.validation_notes = notes
            flash('Training data validated.', 'success')
        elif action == 'reject':
            training_data.is_validated = False
            training_data.validation_notes = notes
            flash('Training data rejected.', 'info')
        
        db.session.commit()
        
    except Exception as e:
        logging.error(f"Error validating training data: {str(e)}")
        db.session.rollback()
        flash('Error updating validation status.', 'error')
    
    return redirect(url_for('admin_training'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
