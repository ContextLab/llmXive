"""Unit tests for ellipticity calculation in code/metrics/ellipticity.py.

These tests verify that the ellipticity calculation is correct for known shapes.
"""
import numpy as np
import pytest
from code.metrics.ellipticity import calculate_ellipticity

def test_ellipticity_calculation():
    """Assert that second-order moments yield correct ellipticity for a known synthetic shape."""
    # Create a synthetic image: a simple elongated Gaussian
    # We want an image with known e1 and e2.
    # Let's create a 2D Gaussian with sigma_x > sigma_y.
    # e1 = (sigma_x^2 - sigma_y^2) / (sigma_x^2 + sigma_y^2)
    # e2 = 0 (if aligned with axes)

    size = 50
    y, x = np.meshgrid(np.linspace(-10, 10, size), np.linspace(-10, 10, size))

    sigma_x = 3.0
    sigma_y = 1.0

    # Gaussian image
    image = np.exp(-(x**2 / (2 * sigma_x**2) + y**2 / (2 * sigma_y**2)))

    e1, e2 = calculate_ellipticity(image)

    # Expected e1
    expected_e1 = (sigma_x**2 - sigma_y**2) / (sigma_x**2 + sigma_y**2)
    expected_e2 = 0.0

    # Tolerance
    tol = 0.05

    assert abs(e1 - expected_e1) < tol, f"e1: {e1} vs expected {expected_e1}"
    assert abs(e2 - expected_e2) < tol, f"e2: {e2} vs expected {expected_e2}"

def test_ellipticity_circle():
    """Assert that a circular image has zero ellipticity."""
    size = 50
    y, x = np.meshgrid(np.linspace(-10, 10, size), np.linspace(-10, 10, size))
    r = np.sqrt(x**2 + y**2)
    image = np.exp(-r**2 / (2 * 2**2))

    e1, e2 = calculate_ellipticity(image)

    tol = 0.01
    assert abs(e1) < tol, f"e1 for circle: {e1}"
    assert abs(e2) < tol, f"e2 for circle: {e2}"
