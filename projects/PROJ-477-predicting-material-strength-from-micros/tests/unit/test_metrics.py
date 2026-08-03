"""
Unit tests for metric calculation (MSE, R²) as per Task T016.
Tests the evaluation logic in code/eval/metrics.py.

This task implements:
1. test_mse_calculation: Asserts MSE matches numpy implementation.
2. test_ttest_significance: Uses specific input arrays and asserts calculated
   t-statistic and p-value match scipy.stats.ttest_1samp within tolerance.
"""
import pytest
import numpy as np
import math
import sys
from pathlib import Path

# Add project root to path to allow imports from code/eval
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "code"))

from eval.metrics import calculate_mse, calculate_r2, single_sample_ttest_squared_errors


class TestCalculateMSE:
    """Tests for Mean Squared Error calculation."""

    def test_perfect_prediction(self):
        """MSE should be 0 for perfect predictions."""
        y_true = [1.0, 2.0, 3.0, 4.0]
        y_pred = [1.0, 2.0, 3.0, 4.0]
        mse = calculate_mse(y_true, y_pred)
        assert mse == 0.0

    def test_single_error(self):
        """MSE for a single squared error."""
        y_true = [10.0]
        y_pred = [12.0]
        # (10-12)^2 = 4, mean = 4
        mse = calculate_mse(y_true, y_pred)
        assert math.isclose(mse, 4.0, rel_tol=1e-9)

    def test_multiple_errors(self):
        """MSE for multiple predictions."""
        y_true = [1.0, 2.0, 3.0]
        y_pred = [1.1, 2.2, 2.7]
        # Errors: -0.1, -0.2, 0.3
        # Squared: 0.01, 0.04, 0.09
        # Mean: 0.14 / 3 = 0.04666...
        expected = (0.01 + 0.04 + 0.09) / 3
        mse = calculate_mse(y_true, y_pred)
        assert math.isclose(mse, expected, rel_tol=1e-9)

    def test_empty_lists(self):
        """MSE should raise ValueError for empty inputs."""
        with pytest.raises(ValueError):
            calculate_mse([], [])

    def test_mismatched_lengths(self):
        """MSE should raise ValueError for mismatched lengths."""
        with pytest.raises(ValueError):
            calculate_mse([1.0, 2.0], [1.0])

    def test_mse_matches_numpy(self):
        """Assert MSE matches numpy implementation exactly."""
        y_true = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        y_pred = np.array([1.1, 2.2, 2.9, 4.1, 5.0])
        
        # Numpy MSE
        np_mse = np.mean((y_true - y_pred) ** 2)
        
        # Our implementation
        our_mse = calculate_mse(y_true.tolist(), y_pred.tolist())
        
        assert math.isclose(our_mse, float(np_mse), rel_tol=1e-9)


class TestCalculateR2:
    """Tests for R-squared (coefficient of determination) calculation."""

    def test_perfect_prediction(self):
        """R² should be 1.0 for perfect predictions."""
        y_true = [1.0, 2.0, 3.0, 4.0, 5.0]
        y_pred = [1.0, 2.0, 3.0, 4.0, 5.0]
        r2 = calculate_r2(y_true, y_pred)
        assert math.isclose(r2, 1.0, rel_tol=1e-9)

    def test_mean_prediction(self):
        """R² should be 0.0 if predictions are the mean of y_true."""
        y_true = [2.0, 4.0, 6.0]
        y_pred = [4.0, 4.0, 4.0]  # Mean is 4.0
        # SS_res = (2-4)^2 + (4-4)^2 + (6-4)^2 = 4 + 0 + 4 = 8
        # SS_tot = (2-4)^2 + (4-4)^2 + (6-4)^2 = 4 + 0 + 4 = 8
        # R² = 1 - (8/8) = 0
        r2 = calculate_r2(y_true, y_pred)
        assert math.isclose(r2, 0.0, rel_tol=1e-9)

    def test_worse_than_mean(self):
        """R² can be negative if predictions are worse than mean."""
        y_true = [1.0, 2.0, 3.0]
        # Predictions far from true values
        y_pred = [10.0, 10.0, 10.0]
        r2 = calculate_r2(y_true, y_pred)
        assert r2 < 0.0

    def test_single_value(self):
        """R² is undefined for single value (division by zero in SS_tot)."""
        y_true = [1.0]
        y_pred = [1.0]
        # SS_tot = 0, so R2 is undefined (typically NaN or 1.0 depending on implementation)
        # Our implementation should handle this gracefully or raise
        r2 = calculate_r2(y_true, y_pred)
        # If SS_tot is 0, we return 1.0 for perfect match or NaN
        # Check that it returns a valid float
        assert isinstance(r2, float)

    def test_empty_lists(self):
        """R² should raise ValueError for empty inputs."""
        with pytest.raises(ValueError):
            calculate_r2([], [])

    def test_mismatched_lengths(self):
        """R² should raise ValueError for mismatched lengths."""
        with pytest.raises(ValueError):
            calculate_r2([1.0, 2.0], [1.0])


class TestTTestSignificance:
    """Tests for single-sample t-test on squared errors as per T016 spec."""

    def test_ttest_significance(self):
        """
        Test t-statistic and p-value match scipy.stats.ttest_1samp.
        
        Inputs per spec:
        y_true = [1, 2, 3, 4, 5]
        y_pred = [1.1, 2.2, 2.9, 4.1, 5.0]
        
        The test compares CNN squared errors against a scalar baseline error.
        For this unit test, we simulate the scenario where the baseline scalar
        is the mean of the squared errors (or a specific scalar value).
        
        We calculate the squared errors, then perform a single-sample t-test
        against a scalar (e.g., the mean of those errors, which should yield
        t_stat ~ 0.0, p_value ~ 1.0).
        """
        y_true = [1.0, 2.0, 3.0, 4.0, 5.0]
        y_pred = [1.1, 2.2, 2.9, 4.1, 5.0]
        
        # Calculate squared errors
        sq_errors = [(yt - yp) ** 2 for yt, yp in zip(y_true, y_pred)]
        # sq_errors = [0.01, 0.04, 0.01, 0.01, 0.0]
        
        # For a single-sample t-test to yield t_stat ~ 0.0, p_value ~ 1.0,
        # we test against the mean of the sample itself.
        baseline_scalar = np.mean(sq_errors)
        
        # Our implementation
        t_stat, p_val = single_sample_ttest_squared_errors(sq_errors, baseline_scalar)
        
        # Scipy reference
        from scipy import stats
        expected_t, expected_p = stats.ttest_1samp(sq_errors, baseline_scalar)
        
        # Assert within tolerance
        assert math.isclose(t_stat, expected_t, rel_tol=1e-5, abs_tol=1e-5), \
            f"t_stat {t_stat} != expected {expected_t}"
        assert math.isclose(p_val, expected_p, rel_tol=1e-5, abs_tol=1e-5), \
            f"p_val {p_val} != expected {expected_p}"
        
        # Specifically check the expected values mentioned in the task:
        # t_stat ~ 0.0, p_value ~ 1.0
        assert math.isclose(t_stat, 0.0, abs_tol=1e-5), f"t_stat should be ~0.0, got {t_stat}"
        assert math.isclose(p_val, 1.0, abs_tol=1e-5), f"p_val should be ~1.0, got {p_val}"

    def test_cnn_better_than_baseline(self):
        """
        Test case where CNN errors are consistently lower than baseline scalar.
        Expect negative t-statistic and significant p-value.
        """
        cnn_sq_errors = [0.1, 0.2, 0.1, 0.15, 0.05]
        baseline_scalar = 0.5  # Higher than any CNN error
        
        t_stat, p_val = single_sample_ttest_squared_errors(cnn_sq_errors, baseline_scalar)
        
        # Expect negative t-stat (mean of errors < baseline)
        assert t_stat < 0, f"t_stat should be negative, got {t_stat}"
        assert p_val < 0.05, f"p_val should be significant (< 0.05), got {p_val}"

    def test_cnn_worse_than_baseline(self):
        """
        Test case where CNN errors are consistently higher than baseline scalar.
        Expect positive t-statistic and significant p-value.
        """
        cnn_sq_errors = [1.0, 1.5, 1.2, 1.3, 1.1]
        baseline_scalar = 0.5  # Lower than any CNN error
        
        t_stat, p_val = single_sample_ttest_squared_errors(cnn_sq_errors, baseline_scalar)
        
        # Expect positive t-stat (mean of errors > baseline)
        assert t_stat > 0, f"t_stat should be positive, got {t_stat}"
        assert p_val < 0.05, f"p_val should be significant (< 0.05), got {p_val}"

    def test_empty_errors(self):
        """Should raise ValueError for empty errors list."""
        with pytest.raises(ValueError):
            single_sample_ttest_squared_errors([], 0.5)

    def test_single_error(self):
        """
        Test with single error value.
        Degrees of freedom = 0, so t-stat is undefined (inf or nan).
        Implementation should handle this gracefully.
        """
        cnn_sq_errors = [0.5]
        baseline_scalar = 0.5
        
        t_stat, p_val = single_sample_ttest_squared_errors(cnn_sq_errors, baseline_scalar)
        
        # With n=1, std dev is 0, t-stat is undefined.
        # We expect inf or nan, but not a crash.
        assert isinstance(t_stat, float)
        assert isinstance(p_val, float)