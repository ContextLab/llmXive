"""
Unit tests for custom metric calculations in utils/metrics.py.
"""
import pytest
import numpy as np
from utils.metrics import (
    calculate_mae,
    calculate_rmse,
    calculate_r2,
    bootstrap_confidence_interval,
    spearman_correlation,
    calculate_variance,
    calculate_std_dev
)

class TestMetrics:
    """Test suite for metric functions."""

    def test_calculate_mae(self):
        """Test Mean Absolute Error calculation."""
        y_true = np.array([3.0, -0.5, 2.0, 7.0])
        y_pred = np.array([2.5, 0.0, 2.0, 8.0])
        result = calculate_mae(y_true, y_pred)
        expected = 0.5
        assert np.isclose(result, expected), f"Expected {expected}, got {result}"

    def test_calculate_rmse(self):
        """Test Root Mean Squared Error calculation."""
        y_true = np.array([3.0, -0.5, 2.0, 7.0])
        y_pred = np.array([2.5, 0.0, 2.0, 8.0])
        result = calculate_rmse(y_true, y_pred)
        # Manual calculation: sqrt(mean((0.5^2 + 0.5^2 + 0 + 1^2)/4)) = sqrt(1.5/4) = sqrt(0.375)
        expected = np.sqrt(0.375)
        assert np.isclose(result, expected), f"Expected {expected}, got {result}"

    def test_calculate_r2(self):
        """Test R-squared calculation."""
        y_true = np.array([3.0, -0.5, 2.0, 7.0])
        y_pred = np.array([2.5, 0.0, 2.0, 8.0])
        result = calculate_r2(y_true, y_pred)
        # Using sklearn r2_score for verification
        from sklearn.metrics import r2_score
        expected = r2_score(y_true, y_pred)
        assert np.isclose(result, expected), f"Expected {expected}, got {result}"

    def test_bootstrap_confidence_interval(self):
        """Test bootstrap confidence interval generation."""
        data = np.array([10.0, 12.0, 11.0, 13.0, 10.5, 11.5, 12.5, 11.0])
        ci = bootstrap_confidence_interval(data, statistic=np.mean, n_bootstraps=1000, confidence_level=0.95)
        assert isinstance(ci, tuple), "CI should be a tuple (lower, upper)"
        assert len(ci) == 2, "CI should have 2 elements"
        assert ci[0] <= ci[1], "Lower bound should be <= upper bound"
        assert np.mean(data) >= ci[0] and np.mean(data) <= ci[1], "Mean should be within CI"

    def test_spearman_correlation(self):
        """Test Spearman rank correlation calculation."""
        x = np.array([1, 2, 3, 4, 5])
        y = np.array([2, 4, 6, 8, 10]) # Perfect positive correlation
        result = spearman_correlation(x, y)
        assert np.isclose(result, 1.0), f"Expected 1.0, got {result}"

    def test_calculate_variance(self):
        """Test variance calculation."""
        data = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        result = calculate_variance(data)
        expected = np.var(data, ddof=1) # Sample variance
        assert np.isclose(result, expected), f"Expected {expected}, got {result}"

    def test_calculate_std_dev(self):
        """Test standard deviation calculation."""
        data = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        result = calculate_std_dev(data)
        expected = np.std(data, ddof=1) # Sample std dev
        assert np.isclose(result, expected), f"Expected {expected}, got {result}"
