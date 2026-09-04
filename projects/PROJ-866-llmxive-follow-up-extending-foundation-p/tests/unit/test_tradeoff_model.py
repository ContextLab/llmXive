import pytest
import numpy as np
from analysis.tradeoff_model import logistic_function, fit_tradeoff_curve

def test_logistic_function():
    """
    T027: Unit test for regression calculation with known synthetic data.
    Verifies the logistic function behaves as expected.
    """
    # Test with known parameters
    x = np.array([0, 1, 2, 3, 4, 5])
    params = np.array([1.0, -0.5, 2.0])  # amplitude, slope, offset
    
    result = logistic_function(x, params)
    
    # Check that result is within expected bounds
    assert np.all(result >= 0), "Logistic function output should be non-negative"
    assert np.all(result <= params[0]), "Logistic function output should not exceed amplitude"

def test_fit_tradeoff_curve():
    """
    Test that the curve fitting function runs without error on synthetic data.
    """
    # Generate synthetic data with known pattern
    np.random.seed(42)
    x = np.linspace(0, 10, 50)
    y = 1 / (1 + np.exp(-(x - 5))) + np.random.normal(0, 0.1, 50)
    
    initial_params = [1.0, -0.5, 2.0]
    
    # This should not raise an exception
    try:
        fitted_params, _ = fit_tradeoff_curve(x, y, initial_params)
        assert len(fitted_params) == 3, "Fitted parameters should have 3 elements"
    except Exception as e:
        pytest.fail(f"fit_tradeoff_curve failed with: {e}")
