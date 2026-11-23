import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys
import os

# Add parent directory to path for imports if running standalone
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from code.data.lag import apply_lag_shift, calculate_l_phys

class TestLagShift:
    """Unit tests for the apply_lag_shift function in code/data/lag.py."""

    def test_lag_shift_applies_correctly(self):
        """
        Verify that apply_lag_shift correctly shifts a time series forward
        by the specified lag minutes.

        This test creates a synthetic time series with a known pattern, applies
        a lag shift, and verifies that:
        1. The values are shifted to later timestamps
        2. The beginning of the series is filled with NaNs (as expected)
        3. The end of the series is truncated (as expected)
        4. The original data integrity is preserved in the shifted portion
        """
        # Create a simple time series with a clear pattern
        # Using 5-minute cadence to match project standard
        start_time = datetime(2023, 1, 1, 0, 0, 0)
        n_points = 20
        cadence_minutes = 5

        # Create index with 5-minute intervals
        timestamps = [start_time + timedelta(minutes=i * cadence_minutes) for i in range(n_points)]

        # Create values with a simple linear pattern for easy verification
        # Values: 1, 2, 3, ..., 20
        values = np.arange(1, n_points + 1, dtype=float)

        series = pd.Series(values, index=pd.to_datetime(timestamps))

        # Apply a 15-minute lag (3 periods at 5-min cadence)
        lag_minutes = 15
        shifted_series = apply_lag_shift(series, lag_minutes)

        # Expected behavior:
        # - First 3 values (15 minutes) should be NaN
        # - Value at index 3 (20:00) should be original value at index 0 (00:00) = 1.0
        # - Value at index 4 (20:05) should be original value at index 1 (00:05) = 2.0
        # - ... and so on

        # Check that the first 3 values are NaN
        expected_nan_count = lag_minutes // cadence_minutes
        assert pd.isna(shifted_series.iloc[:expected_nan_count]).all(), \
            f"Expected {expected_nan_count} NaN values at the start, but got different count"

        # Check that the shifted values match the original values
        # The value at position i in shifted series should equal value at position i - expected_nan_count in original
        for i in range(expected_nan_count, len(series)):
            original_idx = i - expected_nan_count
            expected_value = series.iloc[original_idx]
            actual_value = shifted_series.iloc[i]
            assert actual_value == expected_value, \
                f"Mismatch at index {i}: expected {expected_value}, got {actual_value}"

        # Verify the series length is preserved
        assert len(shifted_series) == len(series), \
            f"Length mismatch: original {len(series)}, shifted {len(shifted_series)}"

        # Verify the index is preserved
        assert shifted_series.index.equals(series.index), \
            "Index mismatch between original and shifted series"

    def test_lag_shift_with_non_divisible_lag(self):
        """
        Test that apply_lag_shift handles lag values that are not perfectly
        divisible by the cadence interval.
        """
        start_time = datetime(2023, 1, 1, 0, 0, 0)
        n_points = 10
        cadence_minutes = 5

        timestamps = [start_time + timedelta(minutes=i * cadence_minutes) for i in range(n_points)]
        values = np.arange(1, n_points + 1, dtype=float)
        series = pd.Series(values, index=pd.to_datetime(timestamps))

        # Use a lag that is not a multiple of 5 (e.g., 7 minutes)
        # This should be rounded down to 1 period (5 minutes) in integer division
        lag_minutes = 7
        shifted_series = apply_lag_shift(series, lag_minutes)

        # Expected: 1 period shift (7 // 5 = 1)
        assert pd.isna(shifted_series.iloc[0]), "First value should be NaN"
        assert shifted_series.iloc[1] == 1.0, "Second value should be original first value"

    def test_lag_shift_with_zero_lag(self):
        """Test that zero lag returns the original series."""
        start_time = datetime(2023, 1, 1, 0, 0, 0)
        n_points = 5
        timestamps = [start_time + timedelta(minutes=i * 5) for i in range(n_points)]
        values = np.arange(1, n_points + 1, dtype=float)
        series = pd.Series(values, index=pd.to_datetime(timestamps))

        shifted_series = apply_lag_shift(series, 0)

        # With zero lag, series should be identical
        pd.testing.assert_series_equal(series, shifted_series)

    def test_lag_shift_preserves_data_types(self):
        """Verify that the shifted series preserves the original data types."""
        start_time = datetime(2023, 1, 1, 0, 0, 0)
        n_points = 5
        timestamps = [start_time + timedelta(minutes=i * 5) for i in range(n_points)]
        values = np.array([1.5, 2.5, 3.5, 4.5, 5.5])  # Float values
        series = pd.Series(values, index=pd.to_datetime(timestamps))

        shifted_series = apply_lag_shift(series, 10)  # 2 periods

        # Check that the non-NaN values are still floats
        non_nan_values = shifted_series.dropna()
        assert non_nan_values.dtype == float, f"Expected float dtype, got {non_nan_values.dtype}"

    def test_lag_shift_with_negative_values(self):
        """Test that the function handles negative values correctly."""
        start_time = datetime(2023, 1, 1, 0, 0, 0)
        n_points = 5
        timestamps = [start_time + timedelta(minutes=i * 5) for i in range(n_points)]
        values = np.array([-1.0, -2.0, -3.0, -4.0, -5.0])
        series = pd.Series(values, index=pd.to_datetime(timestamps))

        shifted_series = apply_lag_shift(series, 5)  # 1 period

        assert pd.isna(shifted_series.iloc[0])
        assert shifted_series.iloc[1] == -1.0
        assert shifted_series.iloc[2] == -2.0

    def test_lag_shift_with_large_lag(self):
        """Test behavior when lag exceeds series length."""
        start_time = datetime(2023, 1, 1, 0, 0, 0)
        n_points = 3
        timestamps = [start_time + timedelta(minutes=i * 5) for i in range(n_points)]
        values = np.array([1.0, 2.0, 3.0])
        series = pd.Series(values, index=pd.to_datetime(timestamps))

        # Lag of 20 minutes (4 periods) on a 3-point series
        shifted_series = apply_lag_shift(series, 20)

        # All values should be NaN since the lag exceeds the series length
        assert pd.isna(shifted_series).all(), "All values should be NaN when lag exceeds series length"