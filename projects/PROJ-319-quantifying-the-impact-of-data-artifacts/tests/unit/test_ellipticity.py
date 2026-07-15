"""
Unit tests for ellipticity calculation.
"""
import numpy as np
from code.metrics.ellipticity import calculate_ellipticity

def test_ellipticity_calculation():
    """
    Assert that second-order moments yield correct ellipticity for a known synthetic shape.
    (FR-004)
    """
    # Create a synthetic elliptical Gaussian
    y, x = np.mgrid[-10:11, -10:11]
    # Elongated in x direction: sigma_x = 4, sigma_y = 2
    sigma_x, sigma_y = 4.0, 2.0
    image = np.exp(-0.5 * ((x/sigma_x)**2 + (y/sigma_y)**2))
    
    e1, e2 = calculate_ellipticity(image)
    
    # For a pure x-elongated ellipse, e1 should be positive
    # e1 = (Qxx - Qyy) / (Qxx + Qyy)
    # Approximation: (sigma_x^2 - sigma_y^2) / (sigma_x^2 + sigma_y^2)
    expected_e1 = (sigma_x**2 - sigma_y**2) / (sigma_x**2 + sigma_y**2)
    
    # Check e1 is close to expected
    assert np.isclose(e1, expected_e1, atol=0.05), f"Expected ~{expected_e1}, got {e1}"
    # e2 should be near 0 for axis-aligned
    assert np.isclose(e2, 0.0, atol=0.05)
