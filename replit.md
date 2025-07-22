# OkroHealthDetector - AI Disease Detection System

## Overview

OkroHealthDetector is a Python-based web application that uses AI to detect diseases in okra leaves. The system employs a hybrid diagnostic approach combining a UNet deep learning model with a rule-based fallback engine for reliable disease classification. The application features role-based access control, real-time image processing, and comprehensive disease analysis with treatment recommendations.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Frontend Architecture
- **Framework**: HTML templates with Bootstrap 5 for responsive UI
- **Styling**: Dark theme with custom CSS and Font Awesome icons
- **JavaScript**: Vanilla JS for file upload handling and UI interactions
- **Template Engine**: Jinja2 templates extending from a base layout

### Backend Architecture
- **Framework**: Flask web framework with Flask-SQLAlchemy ORM
- **Language**: Python 3.x
- **Database**: PostgreSQL with structured data models
- **Session Management**: Flask sessions with secure secret key
- **File Handling**: Werkzeug utilities for secure file uploads
- **Logging**: Database-based system logging with Python's built-in logging module

### Authentication System
- **Method**: Username/password authentication with hashed passwords
- **Storage**: PostgreSQL database with User model
- **Roles**: Admin and User roles with different permission levels
- **Security**: Werkzeug password hashing with decorators for route protection

### Model Training System (NEW)
- **Custom Training**: Admin interface for uploading training images by disease class
- **Training Management**: Database tracking of training sessions with progress monitoring
- **Image Validation**: Automatic validation of training data quality
- **UNet Training**: Custom UNet model training with uploaded data
- **Similarity Validation**: Images validated against training data characteristics

## Key Components

### Disease Detection Pipeline
1. **Image Preprocessing** (`utils/preprocessing.py`)
   - Image resizing and normalization
   - Edge enhancement using unsharp masking
   - Color correction and feature extraction

2. **AI Model** (`models.py`)
   - UNet architecture for image classification
   - 5-class classification: Healthy, Bacterial Blight, Leaf Spot, Mosaic Virus, Powdery Mildew
   - Fallback to dummy model if trained model unavailable

3. **Rule-Based Engine** (`models/fallback_rule_engine.py`)
   - Handcrafted feature extraction
   - Heuristic rules for each disease type
   - Confidence scoring based on multiple criteria

### Access Control System
- **Login Required**: Decorator for protected routes
- **Admin Required**: Special permissions for system management
- **Role-Based Features**: Different UI and functionality based on user role

### Database Architecture
- **PostgreSQL Database**: Comprehensive data models for users, predictions, feedback, and system logs
- **User Management**: Secure user authentication with role-based access control
- **Prediction Tracking**: Complete audit trail of all disease predictions with confidence scores
- **Feedback System**: User feedback collection for continuous model improvement
- **System Logging**: Comprehensive event logging for monitoring and debugging
- **Disease Classes**: Structured disease information with treatments and severity levels
- **Training Data Management**: TrainingData and ModelTraining models for custom model training
- **Chatbot Configuration**: ChatbotConfig, ChatConversation, and ChatMessage models for AI chat system

## Data Flow

1. **User Registration/Login**: Authentication against PostgreSQL user database with role-based access
2. **Image Upload**: Secure file upload with validation and unique filename generation
3. **Preprocessing**: Image enhancement and feature extraction
4. **Primary Prediction**: UNet model inference with confidence scoring
5. **Fallback Analysis**: Rule-based engine if confidence low
6. **Database Logging**: Store complete prediction data including processing time, confidence scores, and method used
7. **Result Compilation**: Combine predictions with treatment recommendations from disease database
8. **Feedback Collection**: User feedback stored in database for model improvement
9. **Admin Monitoring**: Real-time statistics and logs accessible through admin dashboard

## External Dependencies

### Python Packages
- **Flask**: Web framework
- **OpenCV**: Image processing
- **NumPy**: Numerical computations
- **PIL/Pillow**: Image handling
- **PyTorch**: Deep learning framework
- **Werkzeug**: Security utilities

### Frontend Libraries
- **Bootstrap 5**: UI framework with dark theme
- **Font Awesome**: Icon library
- **Custom CSS**: Application-specific styling

### File Storage
- **Static Uploads**: Local file system for uploaded images
- **Model Storage**: PyTorch model files (.pth format)
- **Logs**: CSV files for prediction tracking

## Deployment Strategy

### File Structure
```
/okro_health_detector
├── app.py                    # Main Flask application
├── main.py                   # Application entry point
├── config.json              # System configuration
├── models.py                # AI model definitions
├── templates/               # HTML templates
├── static/                  # CSS, JS, uploads
├── utils/                   # Helper modules
├── models/                  # Trained model files
└── logs/                    # Application logs
```

### Environment Setup
- **Development**: Flask debug mode enabled
- **Host Configuration**: 0.0.0.0:5000 for Replit compatibility
- **File Permissions**: Automatic directory creation for uploads/logs
- **Session Security**: Environment variable for secret key

### Key Features
- **Hybrid AI Approach**: Primary UNet model with rule-based fallback
- **Role-Based Access**: Admin dashboard and user interface separation
- **Real-Time Processing**: Immediate image analysis and results
- **Treatment Guidance**: Detailed recommendations for each disease
- **Prediction Logging**: Admin monitoring of system performance
- **Responsive Design**: Mobile-friendly interface

The system is designed to be easily deployable on Replit with minimal configuration while providing a robust disease detection platform for okra farmers and agricultural professionals.