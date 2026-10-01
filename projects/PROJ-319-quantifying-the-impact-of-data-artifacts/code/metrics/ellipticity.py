"""
Ellipticity calculation using second-order moments.
"""
import logging
from typing import Tuple
import numpy as np

def calculate_ellipticity(image: np.ndarray) -> float:
    """
    Calculate ellipticity from second-order moments.
    Ellipticity e = 1 - b/a, where a and b are the major and minor axes.
    """
    y, x = np.indices(image.shape)
    
    # Center of light
    total_flux = np.sum(image)
    if total_flux == 0:
        return 0.0
    
    x_bar = np.sum(x * image) / total_flux
    y_bar = np.sum(y * image) / total_flux
    
    # Second moments
    m_xx = np.sum((x - x_bar)**2 * image) / total_flux
    m_yy = np.sum((y - y_bar)**2 * image) / total_flux
    m_xy = np.sum((x - x_bar) * (y - y_bar) * image) / total_flux
    
    # Eigenvalues of the moment matrix
    # Matrix: [[m_xx, m_xy], [m_xy, m_yy]]
    trace = m_xx + m_yy
    det = m_xx * m_yy - m_xy**2
    
    if det <= 0:
        return 0.0
    
    # Eigenvalues
    discriminant = np.sqrt(trace**2 - 4 * det)
    lambda1 = (trace + discriminant) / 2
    lambda2 = (trace - discriminant) / 2
    
    if lambda1 <= 0 or lambda2 <= 0:
        return 0.0
    
    # a^2 ~ lambda1, b^2 ~ lambda2 (assuming lambda1 >= lambda2)
    a = np.sqrt(lambda1)
    b = np.sqrt(lambda2)
    
    if a == 0:
        return 0.0
    
    ellipticity = 1 - (b / a)
    return max(0.0, min(1.0, ellipticity))
