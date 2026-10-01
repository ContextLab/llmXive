import cv2
import numpy as np
from typing import Optional, Tuple
import logging

logger = logging.getLogger(__name__)

def extract_lesion_area_ratio(image: np.ndarray, threshold: int = 50) -> float:
    """
    Extract the ratio of lesion (diseased) area to total image area.
    
    Heuristic: Lesions in plant diseases often appear darker or desaturated
    compared to healthy green tissue. We use a simple threshold on intensity
    or saturation to approximate the affected area.
    
    Args:
        image: BGR image loaded via cv2.
        threshold: Intensity threshold for lesion detection (0-255).
        
    Returns:
        Ratio of lesion pixels to total pixels (0.0 to 1.0).
    """
    if image.size == 0:
        return 0.0
    
    # Convert to HSV to better segment based on color properties
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    
    # Split channels
    h, s, v = cv2.split(hsv)
    
    # Heuristic: Lesions are often darker (low Value) or less saturated
    # We'll use a combination: low value indicates brown/black necrosis
    # Low saturation might indicate yellowing
    
    # Create a mask for low value (dark spots)
    mask_low_value = cv2.inRange(v, 0, threshold)
    
    # Create a mask for low saturation (yellowing/graying)
    mask_low_saturation = cv2.inRange(s, 0, 50)
    
    # Combine masks (union)
    combined_mask = cv2.bitwise_or(mask_low_value, mask_low_saturation)
    
    # Calculate ratio
    lesion_pixels = cv2.countNonZero(combined_mask)
    total_pixels = image.shape[0] * image.shape[1]
    
    if total_pixels == 0:
        return 0.0
        
    ratio = float(lesion_pixels) / float(total_pixels)
    
    # Sanity check: cap at 1.0 (should not happen but good practice)
    return min(ratio, 1.0)

def extract_necrosis_color_index(image: np.ndarray) -> float:
    """
    Extract a necrosis color index based on color channel ratios.
    
    Necrotic tissue often shifts from green to brown/red.
    We calculate a ratio of Red to Green channels as a proxy for necrosis.
    
    Args:
        image: BGR image loaded via cv2.
        
    Returns:
        Normalized necrosis index (higher values indicate more necrosis).
    """
    if image.size == 0:
        return 0.0
    
    # Split BGR channels
    b, g, r = cv2.split(image)
    
    # Avoid division by zero
    denominator = g.astype(float) + 1e-5
    
    # Ratio of Red to Green (R/G)
    # Healthy leaves are high G, low R. Necrotic leaves are lower G, higher R (brown).
    ratio = r.astype(float) / denominator
    
    # Normalize to 0-1 range roughly (R/G can be > 1)
    # We'll take the mean ratio of the whole image as a global indicator
    mean_ratio = np.mean(ratio)
    
    # Heuristic normalization: typical healthy R/G is < 1, necrotic > 1.
    # Map to a 0-1 scale where 0 is healthy and 1 is severe necrosis.
    # Using a sigmoid-like scaling or simple clipping.
    # Let's use a simple scaling: 0.5 is baseline, 1.0 is max.
    # Normalized = (mean_ratio - 0.5) / 0.5 -> clip to 0-1
    # But R/G can be > 1. Let's just use a log scale or simple clipping.
    
    # Simple approach: Cap at 2.0 (very necrotic), normalize to 1.0
    normalized = np.clip((mean_ratio - 0.5) / 1.0, 0.0, 1.0)
    
    return float(normalized)

def extract_texture_entropy(image: np.ndarray, window_size: int = 8) -> float:
    """
    Extract texture entropy using a local variance/entropy measure.
    
    Texture entropy measures the complexity or randomness of the texture.
    Diseased leaves often have more complex textures (spots, patterns)
    compared to smooth healthy leaves.
    
    Args:
        image: BGR image loaded via cv2.
        window_size: Size of the sliding window for local entropy calculation.
        
    Returns:
        Average entropy value across the image.
    """
    if image.size == 0:
        return 0.0
    
    # Convert to grayscale
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY).astype(np.float32)
    
    # Normalize to 0-1 for entropy calculation
    gray_norm = gray / 255.0
    
    # Pad the image to handle edges
    pad = window_size // 2
    padded = np.pad(gray_norm, ((pad, pad), (pad, pad)), mode='edge')
    
    # Calculate local entropy using a sliding window
    # Entropy = -sum(p * log(p)) for each bin in the histogram
    # We'll use a simplified approach: calculate local variance as a proxy for texture complexity
    # or use a small histogram entropy.
    
    # Using local variance as a robust proxy for texture complexity
    kernel = np.ones((window_size, window_size)) / (window_size * window_size)
    
    # Calculate local mean
    local_mean = cv2.filter2D(padded, -1, kernel)
    local_mean = local_mean[pad:-pad, pad:-pad]
    
    # Calculate local variance: E[X^2] - E[X]^2
    local_mean_sq = cv2.filter2D(padded**2, -1, kernel)
    local_var = local_mean_sq - (local_mean ** 2)
    
    # Ensure non-negative
    local_var = np.maximum(local_var, 0)
    
    # Return the mean variance as a texture metric
    avg_entropy = float(np.mean(local_var))
    
    # Normalize by max possible variance (0.25 for 0-1 data)
    normalized_entropy = avg_entropy / 0.25
    return float(min(normalized_entropy, 1.0))

def extract_features(image_path: str) -> Optional[dict]:
    """
    Extract all visual features from a single image.
    
    Args:
        image_path: Path to the image file.
        
    Returns:
        Dictionary with extracted features, or None if extraction fails.
    """
    try:
        image = cv2.imread(image_path)
        if image is None:
            logger.warning(f"Could not read image: {image_path}")
            return None
        
        features = {
            'lesion_area_ratio': extract_lesion_area_ratio(image),
            'necrosis_color_index': extract_necrosis_color_index(image),
            'texture_entropy': extract_texture_entropy(image)
        }
        
        return features
    except Exception as e:
        logger.error(f"Error extracting features from {image_path}: {e}")
        return None
