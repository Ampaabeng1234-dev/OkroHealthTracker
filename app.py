import os
import logging
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from werkzeug.utils import secure_filename
from werkzeug.security import check_password_hash, generate_password_hash
import json
import csv
from datetime import datetime
import uuid
from utils.preprocessing import preprocess_image
from utils.prediction import predict_disease
from utils.access_control import login_required, admin_required
import cv2
import numpy as np
from PIL import Image

# Configure logging
logging.basicConfig(level=logging.DEBUG)

app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "okro_health_detector_secret_key")

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

# Load configuration
def load_config():
    try:
        with open('config.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {
            "users": {
                "admin": {
                    "password_hash": generate_password_hash("admin123"),
                    "role": "admin"
                },
                "user": {
                    "password_hash": generate_password_hash("user123"),
                    "role": "user"
                }
            },
            "disease_classes": [
                "Healthy",
                "Bacterial Blight",
                "Leaf Spot",
                "Mosaic Virus",
                "Powdery Mildew"
            ],
            "treatments": {
                "Healthy": "No treatment needed. Continue good care practices.",
                "Bacterial Blight": "Apply copper-based fungicide. Remove infected leaves. Improve air circulation.",
                "Leaf Spot": "Use fungicidal spray. Remove fallen leaves. Avoid overhead watering.",
                "Mosaic Virus": "Remove infected plants. Control aphid vectors. Use virus-free seeds.",
                "Powdery Mildew": "Apply sulfur-based fungicide. Improve air circulation. Reduce humidity."
            }
        }

config = load_config()

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def log_prediction(username, filename, prediction, confidence, method, feedback=None):
    """Log prediction results to CSV file"""
    log_file = 'logs/prediction_log.csv'
    timestamp = datetime.now().isoformat()
    
    # Create header if file doesn't exist
    if not os.path.exists(log_file):
        with open(log_file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['timestamp', 'username', 'filename', 'prediction', 'confidence', 'method', 'feedback'])
    
    # Append log entry
    with open(log_file, 'a', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([timestamp, username, filename, prediction, confidence, method, feedback])

@app.route('/')
def index():
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('index.html', username=session['username'], role=session['role'])

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        if username in config['users']:
            user = config['users'][username]
            if check_password_hash(user['password_hash'], password):
                session['username'] = username
                session['role'] = user['role']
                flash('Login successful!', 'success')
                return redirect(url_for('index'))
        
        flash('Invalid username or password!', 'error')
    
    return render_template('login.html')

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
            log_prediction(
                session['username'], 
                filename, 
                prediction_result['prediction'], 
                prediction_result['confidence'], 
                prediction_result['method']
            )
            
            # Add treatment suggestion
            prediction_result['treatment'] = config['treatments'].get(
                prediction_result['prediction'], 
                "Consult with agricultural expert for treatment advice."
            )
            
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
    # Read prediction logs
    logs = []
    log_file = 'logs/prediction_log.csv'
    if os.path.exists(log_file):
        with open(log_file, 'r') as f:
            reader = csv.DictReader(f)
            logs = list(reader)
            logs.reverse()  # Show newest first
    
    # Get statistics
    total_predictions = len(logs)
    flagged_predictions = len([log for log in logs if log.get('feedback') == 'flagged'])
    
    stats = {
        'total_predictions': total_predictions,
        'flagged_predictions': flagged_predictions,
        'accuracy_rate': round((total_predictions - flagged_predictions) / max(total_predictions, 1) * 100, 1)
    }
    
    return render_template('admin.html', logs=logs, stats=stats)

@app.route('/flag_prediction', methods=['POST'])
@login_required
def flag_prediction():
    filename = request.form.get('filename')
    prediction = request.form.get('prediction')
    
    if filename and prediction:
        # Move file to feedback folder
        source_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        dest_path = os.path.join(FEEDBACK_FOLDER, filename)
        
        try:
            if os.path.exists(source_path):
                import shutil
                shutil.copy2(source_path, dest_path)
            
            # Log the feedback
            log_prediction(
                session['username'], 
                filename, 
                prediction, 
                0.0, 
                'flagged', 
                'flagged'
            )
            
            flash('Thank you for your feedback! This prediction has been flagged for review.', 'success')
        except Exception as e:
            logging.error(f"Error flagging prediction: {str(e)}")
            flash('Error submitting feedback. Please try again.', 'error')
    
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
        log_file = 'logs/prediction_log.csv'
        if os.path.exists(log_file):
            os.remove(log_file)
        flash('Prediction logs cleared successfully.', 'success')
    except Exception as e:
        logging.error(f"Error clearing logs: {str(e)}")
        flash(f'Error clearing logs: {str(e)}', 'error')
    
    return redirect(url_for('admin_dashboard'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
