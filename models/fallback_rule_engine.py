import cv2
import numpy as np
import logging
from utils.preprocessing import extract_leaf_features

class FallbackRuleEngine:
    """
    Rule-based fallback system for okra leaf disease detection
    Uses handcrafted features and heuristic rules
    """
    
    def __init__(self):
        self.disease_rules = self.load_disease_rules()
    
    def load_disease_rules(self):
        """Define rule-based criteria for each disease"""
        return {
            'Healthy': {
                'green_ratio_min': 0.6,
                'yellow_ratio_max': 0.1,
                'green_yellow_ratio_min': 6.0,
                'edge_density_max': 0.15,
                'circularity_min': 0.3
            },
            'Bacterial Blight': {
                'yellow_ratio_min': 0.2,
                'edge_density_min': 0.2,
                'green_ratio_max': 0.5,
                'avg_hue_range': (15, 35),  # Yellow-brown range
                'solidity_max': 0.8
            },
            'Leaf Spot': {
                'edge_density_min': 0.25,
                'circularity_max': 0.6,
                'yellow_ratio_min': 0.15,
                'lbp_variance_min': 100,
                'green_yellow_ratio_max': 3.0
            },
            'Mosaic Virus': {
                'lbp_variance_min': 150,
                'gradient_variance_min': 500,
                'green_ratio_range': (0.3, 0.7),
                'avg_saturation_max': 150,
                'irregular_pattern': True
            },
            'Powdery Mildew': {
                'avg_value_min': 180,  # Bright appearance
                'avg_saturation_max': 100,  # Low saturation (whitish)
                'green_ratio_max': 0.4,
                'yellow_ratio_min': 0.1,
                'edge_density_max': 0.1
            }
        }
    
    def predict(self, image_path):
        """
        Predict disease using rule-based approach
        
        Args:
            image_path (str): Path to the image
        
        Returns:
            dict: Prediction result with confidence
        """
        try:
            # Extract features
            features = extract_leaf_features(image_path)
            
            if not features:
                return {
                    'prediction': 'Unknown',
                    'confidence': 0.0,
                    'features': {}
                }
            
            # Apply rules for each disease
            disease_scores = {}
            
            for disease, rules in self.disease_rules.items():
                score = self.calculate_disease_score(features, rules)
                disease_scores[disease] = score
            
            # Find best match
            best_disease = max(disease_scores, key=disease_scores.get)
            best_score = disease_scores[best_disease]
            
            # Convert score to confidence (0-1 range)
            confidence = min(0.8, best_score / 100.0)  # Cap at 0.8 for rule-based
            
            return {
                'prediction': best_disease,
                'confidence': confidence,
                'features': features,
                'disease_scores': disease_scores
            }
            
        except Exception as e:
            logging.error(f"Error in fallback rule engine: {str(e)}")
            return {
                'prediction': 'Unknown',
                'confidence': 0.0,
                'error': str(e)
            }
    
    def calculate_disease_score(self, features, rules):
        """
        Calculate score for a specific disease based on rules
        
        Args:
            features (dict): Extracted image features
            rules (dict): Disease-specific rules
        
        Returns:
            float: Disease score (0-100)
        """
        score = 0
        max_score = 0
        
        for rule_name, rule_value in rules.items():
            max_score += 10  # Each rule contributes max 10 points
            
            if rule_name.endswith('_min'):
                feature_name = rule_name[:-4]
                if feature_name in features and features[feature_name] >= rule_value:
                    score += 10
            
            elif rule_name.endswith('_max'):
                feature_name = rule_name[:-4]
                if feature_name in features and features[feature_name] <= rule_value:
                    score += 10
            
            elif rule_name.endswith('_range'):
                feature_name = rule_name[:-6]
                if feature_name in features:
                    min_val, max_val = rule_value
                    if min_val <= features[feature_name] <= max_val:
                        score += 10
            
            elif rule_name == 'irregular_pattern':
                # Special case for mosaic virus
                if self.detect_irregular_pattern(features):
                    score += 10
        
        # Calculate percentage score
        if max_score > 0:
            return (score / max_score) * 100
        else:
            return 0
    
    def detect_irregular_pattern(self, features):
        """
        Detect irregular patterns typical of mosaic virus
        
        Args:
            features (dict): Extracted features
        
        Returns:
            bool: True if irregular pattern detected
        """
        # High variance in texture features indicates irregular patterns
        high_lbp_var = features.get('lbp_variance', 0) > 150
        high_grad_var = features.get('gradient_variance', 0) > 500
        irregular_shape = features.get('circularity', 1) < 0.5
        
        return high_lbp_var and high_grad_var and irregular_shape
    
    def explain_prediction(self, features, prediction, disease_scores):
        """
        Generate explanation for the rule-based prediction
        
        Args:
            features (dict): Extracted features
            prediction (str): Predicted disease
            disease_scores (dict): Scores for all diseases
        
        Returns:
            str: Human-readable explanation
        """
        explanations = []
        
        if prediction == 'Healthy':
            if features.get('green_ratio', 0) > 0.6:
                explanations.append("High proportion of healthy green color")
            if features.get('yellow_ratio', 1) < 0.1:
                explanations.append("Low presence of yellowing")
        
        elif prediction == 'Bacterial Blight':
            if features.get('yellow_ratio', 0) > 0.2:
                explanations.append("Significant yellowing observed")
            if features.get('edge_density', 0) > 0.2:
                explanations.append("High edge density indicating lesions")
        
        elif prediction == 'Leaf Spot':
            if features.get('edge_density', 0) > 0.25:
                explanations.append("High edge density from spot boundaries")
            if features.get('lbp_variance', 0) > 100:
                explanations.append("Irregular texture patterns")
        
        elif prediction == 'Mosaic Virus':
            if features.get('lbp_variance', 0) > 150:
                explanations.append("Highly irregular texture patterns")
            if features.get('gradient_variance', 0) > 500:
                explanations.append("Variable color gradients")
        
        elif prediction == 'Powdery Mildew':
            if features.get('avg_value', 0) > 180:
                explanations.append("Bright, whitish appearance")
            if features.get('avg_saturation', 255) < 100:
                explanations.append("Low color saturation")
        
        if explanations:
            return "; ".join(explanations)
        else:
            return f"Based on feature analysis (confidence: {disease_scores.get(prediction, 0):.1f}%)"
