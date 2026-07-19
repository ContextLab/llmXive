"""
Unit tests for power-law fitting logic in scaling analysis.

Tests cover:
1. Basic power-law fitting (R2 >= 0.9)
2. R2 < 0.9 handling (non-power-law classification)
3. Multi-seed averaging of exponents
4. Edge cases: insufficient data points, single point, negative values
"""

import pytest
import numpy as np
from numpy.testing import assert_allclose
import pandas as pd

# Import the fitting logic directly or via a module if it exists.
# Since the implementation file (fit_scaling_laws.py) is not yet written,
# we define the core logic here for testing purposes.
# In the final implementation, this logic should be moved to code/fit_scaling_laws.py
# and imported from there.

def fit_power_law(x: np.ndarray, y: np.ndarray) -> tuple[float, float, float]:
    """
    Fit a power law model: y = a * x^b  =>  log(y) = log(a) + b * log(x)

    Parameters:
        x: Independent variable (dataset sizes)
        y: Dependent variable (errors)

    Returns:
        tuple: (exponent_b, intercept_a, r_squared)
               If fit fails or data is invalid, returns (np.nan, np.nan, np.nan)
    """
    if len(x) < 2 or len(y) < 2:
        return np.nan, np.nan, np.nan

    if np.any(x <= 0) or np.any(y <= 0):
        return np.nan, np.nan, np.nan

    try:
        log_x = np.log(x)
        log_y = np.log(y)

        # Linear regression: log_y = intercept + slope * log_x
        n = len(log_x)
        sum_x = np.sum(log_x)
        sum_y = np.sum(log_y)
        sum_xy = np.sum(log_x * log_y)
        sum_x2 = np.sum(log_x ** 2)

        denominator = n * sum_x2 - sum_x ** 2
        if abs(denominator) < 1e-10:
            return np.nan, np.nan, np.nan

        slope = (n * sum_xy - sum_x * sum_y) / denominator
        intercept = (sum_y - slope * sum_x) / n

        # Calculate R-squared
        y_pred = intercept + slope * log_x
        ss_res = np.sum((log_y - y_pred) ** 2)
        ss_tot = np.sum((log_y - np.mean(log_y)) ** 2)

        if ss_tot < 1e-10:
            r_squared = np.nan
        else:
            r_squared = 1 - (ss_res / ss_tot)

        # Convert back to original scale
        exponent_b = slope
        intercept_a = np.exp(intercept)

        return exponent_b, intercept_a, r_squared

    except (ValueError, RuntimeWarning):
        return np.nan, np.nan, np.nan


def classify_fit(r_squared: float, threshold: float = 0.9) -> str:
    """
    Classify the fit quality based on R-squared value.

    Parameters:
        r_squared: R-squared value from the fit
        threshold: Threshold for classification (default 0.9)

    Returns:
        str: 'power-law' if R2 >= threshold, else 'non-power-law'
    """
    if np.isnan(r_squared):
        return 'non-power-law'
    return 'power-law' if r_squared >= threshold else 'non-power-law'


def average_exponents(exponents: list[float]) -> float:
    """
    Average a list of exponents, ignoring NaN values.

    Parameters:
        exponents: List of exponent values

    Returns:
        float: Mean of valid exponents, or np.nan if all are NaN
    """
    valid_exponents = [e for e in exponents if not np.isnan(e)]
    if not valid_exponents:
        return np.nan
    return np.mean(valid_exponents)


class TestPowerLawFitting:
    """Test suite for power-law fitting logic."""

    def test_basic_power_law_fit(self):
        """Test fitting on perfect power-law data."""
        # y = 10 * x^(-0.5)
        x = np.array([1000, 5000, 10000, 20000, 40000], dtype=float)
        a_true = 10.0
        b_true = -0.5
        y = a_true * np.power(x, b_true)

        b, a, r2 = fit_power_law(x, y)

        assert_allclose(b, b_true, rtol=1e-5)
        assert_allclose(a, a_true, rtol=1e-5)
        assert r2 >= 0.99

    def test_noisy_power_law_fit(self):
        """Test fitting on noisy power-law data."""
        x = np.array([1000, 5000, 10000, 20000, 40000], dtype=float)
        a_true = 10.0
        b_true = -0.5
        y = a_true * np.power(x, b_true) * np.random.normal(1.0, 0.1, size=x.shape)

        b, a, r2 = fit_power_law(x, y)

        assert not np.isnan(b)
        assert not np.isnan(a)
        assert not np.isnan(r2)
        assert abs(b - b_true) < 0.1  # Tolerance for noise

    def test_non_power_law_data(self):
        """Test classification of non-power-law data (R2 < 0.9)."""
        # Exponential decay instead of power law
        x = np.array([1000, 5000, 10000, 20000, 40000], dtype=float)
        y = np.exp(-x / 10000) + 0.1

        b, a, r2 = fit_power_law(x, y)

        assert not np.isnan(r2)
        assert r2 < 0.9
        assert classify_fit(r2) == 'non-power-law'

    def test_classification_threshold_boundary(self):
        """Test classification at the R2 threshold boundary."""
        assert classify_fit(0.9) == 'power-law'
        assert classify_fit(0.8999) == 'non-power-law'
        assert classify_fit(1.0) == 'power-law'
        assert classify_fit(0.0) == 'non-power-law'

    def test_insufficient_data_points(self):
        """Test fitting with fewer than 2 points."""
        x = np.array([1000.0])
        y = np.array([0.5])

        b, a, r2 = fit_power_law(x, y)

        assert np.isnan(b)
        assert np.isnan(a)
        assert np.isnan(r2)

    def test_single_point_classification(self):
        """Test classification when fit fails due to single point."""
        r2 = np.nan
        assert classify_fit(r2) == 'non-power-law'

    def test_negative_values_handling(self):
        """Test fitting with negative values (should fail)."""
        x = np.array([1000, 5000, 10000, 20000, 40000], dtype=float)
        y = np.array([-0.5, -0.4, -0.3, -0.2, -0.1])

        b, a, r2 = fit_power_law(x, y)

        assert np.isnan(b)
        assert np.isnan(a)
        assert np.isnan(r2)

    def test_zero_values_handling(self):
        """Test fitting with zero values (should fail)."""
        x = np.array([1000, 5000, 10000, 20000, 40000], dtype=float)
        y = np.array([0.5, 0.4, 0.3, 0.2, 0.0])

        b, a, r2 = fit_power_law(x, y)

        assert np.isnan(b)
        assert np.isnan(a)
        assert np.isnan(r2)

    def test_multi_seed_averaging(self):
        """Test averaging exponents from multiple seeds."""
        exponents = [-0.48, -0.52, -0.50, np.nan, -0.51]
        avg = average_exponents(exponents)

        expected = (-0.48 - 0.52 - 0.50 - 0.51) / 4
        assert_allclose(avg, expected)

    def test_all_nan_averaging(self):
        """Test averaging when all exponents are NaN."""
        exponents = [np.nan, np.nan, np.nan]
        avg = average_exponents(exponents)

        assert np.isnan(avg)

    def test_empty_list_averaging(self):
        """Test averaging an empty list."""
        avg = average_exponents([])

        assert np.isnan(avg)

    def test_mixed_fit_qualities(self):
        """Test processing a mix of good and bad fits."""
        fits = [
            {'exponent': -0.5, 'r_squared': 0.95, 'status': 'power-law'},
            {'exponent': -0.4, 'r_squared': 0.85, 'status': 'non-power-law'},
            {'exponent': -0.55, 'r_squared': 0.92, 'status': 'power-law'},
        ]

        power_law_exponents = [f['exponent'] for f in fits if f['status'] == 'power-law']
        avg_exponent = average_exponents(power_law_exponents)

        assert_allclose(avg_exponent, (-0.5 - 0.55) / 2)

    def test_realistic_learning_curve_data(self):
        """Test with realistic learning curve data points."""
        # Simulated learning curve: error decreases as dataset size increases
        x = np.array([1000, 5000, 10000, 20000, 40000], dtype=float)
        y = np.array([0.85, 0.65, 0.55, 0.45, 0.38])

        b, a, r2 = fit_power_law(x, y)

        assert not np.isnan(b)
        assert b < 0  # Error should decrease with more data
        assert not np.isnan(r2)
        assert classify_fit(r2) in ['power-law', 'non-power-law']