import pytest
import numpy as np
from src.analysis.stats import linear_regression_slope

def test_linear_regression_slope_basic():
    """
    Test basic linear regression slope calculation.
    Given y = 2x + 1, the slope should be approximately 2.0.
    """
    x = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
    y = np.array([3.0, 5.0, 7.0, 9.0, 11.0])  # y = 2x + 1

    slope = linear_regression_slope(x, y)
    assert np.isclose(slope, 2.0, atol=1e-6), f"Expected slope 2.0, got {slope}"

def test_linear_regression_slope_negative():
    """
    Test negative slope calculation.
    Given y = -3x + 10, the slope should be approximately -3.0.
    """
    x = np.array([1.0, 2.0, 3.0, 4.0])
    y = np.array([7.0, 4.0, 1.0, -2.0])  # y = -3x + 10

    slope = linear_regression_slope(x, y)
    assert np.isclose(slope, -3.0, atol=1e-6), f"Expected slope -3.0, got {slope}"

def test_linear_regression_slope_with_noise():
    """
    Test slope calculation with slight noise (should still be close to expected).
    """
    x = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
    y = np.array([3.1, 4.9, 7.2, 8.8, 11.1])  # Noisy y = 2x + 1

    slope = linear_regression_slope(x, y)
    # Allow for some tolerance due to noise
    assert 1.8 < slope < 2.2, f"Expected slope near 2.0, got {slope}"

def test_linear_regression_slope_horizontal():
    """
    Test slope calculation for a horizontal line (slope = 0).
    """
    x = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
    y = np.array([5.0, 5.0, 5.0, 5.0, 5.0])  # y = 5 (constant)

    slope = linear_regression_slope(x, y)
    assert np.isclose(slope, 0.0, atol=1e-6), f"Expected slope 0.0, got {slope}"

def test_linear_regression_slope_vertical_error():
    """
    Test that vertical line (all x same) raises an error or returns NaN.
    The implementation should handle division by zero (variance of x is 0).
    """
    x = np.array([2.0, 2.0, 2.0, 2.0])
    y = np.array([1.0, 2.0, 3.0, 4.0])

    slope = linear_regression_slope(x, y)
    # Expected behavior: NaN or raise an error. We check for NaN.
    assert np.isnan(slope), f"Expected NaN for vertical line, got {slope}"

def test_slope_comparison_kvarn_vs_uniform_synthetic():
    """
    Unit test for slope comparison regression logic.
    Simulates cumulative MSE data for KVarN and Uniform quantizers.
    
    Hypothesis: KVarN should have a lower slope (slower error accumulation) 
    than Uniform quantization.
    
    We generate synthetic data where:
    - Uniform: steep slope (fast error accumulation)
    - KVarN: shallow slope (slow error accumulation)
    
    The test verifies that the calculated slopes reflect this expectation.
    """
    # Synthetic token positions (1 to 100)
    token_positions = np.arange(1, 101, dtype=float)

    # Synthetic cumulative MSE for Uniform (steeper slope ~0.05)
    # y = 0.05 * x + noise
    uniform_mse = 0.05 * token_positions + np.random.normal(0, 0.1, size=token_positions.shape)

    # Synthetic cumulative MSE for KVarN (shallower slope ~0.02)
    # y = 0.02 * x + noise
    kvarn_mse = 0.02 * token_positions + np.random.normal(0, 0.1, size=token_positions.shape)

    uniform_slope = linear_regression_slope(token_positions, uniform_mse)
    kvarn_slope = linear_regression_slope(token_positions, kvarn_mse)

    # Verify slopes are positive (error accumulates)
    assert uniform_slope > 0, "Uniform slope should be positive"
    assert kvarn_slope > 0, "KVarN slope should be positive"

    # Verify KVarN slope is significantly lower than Uniform slope
    # (This is the core hypothesis: variance normalization reduces error accumulation rate)
    assert kvarn_slope < uniform_slope, \
        f"Expected KVarN slope ({kvarn_slope:.4f}) < Uniform slope ({uniform_slope:.4f})"

    # Assert the difference is meaningful (at least 30% reduction)
    reduction_ratio = (uniform_slope - kvarn_slope) / uniform_slope
    assert reduction_ratio > 0.3, \
        f"Expected >30% reduction in slope, got {reduction_ratio:.2%}"