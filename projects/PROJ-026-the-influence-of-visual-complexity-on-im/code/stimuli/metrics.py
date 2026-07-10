"""
Metrics calculation for visual complexity.
"""
import numpy as np
import cv2
from scipy.stats import entropy

def calculate_edge_density(image_path: str) -> float:
    """
    Calculate edge density using Canny edge detection.
    
    Args:
        image_path: Path to the image file.
        
    Returns:
        Edge density as a float between 0 and 1.
    """
    img = cv2.imread(image_path)
    if img is None:
        raise ValueError(f"Could not read image: {image_path}")
        
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    edges = cv2.Canny(gray, 50, 150)
    
    edge_pixels = np.count_nonzero(edges)
    total_pixels = edges.size
    
    return edge_pixels / total_pixels

def calculate_entropy(image_path: str) -> float:
    """
    Calculate entropy of the grayscale histogram.
    
    Args:
        image_path: Path to the image file.
        
    Returns:
        Entropy value.
    """
    img = cv2.imread(image_path)
    if img is None:
        raise ValueError(f"Could not read image: {image_path}")
        
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    hist, _ = np.histogram(gray, bins=256, range=(0, 256))
    
    # Normalize histogram to get probabilities
    probs = hist / hist.sum()
    probs = probs[probs > 0]  # Remove zeros to avoid log(0)
    
    return entropy(probs)

def calculate_fractal_dim(image_path: str) -> float:
    """
    Calculate fractal dimension using box-counting method.
    
    Args:
        image_path: Path to the image file.
        
    Returns:
        Fractal dimension value.
    """
    img = cv2.imread(image_path)
    if img is None:
        raise ValueError(f"Could not read image: {image_path}")
        
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    _, binary = cv2.threshold(gray, 128, 255, cv2.THRESH_BINARY)
    
    # Box counting
    sizes = []
    counts = []
    
    h, w = binary.shape
    max_size = min(h, w)
    
    # Use powers of 2 for box sizes
    for k in range(1, 6):
        size = max_size // (2 ** k)
        if size <= 0:
            break
            
        # Count boxes with at least one non-zero pixel
        count = 0
        for i in range(0, h, size):
            for j in range(0, w, size):
                box = binary[i:i+size, j:j+size]
                if np.any(box > 0):
                    count += 1
                    
        sizes.append(size)
        counts.append(count)
        
    if len(sizes) < 2:
        return 1.5  # Default value if not enough data
        
    # Fit line to log-log plot
    log_sizes = np.log(sizes)
    log_counts = np.log(counts)
    
    slope, _ = np.polyfit(log_sizes, log_counts, 1)
    fractal_dim = -slope
    
    # Clamp to reasonable range [1.0, 2.0]
    return np.clip(fractal_dim, 1.0, 2.0)
