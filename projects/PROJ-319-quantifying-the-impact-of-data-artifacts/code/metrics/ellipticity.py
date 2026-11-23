"""
Ellipticity calculation using second-order moments.
"""
import logging
from typing import Tuple
import numpy as np

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def calculate_ellipticity(image: np.ndarray) -> float:
    """
    Calculate ellipticity from second-order moments.
    e = (a - b) / (a + b)
    """
    y, x = np.ogrid[:image.shape[0], :image.shape[1]]
    center_x = np.sum(x * image) / np.sum(image)
    center_y = np.sum(y * image) / np.sum(image)
    
    # Second moments
    Mxx = np.sum((x - center_x)**2 * image) / np.sum(image)
    Myy = np.sum((y - center_y)**2 * image) / np.sum(image)
    Mxy = np.sum((x - center_x) * (y - center_y) * image) / np.sum(image)
    
    # Eigenvalues of the moment matrix
    trace = Mxx + Myy
    det = Mxx * Myy - Mxy**2
    
    if det <= 0:
        logger.warning("Moment matrix determinant is non-positive. Returning 0 ellipticity.")
        return 0.0
    
    lambda1 = (trace + np.sqrt(trace**2 - 4*det)) / 2
    lambda2 = (trace - np.sqrt(trace**2 - 4*det)) / 2
    
    if lambda1 + lambda2 == 0:
        return 0.0
    
    ellipticity = (lambda1 - lambda2) / (lambda1 + lambda2)
    return float(ellipticity)
