import numpy as np
import cv2
from scipy.stats import entropy
from typing import Tuple, Optional

def calculate_edge_density(image: np.ndarray) -> float:
    """
    Calculate edge density using Canny edge detection.
    
    Args:
        image: Input image (grayscale or BGR).
        
    Returns:
        Edge density (ratio of edge pixels to total pixels).
    """
    if image.ndim == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        gray = image.copy()
        
    gray = gray.astype(np.uint8)
    edges = cv2.Canny(gray, 100, 200)
    edge_pixels = np.count_nonzero(edges)
    total_pixels = edges.size
    return float(edge_pixels / total_pixels)

def calculate_entropy(image: np.ndarray) -> float:
    """
    Calculate entropy of the grayscale histogram.
    
    Args:
        image: Input image (grayscale or BGR).
        
    Returns:
        Entropy value.
    """
    if image.ndim == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        gray = image.copy()
        
    hist, _ = np.histogram(gray.flatten(), bins=256, range=(0, 256))
    hist = hist.astype(float) / hist.sum()
    hist = hist[hist > 0]
    return float(entropy(hist))

def calculate_fractal_dim(image: np.ndarray) -> float:
    """
    Calculate fractal dimension via box-counting method.
    
    Args:
        image: Input image (grayscale or BGR).
        
    Returns:
        Fractal dimension (clamped to [1.0, 2.0]).
    """
    if image.ndim == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        gray = image.copy()
        
    gray = gray.astype(np.uint8)
    _, binary = cv2.threshold(gray, 128, 255, cv2.THRESH_BINARY)
    
    h, w = binary.shape
    sizes = []
    counts = []
    
    # Box sizes: powers of 2, from large to small
    max_size = min(h, w)
    min_size = 2
    k = 0
    while True:
        box_size = max_size // (2 ** k)
        if box_size < min_size:
            break
        sizes.append(box_size)
        
        # Count boxes with at least one edge pixel
        count = 0
        for i in range(0, h, box_size):
            for j in range(0, w, box_size):
                box = binary[i:i+box_size, j:j+box_size]
                if np.any(box > 0):
                    count += 1
        counts.append(count)
        k += 1
        
    if len(sizes) < 2:
        return 1.5
        
    log_sizes = np.log(1.0 / np.array(sizes))
    log_counts = np.log(counts)
    
    # Linear regression to estimate slope
    slope, _ = np.polyfit(log_sizes, log_counts, 1)
    fractal_dim = float(slope)
    
    # Clamp to valid range [1.0, 2.0] for 2D images
    return max(1.0, min(2.0, fractal_dim))

def process_image_vectorized(image: np.ndarray) -> Tuple[float, float, float]:
    """
    Vectorized wrapper for processing a single image.
    Returns edge_density, entropy, fractal_dim.
    """
    edge_density = calculate_edge_density(image)
    entropy_val = calculate_entropy(image)
    fractal_dim = calculate_fractal_dim(image)
    return edge_density, entropy_val, fractal_dim
