import numpy as np
import cv2
from scipy.stats import entropy
from typing import Tuple, Optional

def calculate_edge_density(image_path: str, low_threshold: int = 50, high_threshold: int = 150, kernel_size: int = 3) -> float:
    """
    Calculate edge density using Canny edge detection.
    
    Args:
        image_path: Path to the image file
        low_threshold: Lower threshold for Canny
        high_threshold: Upper threshold for Canny
        kernel_size: Size of the Sobel kernel
        
    Returns:
        Edge density as a float between 0 and 1
    """
    img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    if img is None:
        raise ValueError(f"Could not load image: {image_path}")
    
    # Apply Gaussian blur to reduce noise
    blurred = cv2.GaussianBlur(img, (5, 5), 0)
    
    # Apply Canny edge detection
    edges = cv2.Canny(blurred, low_threshold, high_threshold)
    
    # Calculate edge density
    total_pixels = img.shape[0] * img.shape[1]
    edge_pixels = np.count_nonzero(edges)
    density = edge_pixels / total_pixels
    
    return density

def calculate_entropy(image_path: str) -> float:
    """
    Calculate entropy of grayscale histogram.
    
    Args:
        image_path: Path to the image file
        
    Returns:
        Entropy value
    """
    img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    if img is None:
        raise ValueError(f"Could not load image: {image_path}")
    
    # Calculate histogram
    hist = cv2.calcHist([img], [0], None, [256], [0, 256])
    hist = hist.flatten()
    
    # Normalize histogram to get probabilities
    prob = hist / np.sum(hist)
    
    # Filter out zero probabilities to avoid log(0)
    prob = prob[prob > 0]
    
    # Calculate entropy
    ent = entropy(prob, base=2)
    
    return ent

def calculate_fractal_dim(image_path: str, min_box_size: int = 2, max_box_size: int = 64) -> float:
    """
    Calculate fractal dimension using box-counting method.
    
    Args:
        image_path: Path to the image file
        min_box_size: Minimum box size in pixels
        max_box_size: Maximum box size in pixels
        
    Returns:
        Fractal dimension value
    """
    img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    if img is None:
        raise ValueError(f"Could not load image: {image_path}")
    
    # Apply edge detection to create a binary edge map
    blurred = cv2.GaussianBlur(img, (5, 5), 0)
    edges = cv2.Canny(blurred, 50, 150)
    
    # Convert to binary (0 and 1)
    binary = (edges > 0).astype(float)
    
    # Box counting
    box_sizes = []
    counts = []
    
    # Use logarithmically spaced box sizes
    for exp in np.linspace(np.log2(min_box_size), np.log2(max_box_size), 10):
        box_size = int(2 ** exp)
        if box_size < 1 or box_size >= min(binary.shape):
            continue
            
        box_sizes.append(box_size)
        
        # Count boxes that contain edges
        count = 0
        h, w = binary.shape
        for i in range(0, h, box_size):
            for j in range(0, w, box_size):
                if np.sum(binary[i:i+box_size, j:j+box_size]) > 0:
                    count += 1
        
        counts.append(count)
    
    if len(box_sizes) < 2:
        # Not enough data points for regression
        return 1.5  # Default value for 2D images
    
    # Calculate fractal dimension via linear regression
    log_sizes = np.log(1 / np.array(box_sizes))
    log_counts = np.log(counts)
    
    # Linear regression
    slope, intercept = np.polyfit(log_sizes, log_counts, 1)
    fractal_dim = slope
    
    # Clamp to valid physical range for 2D images [1, 2]
    fractal_dim = np.clip(fractal_dim, 1.0, 2.0)
    
    return fractal_dim

def process_image_vectorized(image_path: str) -> Tuple[float, float, float]:
    """
    Process an image and return all three complexity metrics.
    
    Args:
        image_path: Path to the image file
        
    Returns:
        Tuple of (edge_density, entropy, fractal_dim)
    """
    edge_density = calculate_edge_density(image_path)
    image_entropy = calculate_entropy(image_path)
    fractal_dim = calculate_fractal_dim(image_path)
    
    return edge_density, image_entropy, fractal_dim
