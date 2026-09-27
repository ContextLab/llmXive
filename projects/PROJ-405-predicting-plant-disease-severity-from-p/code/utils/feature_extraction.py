"""
OpenCV feature extraction utilities for plant disease severity.

Implements:
- Lesion Area Ratio
- Necrosis Color Index
- Texture Entropy
"""

import cv2
import numpy as np
from typing import Optional

def extract_lesion_area_ratio(image: np.ndarray, mask: np.ndarray) -> float:
    """
    Calculates the ratio of lesion pixels to total valid pixels.

    Args:
        image: BGR image (not strictly used for calculation if mask is provided,
               but kept for interface consistency).
        mask: Binary mask where 255 indicates lesion pixels.

    Returns:
        float: Ratio of lesion area to total area.
    """
    if mask is None or np.sum(mask) == 0:
        return 0.0

    total_pixels = mask.size
    lesion_pixels = np.count_nonzero(mask)
    
    return float(lesion_pixels) / float(total_pixels)

def extract_necrosis_color_index(image: np.ndarray, mask: np.ndarray) -> float:
    """
    Calculates a necrosis color index based on RGB values in the lesion area.
    
    Necrosis is typically characterized by dark, brownish colors.
    This implementation uses a simple weighted sum of normalized RGB channels
    for pixels within the mask.
    
    Formula: Index = (R + G + B) / 3 / 255.0 (Normalized intensity)
    Higher values indicate brighter (less necrotic), lower values indicate darker (more necrotic).
    We invert this so higher index = more necrotic.
    
    Args:
        image: BGR image.
        mask: Binary mask where 255 indicates lesion pixels.

    Returns:
        float: Necrosis color index (0.0 to 1.0, where 1.0 is most necrotic).
    """
    if mask is None or np.sum(mask) == 0:
        return 0.0

    # Ensure image is float for calculation
    img_float = image.astype(np.float32)
    
    # Extract lesion pixels
    lesion_pixels = img_float[mask == 255]
    
    if len(lesion_pixels) == 0:
        return 0.0

    # Calculate mean intensity (BGR)
    mean_bgr = np.mean(lesion_pixels, axis=0)
    
    # Normalize to 0-1
    normalized_intensity = np.mean(mean_bgr) / 255.0
    
    # Invert: Darker (lower intensity) -> Higher necrosis index
    # Necrosis is dark, so low intensity. We want high index for low intensity.
    necrosis_index = 1.0 - normalized_intensity
    
    return float(necrosis_index)

def extract_texture_entropy(image: np.ndarray, mask: Optional[np.ndarray] = None) -> float:
    """
    Calculates the Shannon entropy of the grayscale intensity histogram.
    
    Args:
        image: Grayscale or BGR image (converted to grayscale internally).
        mask: Optional binary mask. If provided, only calculates entropy for masked pixels.

    Returns:
        float: Shannon entropy value.
    """
    # Convert to grayscale if needed
    if len(image.shape) == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        gray = image

    if mask is not None:
        # Apply mask
        masked_pixels = gray[mask == 255]
        if len(masked_pixels) == 0:
            return 0.0
        histogram, _ = np.histogram(masked_pixels, bins=256, range=(0, 256))
    else:
        histogram, _ = np.histogram(gray.flatten(), bins=256, range=(0, 256))

    # Normalize histogram to get probabilities
    prob = histogram / float(np.sum(histogram))
    
    # Remove zero probabilities to avoid log(0)
    prob = prob[prob > 0]
    
    # Calculate Shannon entropy
    entropy = -np.sum(prob * np.log2(prob))
    
    return float(entropy)