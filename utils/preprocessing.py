import cv2
import numpy as np
from PIL import Image
import logging

def preprocess_image(image_path, target_size=(224, 224)):
    """
    Preprocess uploaded image for disease detection
    
    Args:
        image_path (str): Path to the uploaded image
        target_size (tuple): Target size for resizing (width, height)
    
    Returns:
        numpy.ndarray: Preprocessed image array
    """
    try:
        # Load image using OpenCV
        image = cv2.imread(image_path)
        if image is None:
            raise ValueError(f"Could not load image from {image_path}")
        
        # Convert BGR to RGB
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        
        # Resize image
        image = cv2.resize(image, target_size, interpolation=cv2.INTER_LANCZOS4)
        
        # Color normalization
        image = image.astype(np.float32) / 255.0
        
        # Enhance edges using Unsharp masking
        image = enhance_edges(image)
        
        # Normalize to standard range
        image = normalize_image(image)
        
        logging.debug(f"Successfully preprocessed image: {image_path}")
        return image
        
    except Exception as e:
        logging.error(f"Error preprocessing image {image_path}: {str(e)}")
        raise

def enhance_edges(image):
    """
    Enhance edges in the image using Unsharp masking
    
    Args:
        image (numpy.ndarray): Input image array
    
    Returns:
        numpy.ndarray: Edge-enhanced image
    """
    # Convert to uint8 for OpenCV operations
    img_uint8 = (image * 255).astype(np.uint8)
    
    # Create Gaussian blur
    gaussian = cv2.GaussianBlur(img_uint8, (5, 5), 1.0)
    
    # Unsharp masking
    unsharp = cv2.addWeighted(img_uint8, 1.5, gaussian, -0.5, 0)
    
    # Convert back to float32
    enhanced = unsharp.astype(np.float32) / 255.0
    
    return enhanced

def normalize_image(image):
    """
    Normalize image using standard ImageNet statistics
    
    Args:
        image (numpy.ndarray): Input image array
    
    Returns:
        numpy.ndarray: Normalized image
    """
    # ImageNet statistics
    mean = np.array([0.485, 0.456, 0.406])
    std = np.array([0.229, 0.224, 0.225])
    
    # Normalize
    normalized = (image - mean) / std
    
    return normalized

def extract_leaf_features(image_path):
    """
    Extract handcrafted features from leaf image for fallback system
    
    Args:
        image_path (str): Path to the image
    
    Returns:
        dict: Dictionary of extracted features
    """
    try:
        # Load image
        image = cv2.imread(image_path)
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        
        # Convert to HSV for color analysis
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        
        # Extract color features
        color_features = extract_color_features(hsv)
        
        # Extract shape features
        shape_features = extract_shape_features(image)
        
        # Extract texture features
        texture_features = extract_texture_features(image)
        
        features = {
            **color_features,
            **shape_features,
            **texture_features
        }
        
        return features
        
    except Exception as e:
        logging.error(f"Error extracting features from {image_path}: {str(e)}")
        return {}

def extract_color_features(hsv_image):
    """Extract color-based features from HSV image"""
    
    # Define color ranges for healthy green
    lower_green = np.array([40, 40, 40])
    upper_green = np.array([80, 255, 255])
    
    # Define color ranges for diseased yellow/brown
    lower_yellow = np.array([15, 40, 40])
    upper_yellow = np.array([35, 255, 255])
    
    # Create masks
    green_mask = cv2.inRange(hsv_image, lower_green, upper_green)
    yellow_mask = cv2.inRange(hsv_image, lower_yellow, upper_yellow)
    
    # Calculate ratios
    total_pixels = hsv_image.shape[0] * hsv_image.shape[1]
    green_ratio = np.sum(green_mask > 0) / total_pixels
    yellow_ratio = np.sum(yellow_mask > 0) / total_pixels
    
    # Calculate average hue and saturation
    avg_hue = np.mean(hsv_image[:, :, 0])
    avg_saturation = np.mean(hsv_image[:, :, 1])
    avg_value = np.mean(hsv_image[:, :, 2])
    
    return {
        'green_ratio': green_ratio,
        'yellow_ratio': yellow_ratio,
        'avg_hue': avg_hue,
        'avg_saturation': avg_saturation,
        'avg_value': avg_value,
        'green_yellow_ratio': green_ratio / max(yellow_ratio, 0.001)
    }

def extract_shape_features(image):
    """Extract shape-based features from image"""
    
    # Convert to grayscale
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    
    # Apply threshold to get binary image
    _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    
    # Find contours
    contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    if len(contours) == 0:
        return {
            'leaf_area': 0,
            'perimeter': 0,
            'aspect_ratio': 0,
            'circularity': 0,
            'solidity': 0
        }
    
    # Get largest contour (assumed to be the leaf)
    largest_contour = max(contours, key=cv2.contourArea)
    
    # Calculate features
    area = cv2.contourArea(largest_contour)
    perimeter = cv2.arcLength(largest_contour, True)
    
    # Bounding rectangle
    x, y, w, h = cv2.boundingRect(largest_contour)
    aspect_ratio = w / h if h > 0 else 0
    
    # Circularity
    circularity = 4 * np.pi * area / (perimeter * perimeter) if perimeter > 0 else 0
    
    # Solidity (convex hull)
    hull = cv2.convexHull(largest_contour)
    hull_area = cv2.contourArea(hull)
    solidity = area / hull_area if hull_area > 0 else 0
    
    return {
        'leaf_area': area,
        'perimeter': perimeter,
        'aspect_ratio': aspect_ratio,
        'circularity': circularity,
        'solidity': solidity
    }

def extract_texture_features(image):
    """Extract texture-based features from image"""
    
    # Convert to grayscale
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    
    # Calculate edge density using Canny edge detection
    edges = cv2.Canny(gray, 50, 150)
    edge_density = np.sum(edges > 0) / (edges.shape[0] * edges.shape[1])
    
    # Calculate local binary pattern-like feature
    lbp_var = calculate_lbp_variance(gray)
    
    # Calculate gradient magnitude variance
    grad_x = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
    grad_y = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)
    grad_magnitude = np.sqrt(grad_x**2 + grad_y**2)
    grad_variance = np.var(grad_magnitude)
    
    return {
        'edge_density': edge_density,
        'lbp_variance': lbp_var,
        'gradient_variance': grad_variance
    }

def calculate_lbp_variance(gray_image):
    """Calculate Local Binary Pattern variance"""
    
    # Simple LBP-like calculation
    rows, cols = gray_image.shape
    lbp_values = []
    
    for i in range(1, rows-1):
        for j in range(1, cols-1):
            center = gray_image[i, j]
            binary_string = ""
            
            # 8-neighborhood
            neighbors = [
                gray_image[i-1, j-1], gray_image[i-1, j], gray_image[i-1, j+1],
                gray_image[i, j+1], gray_image[i+1, j+1], gray_image[i+1, j],
                gray_image[i+1, j-1], gray_image[i, j-1]
            ]
            
            for neighbor in neighbors:
                binary_string += "1" if neighbor >= center else "0"
            
            lbp_values.append(int(binary_string, 2))
    
    return np.var(lbp_values) if lbp_values else 0
