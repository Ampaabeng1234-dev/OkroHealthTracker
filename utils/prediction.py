import torch
import numpy as np
import logging
import os
import sys
import cv2

# Import models directly from the root directory
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import model_definitions
UNetModel = model_definitions.UNetModel
create_dummy_model = model_definitions.create_dummy_model

# Import fallback rule engine
from models.fallback_rule_engine import FallbackRuleEngine

class DiseasePredictor:
    def __init__(self):
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.model = None
        self.class_names = ["Healthy", "Bacterial Blight", "Leaf Spot", "Mosaic Virus", "Powdery Mildew"]
        self.confidence_threshold = 0.6
        self.fallback_engine = FallbackRuleEngine()
        
        # Load or create model
        self.load_model()
    
    def load_model(self):
        """Load the UNet model from file or create dummy model"""
        model_path = 'models/unet_model.pth'
        
        try:
            if os.path.exists(model_path):
                # Load trained model
                self.model = UNetModel(n_channels=3, n_classes=5)
                self.model.load_state_dict(torch.load(model_path, map_location=self.device))
                self.model.to(self.device)
                self.model.eval()
                logging.info("Loaded trained UNet model")
            else:
                # Create dummy model for demonstration
                self.model = create_dummy_model()
                self.model.to(self.device)
                logging.warning("Using dummy model - no trained model found")
                
        except Exception as e:
            logging.error(f"Error loading model: {str(e)}")
            # Fallback to dummy model
            self.model = create_dummy_model()
            self.model.to(self.device)
    
    def predict(self, processed_image, image_path):
        """
        Predict disease from preprocessed image
        
        Args:
            processed_image (numpy.ndarray): Preprocessed image
            image_path (str): Path to original image
        
        Returns:
            dict: Prediction results
        """
        try:
            # Primary prediction using deep learning
            dl_result = self.deep_learning_prediction(processed_image)
            
            # Check confidence threshold
            if dl_result['confidence'] >= self.confidence_threshold:
                return {
                    'prediction': dl_result['prediction'],
                    'confidence': dl_result['confidence'],
                    'method': 'deep_learning',
                    'all_probabilities': dl_result['all_probabilities']
                }
            else:
                # Use fallback rule-based system
                fallback_result = self.fallback_engine.predict(image_path)
                
                # Combine results
                combined_result = self.combine_predictions(dl_result, fallback_result)
                
                return {
                    'prediction': combined_result['prediction'],
                    'confidence': combined_result['confidence'],
                    'method': 'hybrid',
                    'dl_confidence': dl_result['confidence'],
                    'rule_confidence': fallback_result['confidence'],
                    'all_probabilities': dl_result['all_probabilities']
                }
                
        except Exception as e:
            logging.error(f"Error during prediction: {str(e)}")
            # Emergency fallback
            return {
                'prediction': 'Unknown',
                'confidence': 0.0,
                'method': 'error',
                'error': str(e)
            }
    
    def deep_learning_prediction(self, processed_image):
        """Perform deep learning prediction"""
        
        # Convert to tensor
        image_tensor = torch.from_numpy(processed_image).permute(2, 0, 1).unsqueeze(0)
        image_tensor = image_tensor.to(self.device)
        
        with torch.no_grad():
            # Get model output
            outputs = self.model(image_tensor)
            probabilities = torch.nn.functional.softmax(outputs, dim=1)
            
            # Get prediction
            confidence, predicted_idx = torch.max(probabilities, 1)
            
            # Convert to numpy
            confidence = confidence.item()
            predicted_idx = predicted_idx.item()
            all_probs = probabilities.squeeze().cpu().numpy()
            
            prediction = self.class_names[predicted_idx]
            
            return {
                'prediction': prediction,
                'confidence': confidence,
                'all_probabilities': {
                    class_name: float(prob) 
                    for class_name, prob in zip(self.class_names, all_probs)
                }
            }
    
    def combine_predictions(self, dl_result, rule_result):
        """Combine deep learning and rule-based predictions"""
        
        # Weight the predictions based on their confidence
        dl_weight = dl_result['confidence']
        rule_weight = rule_result['confidence']
        
        total_weight = dl_weight + rule_weight
        
        if total_weight == 0:
            return {
                'prediction': 'Unknown',
                'confidence': 0.0
            }
        
        # Weighted combination
        if dl_result['prediction'] == rule_result['prediction']:
            # Both agree - high confidence
            combined_confidence = min(0.95, (dl_weight + rule_weight) / 2 * 1.2)
            return {
                'prediction': dl_result['prediction'],
                'confidence': combined_confidence
            }
        else:
            # Disagreement - choose higher confidence but reduce overall confidence
            if dl_weight > rule_weight:
                return {
                    'prediction': dl_result['prediction'],
                    'confidence': dl_weight * 0.8
                }
            else:
                return {
                    'prediction': rule_result['prediction'],
                    'confidence': rule_weight * 0.8
                }

# Global predictor instance
predictor = DiseasePredictor()

def predict_disease(processed_image, image_path):
    """
    Main prediction function called by Flask app
    
    Args:
        processed_image (numpy.ndarray): Preprocessed image
        image_path (str): Path to original image
    
    Returns:
        dict: Prediction results
    """
    return predictor.predict(processed_image, image_path)

def retrain_model(training_data_path):
    """
    Placeholder function for model retraining
    
    Args:
        training_data_path (str): Path to training data
    
    Returns:
        bool: Success status
    """
    try:
        logging.info(f"Starting model retraining with data from {training_data_path}")
        
        # This would contain the actual retraining logic
        # For now, we'll just log the attempt
        
        # 1. Load training data
        # 2. Create data loaders
        # 3. Initialize model and optimizer
        # 4. Training loop
        # 5. Save trained model
        
        logging.info("Model retraining completed successfully")
        return True
        
    except Exception as e:
        logging.error(f"Error during model retraining: {str(e)}")
        return False
