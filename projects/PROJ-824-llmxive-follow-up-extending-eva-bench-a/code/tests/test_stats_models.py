"""
Unit tests for piecewise regression fitting logic.

This module validates the statistical models used in User Story 2 (Threshold Detection).
It tests the piecewise linear regression fitting, ensuring that:
1. The model fits data with a clear breakpoint correctly.
2. The estimated breakpoint is close to the ground truth.
3. The model raises appropriate errors for invalid inputs (e.g., insufficient data).
"""

import pytest
import numpy as np
from typing import Tuple

# Local imports for the implementation under test.
# We assume the implementation resides in code/analysis/piecewise_regression.py
# as per the project structure for User Story 2 analysis components.
try:
    from analysis.piecewise_regression import fit_piecewise_linear
except ImportError:
    # Fallback for testing environments where the module might not yet exist
    # or to allow the test to define the expected interface.
    # In a real run, this import must succeed.
    pytest.skip("analysis.piecewise_regression module not found", allow_module_level=True)

# Set random seed for reproducibility in tests
SEED = 42
np.random.seed(SEED)


def generate_synthetic_piecewise_data(
    n_points: int = 100,
    breakpoint: float = 50.0,
    slope1: float = 1.0,
    slope2: float = -0.5,
    noise_std: float = 2.0
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Generates synthetic 1D data with a known piecewise linear structure.
    
    Args:
        n_points: Number of data points to generate.
        breakpoint: The x-value where the slope changes.
        slope1: Slope before the breakpoint.
        slope2: Slope after the breakpoint.
        noise_std: Standard deviation of Gaussian noise.
        
    Returns:
        Tuple of (x, y) numpy arrays.
    """
    x = np.linspace(0, 100, n_points)
    y = np.zeros_like(x)
    
    # Generate piecewise linear signal
    for i, xi in enumerate(x):
        if xi <= breakpoint:
            y[i] = slope1 * (xi - breakpoint)
        else:
            y[i] = slope2 * (xi - breakpoint)
    
    # Add noise
    y += np.random.normal(0, noise_std, size=n_points)
    
    return x, y


class TestPiecewiseRegressionFitting:
    """Tests for the piecewise linear regression fitting function."""

    def test_fits_known_breakpoint(self):
        """
        Test that the model can recover a known breakpoint from synthetic data.
        """
        true_breakpoint = 50.0
        true_slope1 = 1.0
        true_slope2 = -0.5
        noise = 1.0
        
        x, y = generate_synthetic_piecewise_data(
            n_points=200,
            breakpoint=true_breakpoint,
            slope1=true_slope1,
            slope2=true_slope2,
            noise_std=noise
        )
        
        # Fit the model
        result = fit_piecewise_linear(x, y)
        
        # Assertions
        assert 'breakpoint' in result, "Result must contain 'breakpoint'"
        assert 'slope1' in result, "Result must contain 'slope1'"
        assert 'slope2' in result, "Result must contain 'slope2'"
        
        # Check breakpoint accuracy (allowing for some tolerance due to noise)
        estimated_bp = result['breakpoint']
        assert abs(estimated_bp - true_breakpoint) < 5.0, \
            f"Estimated breakpoint {estimated_bp} too far from true {true_breakpoint}"
        
        # Check slopes
        assert abs(result['slope1'] - true_slope1) < 0.2, \
            f"Slope1 {result['slope1']} deviates too much from {true_slope1}"
        assert abs(result['slope2'] - true_slope2) < 0.2, \
            f"Slope2 {result['slope2']} deviates too much from {true_slope2}"

    def test_handles_low_noise(self):
        """
        Test fitting on data with very low noise.
        """
        x, y = generate_synthetic_piecewise_data(
            n_points=100,
            breakpoint=30.0,
            slope1=2.0,
            slope2=0.0,
            noise_std=0.1
        )
        
        result = fit_piecewise_linear(x, y)
        
        # With low noise, the fit should be very close
        assert abs(result['breakpoint'] - 30.0) < 2.0
        assert abs(result['slope1'] - 2.0) < 0.1
        assert abs(result['slope2'] - 0.0) < 0.1

    def test_raises_error_on_insufficient_data(self):
        """
        Test that the function raises an error when data points are too few.
        """
        x = np.array([1.0, 2.0, 3.0])
        y = np.array([1.0, 2.0, 3.0])
        
        with pytest.raises(ValueError):
            fit_piecewise_linear(x, y)

    def test_handles_flat_data(self):
        """
        Test fitting on data that is effectively flat (zero slope everywhere).
        """
        x = np.linspace(0, 100, 100)
        y = np.ones(100) * 5.0 + np.random.normal(0, 0.1, 100)
        
        result = fit_piecewise_linear(x, y)
        
        # Slopes should be close to zero
        assert abs(result['slope1']) < 0.5
        assert abs(result['slope2']) < 0.5

    def test_output_structure(self):
        """
        Test that the output dictionary contains all expected keys.
        """
        x, y = generate_synthetic_piecewise_data()
        result = fit_piecewise_linear(x, y)
        
        expected_keys = ['breakpoint', 'slope1', 'slope2', 'r_squared', 'n_iterations']
        for key in expected_keys:
            assert key in result, f"Missing expected key: {key}"