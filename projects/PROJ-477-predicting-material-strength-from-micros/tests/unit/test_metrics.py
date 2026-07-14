"""
Unit tests for metric calculation (MSE, R²) as per Task T016.
Tests the evaluation logic in code/eval/metrics.py.
"""
import pytest
import numpy as np
import math
import sys
from pathlib import Path

# Add project root to path to allow imports from code/eval
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "code"))

from eval.metrics import calculate_mse, calculate_r2, calculate_t_statistic


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


class TestCalculateTStatistic:
    """Tests for paired t-test statistic on squared errors."""

    def test_identical_errors(self):
        """T-stat should be 0 if error differences are all zero."""
        err_cnn = [1.0, 2.0, 3.0]
        err_baseline = [1.0, 2.0, 3.0]
        t_stat, p_val = calculate_t_statistic(err_cnn, err_baseline)
        assert t_stat == 0.0

    def test_cnn_better(self):
        """T-stat should be negative if CNN errors are consistently lower."""
        # CNN errors: 1, 2, 3; Baseline: 2, 3, 4
        # Diff: -1, -1, -1. Mean diff = -1. Std dev = 0.
        # T-stat = mean_diff / (std/sqrt(n)) -> -inf or very large negative
        err_cnn = [1.0, 2.0, 3.0]
        err_baseline = [2.0, 3.0, 4.0]
        t_stat, p_val = calculate_t_statistic(err_cnn, err_baseline)
        # We expect a large negative t-statistic
        assert t_stat < 0
        assert p_val < 0.05  # Significant

    def test_baseline_better(self):
        """T-stat should be positive if Baseline errors are consistently lower."""
        err_cnn = [2.0, 3.0, 4.0]
        err_baseline = [1.0, 2.0, 3.0]
        t_stat, p_val = calculate_t_statistic(err_cnn, err_baseline)
        assert t_stat > 0

    def test_empty_lists(self):
        """Should raise ValueError for empty inputs."""
        with pytest.raises(ValueError):
            calculate_t_statistic([], [])

    def test_single_pair(self):
        """Should handle single pair (degrees of freedom = 0)."""
        err_cnn = [1.0]
        err_baseline = [2.0]
        # With n=1, std dev is 0/undefined.
        # Implementation should handle this (likely return inf or raise).
        # We just ensure it doesn't crash with a weird type error.
        t_stat, p_val = calculate_t_statistic(err_cnn, err_baseline)
        # Depending on implementation, this might be inf or nan
        assert isinstance(t_stat, float)
        assert isinstance(p_val, float)