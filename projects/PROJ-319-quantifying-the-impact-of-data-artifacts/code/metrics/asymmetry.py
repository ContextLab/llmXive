"""
Asymmetry calculation using Conselice (2003) definition.
"""
import logging
from typing import Tuple, Optional
import numpy as np

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def calculate_asymmetry(image: np.ndarray) -> float:
    """
    Calculate asymmetry A-statistic: A = sum(|I - I_rotated|) / sum(|I|)
    """
    # Rotate 180 degrees
    rotated = np.rot90(image, 2)
    
    numerator = np.sum(np.abs(image - rotated))
    denominator = np.sum(np.abs(image))
    
    if denominator == 0:
        logger.warning("Image sum is zero. Returning 0 asymmetry.")
        return 0.0
    
    return float(numerator / denominator)
