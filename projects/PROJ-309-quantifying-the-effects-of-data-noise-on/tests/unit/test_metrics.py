"""
Unit tests for the Grassberger-Procaccia algorithm (Correlation Dimension).

This test verifies the correctness of the implementation using a known synthetic
dataset where the theoretical correlation dimension is established.
"""
import numpy as np
import pytest
from scipy.spatial.distance import cdist

# Import the function under test from the project's metrics module
import sys
import os
# Ensure the code directory is in the path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'code'))

from metrics import compute_correlation_dimension


def test_correlation_dimension_mandelbrot():
    """
    Test Grassberger-Procaccia algorithm on a synthetic dataset approximating
    a known fractal structure.
    
    We generate a 2D dataset with a known scaling region. While a perfect
    mathematical fractal is infinite, we use a large enough sample of a
    deterministic chaotic attractor (Lorenz) or a constructed fractal set
    to verify the slope calculation logic.
    
    For this unit test, we use a synthetic dataset constructed to have
    a known correlation dimension close to 2.0 (a filled 2D plane) or
    verify the algorithm's behavior on a known fractal approximation.
    
    Here, we generate a large set of points from a 2D Gaussian distribution.
    The correlation dimension of a 2D Gaussian cloud is theoretically 2.0
    (the embedding dimension) within the scaling region, provided the
    sample size is sufficient and noise is low.
    """
    # Set random seed for reproducibility
    np.random.seed(42)
    
    # Generate 2000 points from a standard 2D normal distribution
    # This approximates a 2D manifold with D2 = 2.0 in the scaling region
    n_points = 2000
    dim = 2
    data = np.random.randn(n_points, dim)
    
    # Parameters for the GP algorithm
    r_min = 0.01
    r_max = 2.0
    n_bins = 20
    
    # Compute the correlation dimension
    # We expect the result to be close to 2.0 (the embedding dimension)
    # with some tolerance due to finite sample size and binning
    d2, r_values, c_values = compute_correlation_dimension(
        data, 
        r_min=r_min, 
        r_max=r_max, 
        n_bins=n_bins
    )
    
    # The correlation dimension of a 2D Gaussian is 2.0
    # We allow a tolerance of 0.5 due to finite sample effects and the
    # specific range of r values chosen.
    assert d2 is not None, "Correlation dimension calculation returned None"
    assert isinstance(d2, float), "Correlation dimension should be a float"
    
    # Check that the value is within a reasonable range for a 2D distribution
    # It should be positive and less than or equal to the embedding dimension
    assert 1.0 < d2 < 2.5, f"Expected D2 near 2.0 for 2D Gaussian, got {d2}"
    
    # Verify that the return values for r and C are arrays of expected length
    assert len(r_values) == n_bins, f"Expected {n_bins} r values, got {len(r_values)}"
    assert len(c_values) == n_bins, f"Expected {n_bins} C values, got {len(c_values)}"
    
    # Verify that C(r) is monotonically increasing (property of correlation integral)
    # This is a sanity check for the implementation logic
    for i in range(1, len(c_values)):
        assert c_values[i] >= c_values[i-1], "Correlation integral should be monotonically increasing"


def test_correlation_dimension_empty_input():
    """Test behavior with insufficient data points."""
    data = np.random.randn(5, 2) # Too few points for reliable GP
    
    with pytest.raises(ValueError):
        compute_correlation_dimension(data, r_min=0.01, r_max=1.0, n_bins=10)


def test_correlation_dimension_1d():
    """Test on a 1D dataset (line). D2 should be close to 1.0."""
    np.random.seed(123)
    n_points = 1000
    data = np.random.randn(n_points, 1)
    
    d2, r_values, c_values = compute_correlation_dimension(
        data, 
        r_min=0.01, 
        r_max=2.0, 
        n_bins=15
    )
    
    assert d2 is not None
    # For a 1D line, D2 should be close to 1.0
    assert 0.5 < d2 < 1.5, f"Expected D2 near 1.0 for 1D Gaussian, got {d2}"


def test_correlation_dimension_deterministic_fractal():
    """
    Test on a synthetic dataset designed to mimic a fractal with D < 2.
    We generate points on a Sierpinski triangle approximation.
    """
    np.random.seed(999)
    n_points = 3000
    
    # Generate Sierpinski Triangle points using Chaos Game
    vertices = np.array([[0, 0], [1, 0], [0.5, np.sqrt(3)/2]])
    points = np.zeros((n_points, 2))
    current = np.array([0.0, 0.0])
    
    for i in range(n_points):
        # Pick a random vertex
        v = vertices[np.random.randint(0, 3)]
        # Move halfway to the vertex
        current = (current + v) / 2
        points[i] = current
    
    # The theoretical correlation dimension of Sierpinski Triangle is log(3)/log(2) ≈ 1.585
    d2, r_values, c_values = compute_correlation_dimension(
        points,
        r_min=0.001,
        r_max=0.5,
        n_bins=25
    )
    
    assert d2 is not None
    theoretical_d2 = np.log(3) / np.log(2)
    # Allow a tolerance of 0.2 due to finite sample and binning
    assert abs(d2 - theoretical_d2) < 0.2, f"Expected D2 near {theoretical_d2}, got {d2}"
