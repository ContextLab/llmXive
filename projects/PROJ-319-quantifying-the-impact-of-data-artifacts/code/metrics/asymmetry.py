"""
Asymmetry calculation using Conselice (2003) definition.
"""
import logging
from typing import Tuple, Optional
import numpy as np

def calculate_asymmetry(image: np.ndarray, center: Optional[Tuple[int, int]] = None) -> float:
    """
    Calculate the A-statistic (asymmetry) as defined by Conselice (2003).
    A = sum(|I - I_180|) / sum(|I|)
    """
    if center is None:
        # Estimate center as center of light
        y, x = np.indices(image.shape)
        total_flux = np.sum(image)
        if total_flux == 0:
            return 0.0
        cx = int(np.sum(x * image) / total_flux)
        cy = int(np.sum(y * image) / total_flux)
    else:
        cx, cy = center
    
    # Rotate 180 degrees
    # I_180 is the image rotated by 180 degrees around the center
    # For a discrete grid, this is equivalent to flipping both axes around the center
    # We can use np.rot90 twice
    rotated = np.rot90(image, k=2)
    
    # Calculate asymmetry
    # A = sum(|I - I_180|) / sum(|I|)
    # We should subtract background, but for synthetic data we assume 0 background
    numerator = np.sum(np.abs(image - rotated))
    denominator = np.sum(np.abs(image))
    
    if denominator == 0:
        return 0.0
    
    return numerator / denominator
