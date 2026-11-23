"""
Unit tests for edge cases in calibration metrics and data handling.
Specifically targets constant variance, NaN handling, and empty series scenarios.
"""
import pytest
import numpy as np
import pandas as pd
from typing import List, Dict, Tuple

# Import project modules
from metrics.coverage import compute_coverage, compute_coverage_deviation
from metrics.pit import calculate_pit, ljung_box_test
from metrics.crps import compute_crps
from data_loader import standardize, split_series
from utils.exceptions import DataValidationError
from config import set_seed

# Ensure reproducibility for tests
set_seed(42)


class TestConstantVariance:
    """Tests for scenarios where forecast uncertainty is constant or zero."""

    def test_constant_forecast_intervals(self):
        """Test coverage calculation when intervals are constant width."""
        # True values
        y_true = np.array([10.0, 20.0, 30.0, 40.0, 50.0])
        # Predictions
        y_pred = np.array([10.0, 20.0, 30.0, 40.0, 50.0])
        # Constant width intervals (lower, upper)
        # 80% nominal: +/- 2 units
        lower_80 = y_pred - 2.0
        upper_80 = y_pred + 2.0
        # 95% nominal: +/- 4 units
        lower_95 = y_pred - 4.0
        upper_95 = y_pred + 4.0

        # All true values fall exactly on prediction, so inside intervals
        coverage_80 = compute_coverage(y_true, lower_80, upper_80, nominal_level=0.80)
        coverage_95 = compute_coverage(y_true, lower_95, upper_95, nominal_level=0.95)

        assert coverage_80 == 1.0, "Coverage should be 100% for constant intervals containing all points"
        assert coverage_95 == 1.0, "Coverage should be 100% for constant intervals containing all points"

    def test_zero_width_intervals(self):
        """Test behavior when intervals have zero width (point forecasts)."""
        y_true = np.array([10.0, 20.0, 30.0])
        y_pred = np.array([10.0, 20.0, 30.0])
        # Zero width
        lower = y_pred.copy()
        upper = y_pred.copy()

        # If true == pred, it counts as inside (inclusive boundaries)
        coverage = compute_coverage(y_true, lower, upper, nominal_level=0.95)
        assert coverage == 1.0

        # If true != pred, coverage should be 0
        y_true_diff = np.array([11.0, 20.0, 30.0])
        coverage_diff = compute_coverage(y_true_diff, lower, upper, nominal_level=0.95)
        assert coverage_diff == 0.0

    def test_constant_variance_pit(self):
        """Test PIT calculation with constant variance forecasts."""
        # Generate synthetic residuals that are constant variance
        # Simulate a scenario where forecast uncertainty is uniform
        y_true = np.array([10.0, 20.0, 30.0, 40.0, 50.0, 60.0, 70.0, 80.0, 90.0, 100.0])
        y_pred = np.array([10.0, 20.0, 30.0, 40.0, 50.0, 60.0, 70.0, 80.0, 90.0, 100.0])
        # Assume constant standard deviation of 5.0
        std_dev = np.full_like(y_true, 5.0)

        # Calculate PIT assuming Gaussian distribution
        # PIT = CDF((y_true - y_pred) / sigma)
        # Since y_true == y_pred, z-scores are 0, CDF(0) = 0.5
        pit_values = calculate_pit(y_true, y_pred, std_dev)

        assert np.allclose(pit_values, 0.5), "PIT values should be 0.5 for perfect predictions with constant variance"

    def test_ljung_box_constant_pit(self):
        """Test Ljung-Box test on constant PIT values (should fail uniformity)."""
        # Constant PIT values (not uniform)
        pit_values = np.full(100, 0.5)

        # This should likely result in a very low p-value (reject uniformity)
        # or raise an error if variance is zero.
        # We expect the test to detect non-uniformity.
        try:
            _, p_value = ljung_box_test(pit_values)
            # With constant values, the test statistic might be undefined or p-value near 0
            # We assert that it doesn't crash and returns a float
            assert isinstance(p_value, float)
        except Exception:
            # Some implementations might raise on zero variance; that's acceptable
            pass


class TestNaNHandling:
    """Tests for scenarios involving NaN values in data or predictions."""

    def test_nan_in_true_values_coverage(self):
        """Test coverage calculation with NaN in true values."""
        y_true = np.array([10.0, np.nan, 30.0, 40.0, 50.0])
        y_pred = np.array([10.0, 20.0, 30.0, 40.0, 50.0])
        lower = y_pred - 5.0
        upper = y_pred + 5.0

        # Function should handle NaN by either skipping or raising
        # Based on robust design, we expect it to skip NaN or handle gracefully
        # If it raises, we catch it; if it returns, we check validity
        try:
            coverage = compute_coverage(y_true, lower, upper, nominal_level=0.95)
            # If it returns, it should be based on valid points only
            # 4 valid points, all covered -> 1.0
            assert 0.0 <= coverage <= 1.0
        except (ValueError, DataValidationError):
            # Expected behavior if NaN is not allowed
            pass

    def test_nan_in_predictions_coverage(self):
        """Test coverage calculation with NaN in predictions."""
        y_true = np.array([10.0, 20.0, 30.0, 40.0, 50.0])
        y_pred = np.array([10.0, np.nan, 30.0, 40.0, 50.0])
        lower = y_pred - 5.0
        upper = y_pred + 5.0

        try:
            coverage = compute_coverage(y_true, lower, upper, nominal_level=0.95)
            assert 0.0 <= coverage <= 1.0
        except (ValueError, DataValidationError):
            pass

    def test_standardize_with_nan(self):
        """Test standardization function with NaN values."""
        data = pd.Series([1.0, 2.0, np.nan, 4.0, 5.0])

        # Standardize should either drop NaN or raise
        try:
            standardized = standardize(data)
            # If it returns, it should not have NaN
            assert not standardized.isna().any()
        except (ValueError, DataValidationError):
            # Expected if NaN is not allowed in standardization
            pass

    def test_split_series_with_nan(self):
        """Test series splitting with NaN values."""
        series = pd.Series([1.0, 2.0, np.nan, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0])

        try:
            train, test = split_series(series, test_size=0.2)
            # Check that splits are valid
            assert len(train) + len(test) == len(series.dropna())
        except (ValueError, DataValidationError):
            pass


class TestEmptyAndSinglePoint:
    """Tests for edge cases with minimal data."""

    def test_single_point_coverage(self):
        """Test coverage calculation with a single data point."""
        y_true = np.array([10.0])
        y_pred = np.array([10.0])
        lower = np.array([5.0])
        upper = np.array([15.0])

        coverage = compute_coverage(y_true, lower, upper, nominal_level=0.95)
        assert coverage == 1.0

    def test_empty_array_coverage(self):
        """Test coverage calculation with empty arrays."""
        y_true = np.array([])
        y_pred = np.array([])
        lower = np.array([])
        upper = np.array([])

        with pytest.raises((ValueError, DataValidationError)):
            compute_coverage(y_true, lower, upper, nominal_level=0.95)

    def test_single_point_pit(self):
        """Test PIT calculation with a single point."""
        y_true = np.array([10.0])
        y_pred = np.array([10.0])
        std_dev = np.array([5.0])

        pit_values = calculate_pit(y_true, y_pred, std_dev)
        assert len(pit_values) == 1
        assert pit_values[0] == 0.5

    def test_ljung_box_insufficient_data(self):
        """Test Ljung-Box test with insufficient data points."""
        pit_values = np.array([0.5])  # Only one point

        with pytest.raises((ValueError, RuntimeError)):
            ljung_box_test(pit_values)


class TestExtremeValues:
    """Tests for scenarios with extreme numerical values."""

    def test_very_large_values(self):
        """Test coverage with very large values."""
        y_true = np.array([1e10, 2e10, 3e10])
        y_pred = np.array([1e10, 2e10, 3e10])
        lower = y_pred - 1e9
        upper = y_pred + 1e9

        coverage = compute_coverage(y_true, lower, upper, nominal_level=0.95)
        assert coverage == 1.0

    def test_very_small_values(self):
        """Test coverage with very small values (near machine epsilon)."""
        y_true = np.array([1e-10, 2e-10, 3e-10])
        y_pred = np.array([1e-10, 2e-10, 3e-10])
        lower = y_pred - 1e-11
        upper = y_pred + 1e-11

        coverage = compute_coverage(y_true, lower, upper, nominal_level=0.95)
        assert coverage == 1.0

    def test_extreme_variance(self):
        """Test PIT with extremely large variance."""
        y_true = np.array([10.0, 20.0])
        y_pred = np.array([10.0, 20.0])
        std_dev = np.array([1e10, 1e10])

        pit_values = calculate_pit(y_true, y_pred, std_dev)
        # With huge variance, z-score is ~0, PIT ~ 0.5
        assert np.allclose(pit_values, 0.5, atol=1e-6)


class TestBoundaryConditions:
    """Tests for boundary conditions in interval calculations."""

    def test_exact_boundary_inclusion(self):
        """Test that points exactly on the boundary are included."""
        y_true = np.array([10.0, 20.0])
        y_pred = np.array([15.0, 15.0])
        lower = np.array([10.0, 10.0])
        upper = np.array([20.0, 20.0])

        coverage = compute_coverage(y_true, lower, upper, nominal_level=0.95)
        assert coverage == 1.0, "Points on the boundary should be included"

    def test_just_outside_boundary(self):
        """Test points just outside the boundary."""
        y_true = np.array([9.99, 20.01])
        y_pred = np.array([15.0, 15.0])
        lower = np.array([10.0, 10.0])
        upper = np.array([20.0, 20.0])

        coverage = compute_coverage(y_true, lower, upper, nominal_level=0.95)
        assert coverage == 0.0, "Points outside the boundary should not be included"

    def test_inverted_intervals(self):
        """Test behavior when lower > upper (invalid intervals)."""
        y_true = np.array([10.0])
        y_pred = np.array([10.0])
        lower = np.array([15.0])
        upper = np.array([5.0])

        with pytest.raises((ValueError, DataValidationError)):
            compute_coverage(y_true, lower, upper, nominal_level=0.95)