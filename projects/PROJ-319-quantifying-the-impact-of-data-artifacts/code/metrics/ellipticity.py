"""
Ellipticity calculation using second-order moments.
"""
import logging
from typing import Tuple
import numpy as np

def calculate_ellipticity(image: np.ndarray) -> Tuple[float, float]:
    """
    Calculate ellipticity and position angle from second-order moments.
    Returns (ellipticity, angle).
    Ellipticity e = 1 - (b/a).
    """
    y, x = np.indices(image.shape)
    cx = np.sum(x * image) / np.sum(image)
    cy = np.sum(y * image) / np.sum(image)

    dx = x - cx
    dy = y - cy

    # Second moments
    m00 = np.sum(image)
    m20 = np.sum(dx**2 * image) / m00
    m02 = np.sum(dy**2 * image) / m00
    m11 = np.sum(dx * dy * image) / m00

    # Eigenvalues of moment matrix
    # Matrix: [[m20, m11], [m11, m02]]
    trace = m20 + m02
    det = m20 * m02 - m11**2
    delta = np.sqrt(trace**2 - 4 * det)

    lambda1 = (trace + delta) / 2
    lambda2 = (trace - delta) / 2

    # Ensure non-negative
    lambda1 = max(0.0, lambda1)
    lambda2 = max(0.0, lambda2)

    if lambda1 == 0:
        return 0.0, 0.0

    # Ellipticity e = 1 - sqrt(lambda2/lambda1)
    e = 1.0 - np.sqrt(lambda2 / lambda1)
    e = max(0.0, min(1.0, e))

    # Angle
    if m11 == 0 and m20 == m02:
        angle = 0.0
    else:
        angle = 0.5 * np.arctan2(2 * m11, m20 - m02)

    return e, angle
