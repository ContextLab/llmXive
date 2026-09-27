"""
Asymmetry calculation (Conselice 2003 definition).
"""
import logging
from typing import Tuple, Optional
import numpy as np

def calculate_asymmetry(image: np.ndarray) -> float:
    """
    Calculate the A-statistic (Asymmetry) as defined by Conselice (2003).
    A = sum |I(x,y) - I_180(x,y)| / sum |I(x,y)|
    where I_180 is the image rotated by 180 degrees.
    """
    # Center of image
    h, w = image.shape
    cy, cx = h // 2, w // 2

    # Rotate 180 degrees
    # np.rot90 with k=2 rotates 180
    img_rot = np.rot90(image, k=2)

    # Calculate numerator and denominator
    numerator = np.sum(np.abs(image - img_rot))
    denominator = np.sum(np.abs(image))

    if denominator == 0:
        return 0.0

    return numerator / denominator
