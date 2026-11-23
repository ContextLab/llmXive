"""
Unit Test: Power-Law Fitting Logic
"""
import numpy as np
from scipy.optimize import curve_fit
from code.fit_scaling_laws import power_law, fit_power_law

def test_power_law_function():
    """Test the power law function definition."""
    x = np.array([1000, 5000, 10000])
    a, b = 1.0, 0.5
    y = power_law(x, a, b)
    expected = a * (x ** -b)
    np.testing.assert_array_almost_equal(y, expected)

def test_fit_power_law_r_squared():
    """Test that fit_power_law returns valid R2 scores."""
    # Generate synthetic data with noise
    x = np.array([1000, 5000, 10000, 20000, 40000])
    true_a, true_b = 2.0, 0.4
    y_true = power_law(x, true_a, true_b)
    y_noisy = y_true + np.random.normal(0, 0.1, size=x.shape)

    popt, r_squared = fit_power_law(x, y_noisy)

    assert r_squared <= 1.0, "R2 cannot exceed 1.0"
    assert r_squared >= -1.0, "R2 should be reasonable"
    assert len(popt) == 2, "Should return 2 parameters (a, b)"
