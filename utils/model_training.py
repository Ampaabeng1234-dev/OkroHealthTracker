import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
import torchvision.transforms as transforms
from PIL import Image
import os
import numpy as np
import logging
from datetime import datetime
import json
from database_models import TrainingData, ModelTraining
from model_definitions import UNetModel
import cv2
from sklearn.model_selection import train_test_split

class CustomTrainingDataset(Dataset):
    """Custom dataset for training the UNet model with uploaded data"""
    
    def __init__(self, training_data_records, transform=None, validation_features=None):
        self.training_data = training_data_records
        self.transform = transform
        self.validation_features = validation_features  # Features from training data for validation
        self.class_names = ['Healthy', 'Bacterial_Blight', 'Leaf_Spot', 'Mosaic_Virus', 'Powdery_Mildew']
        self.class_to_idx = {cls: idx for idx, cls in enumerate(self.class_names)}
        
    def __len__(self):
        return len(self.training_data)
    
    def __getitem__(self, idx):
        data_record = self.training_data[idx]
        
        # Load image
        image = Image.open(data_record.file_path).convert('RGB')
        
        # Apply transforms
        if self.transform:
            image = self.transform(image)
        
        # Get class index
        label = self.class_to_idx[data_record.disease_class]
        
        return image, label

class TrainingValidator:
    """Validates new images against training data characteristics"""
    
    def __init__(self, training_features=None):
        self.training_features = training_features or {}
        
    def extract_image_features(self, image_path):
        """Extract features from an image for similarity comparison"""
        try:
            # Load image
            image = cv2.imread(image_path)
            if image is None:
                return None
                
            # Convert to RGB
            image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            
            # Extract basic features
            features = {}
            
            # Color histogram features
            hist_r = cv2.calcHist([image_rgb], [0], None, [64], [0, 256])
            hist_g = cv2.calcHist([image_rgb], [1], None, [64], [0, 256])
            hist_b = cv2.calcHist([image_rgb], [2], None, [64], [0, 256])
            
            features['color_hist'] = np.concatenate([hist_r.flatten(), hist_g.flatten(), hist_b.flatten()])
            
            # Texture features (simplified)
            gray = cv2.cvtColor(image_rgb, cv2.COLOR_RGB2GRAY)
            features['mean_intensity'] = np.mean(gray)
            features['std_intensity'] = np.std(gray)
            
            # Edge features
            edges = cv2.Canny(gray, 50, 150)
            features['edge_density'] = np.sum(edges > 0) / (edges.shape[0] * edges.shape[1])
            
            return features
            
        except Exception as e:
            logging.error(f"Error extracting features from {image_path}: {str(e)}")
            return None
    
    def is_similar_to_training_data(self, image_path, threshold=0.3):
        """Check if an image is similar to the training data"""
        if not self.training_features:
            # If no training features available, accept all images
            return True, 1.0, "No training data features available for comparison"
        
        # Extract features from the new image
        image_features = self.extract_image_features(image_path)
        if image_features is None:
            return False, 0.0, "Could not extract features from image"
        
        try:
            # Calculate similarity scores for each training feature set
            similarities = []
            
            for training_feature_set in self.training_features:
                # Color histogram similarity (simplified)
                if 'color_hist' in training_feature_set and 'color_hist' in image_features:
                    hist_similarity = cv2.compareHist(
                        image_features['color_hist'].astype(np.float32),
                        training_feature_set['color_hist'].astype(np.float32),
                        cv2.HISTCMP_CORREL
                    )
                    similarities.append(max(0, hist_similarity))  # Correlation can be negative
                
                # Intensity similarity
                if 'mean_intensity' in training_feature_set:
                    intensity_diff = abs(image_features['mean_intensity'] - training_feature_set['mean_intensity'])
                    intensity_similarity = max(0, 1 - (intensity_diff / 255))
                    similarities.append(intensity_similarity)
            
            if not similarities:
                return True, 0.5, "Could not compute similarity metrics"
            
            # Get maximum similarity score
            max_similarity = max(similarities)
            
            if max_similarity >= threshold:
                return True, max_similarity, f"Image is similar to training data (similarity: {max_similarity:.2f})"
            else:
                return False, max_similarity, f"Image not similar to training data (similarity: {max_similarity:.2f}, threshold: {threshold})"
                
        except Exception as e:
            logging.error(f"Error calculating similarity: {str(e)}")
            return True, 0.5, f"Error in similarity calculation: {str(e)}"

class ModelTrainer:
    """Handles UNet model training with custom data"""
    
    def __init__(self, training_session_id):
        self.training_session_id = training_session_id
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.validator = None
        
    def prepare_data(self):
        """Prepare training data from database"""
        from app import app, db
        
        with app.app_context():
            # Get validated training data
            training_data = TrainingData.query.filter_by(is_validated=True).all()
            
            if len(training_data) < 10:
                raise ValueError("Not enough validated training data (minimum 10 images required)")
            
            # Extract features for validation
            training_features = []
            for data_record in training_data[:20]:  # Use first 20 for feature extraction
                features = self.extract_training_features(data_record.file_path)
                if features:
                    training_features.append(features)
            
            # Create validator
            self.validator = TrainingValidator(training_features)
            
            # Split data
            train_data, val_data = train_test_split(training_data, test_size=0.2, random_state=42)
            
            # Create datasets
            transform_train = transforms.Compose([
                transforms.Resize((224, 224)),
                transforms.RandomHorizontalFlip(p=0.5),
                transforms.RandomRotation(10),
                transforms.ColorJitter(brightness=0.2, contrast=0.2),
                transforms.ToTensor(),
                transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
            ])
            
            transform_val = transforms.Compose([
                transforms.Resize((224, 224)),
                transforms.ToTensor(),
                transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
            ])
            
            train_dataset = CustomTrainingDataset(train_data, transform=transform_train)
            val_dataset = CustomTrainingDataset(val_data, transform=transform_val)
            
            return train_dataset, val_dataset
    
    def extract_training_features(self, image_path):
        """Extract features from training images"""
        validator = TrainingValidator()
        return validator.extract_image_features(image_path)
    
    def train_model(self, epochs=10, batch_size=8, learning_rate=0.001):
        """Train the UNet model"""
        from app import app, db
        
        try:
            # Prepare data
            train_dataset, val_dataset = self.prepare_data()
            
            train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
            val_loader = DataLoader(val_dataset, batch_size=batch_size, shuffle=False)
            
            # Initialize model
            model = UNetModel(n_channels=3, n_classes=5)
            model.to(self.device)
            
            # Loss and optimizer
            criterion = nn.CrossEntropyLoss()
            optimizer = optim.Adam(model.parameters(), lr=learning_rate)
            scheduler = optim.lr_scheduler.StepLR(optimizer, step_size=5, gamma=0.5)
            
            best_val_acc = 0.0
            training_log = []
            
            with app.app_context():
                # Update training session status
                training_session = ModelTraining.query.get(self.training_session_id)
                training_session.training_status = 'training'
                training_session.training_start = datetime.utcnow()
                db.session.commit()
            
            # Training loop
            for epoch in range(epochs):
                # Training phase
                model.train()
                running_loss = 0.0
                correct_train = 0
                total_train = 0
                
                for batch_idx, (data, target) in enumerate(train_loader):
                    data, target = data.to(self.device), target.to(self.device)
                    
                    optimizer.zero_grad()
                    output = model(data)
                    loss = criterion(output, target)
                    loss.backward()
                    optimizer.step()
                    
                    running_loss += loss.item()
                    _, predicted = torch.max(output.data, 1)
                    total_train += target.size(0)
                    correct_train += (predicted == target).sum().item()
                
                train_acc = 100 * correct_train / total_train
                avg_loss = running_loss / len(train_loader)
                
                # Validation phase
                model.eval()
                val_loss = 0.0
                correct_val = 0
                total_val = 0
                
                with torch.no_grad():
                    for data, target in val_loader:
                        data, target = data.to(self.device), target.to(self.device)
                        output = model(data)
                        val_loss += criterion(output, target).item()
                        _, predicted = torch.max(output.data, 1)
                        total_val += target.size(0)
                        correct_val += (predicted == target).sum().item()
                
                val_acc = 100 * correct_val / total_val if total_val > 0 else 0
                
                scheduler.step()
                
                # Log progress
                epoch_log = {
                    'epoch': epoch + 1,
                    'train_loss': avg_loss,
                    'train_acc': train_acc,
                    'val_loss': val_loss / len(val_loader) if len(val_loader) > 0 else 0,
                    'val_acc': val_acc,
                    'timestamp': datetime.utcnow().isoformat()
                }
                training_log.append(epoch_log)
                
                logging.info(f"Epoch {epoch+1}/{epochs}: Train Acc: {train_acc:.2f}%, Val Acc: {val_acc:.2f}%")
                
                # Save best model
                if val_acc > best_val_acc:
                    best_val_acc = val_acc
                    model_path = f'models/custom_trained_model_{self.training_session_id}.pth'
                    os.makedirs('models', exist_ok=True)
                    torch.save(model.state_dict(), model_path)
                
                # Update database
                with app.app_context():
                    training_session = ModelTraining.query.get(self.training_session_id)
                    training_session.epochs_completed = epoch + 1
                    training_session.training_accuracy = train_acc / 100
                    training_session.validation_accuracy = val_acc / 100
                    training_session.training_log = json.dumps(training_log)
                    db.session.commit()
            
            # Complete training
            with app.app_context():
                training_session = ModelTraining.query.get(self.training_session_id)
                training_session.training_status = 'completed'
                training_session.training_end = datetime.utcnow()
                training_session.model_file_path = model_path
                db.session.commit()
            
            return model, self.validator, training_log
            
        except Exception as e:
            logging.error(f"Training failed: {str(e)}")
            
            # Update training session as failed
            with app.app_context():
                training_session = ModelTraining.query.get(self.training_session_id)
                training_session.training_status = 'failed'
                training_session.training_log = json.dumps([{
                    'error': str(e),
                    'timestamp': datetime.utcnow().isoformat()
                }])
                db.session.commit()
            
            raise e

def load_custom_trained_model():
    """Load the latest custom trained model if available"""
    from app import app
    
    with app.app_context():
        # Get the latest completed training session
        latest_training = ModelTraining.query.filter_by(
            training_status='completed'
        ).order_by(ModelTraining.training_end.desc()).first()
        
        if latest_training and latest_training.model_file_path:
            if os.path.exists(latest_training.model_file_path):
                try:
                    model = UNetModel(n_channels=3, n_classes=5)
                    model.load_state_dict(torch.load(latest_training.model_file_path, map_location='cpu'))
                    model.eval()
                    
                    # Create validator from training features
                    validator = create_validator_from_training_data()
                    
                    logging.info(f"Loaded custom trained model: {latest_training.model_version}")
                    return model, validator
                except Exception as e:
                    logging.error(f"Error loading custom trained model: {str(e)}")
    
    return None, None

def create_validator_from_training_data():
    """Create a validator from existing training data"""
    from app import app
    
    try:
        with app.app_context():
            # Get some validated training data for feature extraction
            training_data = TrainingData.query.filter_by(is_validated=True).limit(20).all()
            
            if not training_data:
                return None
            
            validator = TrainingValidator()
            training_features = []
            
            for data_record in training_data:
                if os.path.exists(data_record.file_path):
                    features = validator.extract_image_features(data_record.file_path)
                    if features:
                        training_features.append(features)
            
            if training_features:
                return TrainingValidator(training_features)
    
    except Exception as e:
        logging.error(f"Error creating validator: {str(e)}")
    
    return None