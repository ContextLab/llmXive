"""
Unit tests for mathematical utility functions in code/utils/math_utils.py.
"""
import pytest
import numpy as np
import pandas as pd
from code.utils.math_utils import (
    interpolate_missing_timesteps,
    safe_z_score,
    rolling_std_dev,
    calculate_pearson_correlation
)


class TestInterpolateMissingTimesteps:
    """Tests for the interpolate_missing_timesteps function."""

    def test_no_gaps(self):
        """Test interpolation when there are no gaps."""
        df = pd.DataFrame({
            "timestep": [1, 2, 3, 4, 5],
            "value": [10.0, 20.0, 30.0, 40.0, 50.0]
        })
        result = interpolate_missing_timesteps(df, time_col="timestep")
        # Should be identical to input since there are no gaps
        assert len(result) == len(df)
        np.testing.assert_array_almost_equal(result["value"], df["value"])

    def test_with_gaps(self):
        """Test interpolation with missing timesteps."""
        df = pd.DataFrame({
            "timestep": [1, 2, 4, 5],  # Missing 3
            "value": [10.0, 20.0, 40.0, 50.0]
        })
        result = interpolate_missing_timesteps(df, time_col="timestep")

        # Should now have 5 rows (timesteps 1-5)
        assert len(result) == 5
        # Timestep 3 should be interpolated
        timestep_3 = result[result["timestep"] == 3]
        assert len(timestep_3) == 1
        # Value should be 30.0 (linear interpolation between 20 and 40)
        assert timestep_3["value"].values[0] == 30.0

    def test_multiple_value_columns(self):
        """Test interpolation with multiple value columns."""
        df = pd.DataFrame({
            "timestep": [1, 2, 4, 5],
            "value1": [10.0, 20.0, 40.0, 50.0],
            "value2": [100.0, 200.0, 400.0, 500.0]
        })
        result = interpolate_missing_timesteps(df, time_col="timestep")

        assert len(result) == 5
        # Both columns should be interpolated
        timestep_3 = result[result["timestep"] == 3]
        assert timestep_3["value1"].values[0] == 30.0
        assert timestep_3["value2"].values[0] == 300.0

    def test_invalid_time_column(self):
        """Test error when time column is missing."""
        df = pd.DataFrame({
            "time": [1, 2, 3],
            "value": [10.0, 20.0, 30.0]
        })
        with pytest.raises(ValueError):
            interpolate_missing_timesteps(df, time_col="timestep")

    def test_non_numeric_time_column(self):
        """Test error when time column is non-numeric."""
        df = pd.DataFrame({
            "timestep": ["a", "b", "c"],
            "value": [10.0, 20.0, 30.0]
        })
        with pytest.raises(ValueError):
            interpolate_missing_timesteps(df, time_col="timestep")


class TestSafeZScore:
    """Tests for the safe_z_score function."""

    def test_basic_z_score(self):
        """Test basic z-score calculation."""
        data = [10, 20, 30, 40, 50]
        result = safe_z_score(data, window_size=3, min_samples=2)
        # The middle values should have non-NaN z-scores
        assert not np.isnan(result[2])

    def test_zero_variance(self):
        """Test that zero variance returns a neutral value (0) instead of error."""
        data = [10.0, 10.0, 10.0, 10.0, 10.0]
        result = safe_z_score(data, window_size=3, min_samples=2)
        # Should not raise an error and should return 0 (or close to 0)
        for z in result:
            if not np.isnan(z):
                assert abs(z) < 1e-6

    def test_insufficient_samples(self):
        """Test behavior when samples are insufficient."""
        data = [10, 20, 30]
        result = safe_z_score(data, window_size=10, min_samples=5)
        # All values should be NaN because we never have 5 samples in a window of 10
        assert all(np.isnan(result))

    def test_min_samples_constraint(self):
        """Test that min_samples constraint is respected."""
        data = [10, 20, 30, 40, 50]
        # With min_samples=3, the first 2 values should be NaN
        result = safe_z_score(data, window_size=5, min_samples=3)
        assert np.isnan(result[0])
        assert np.isnan(result[1])
        # The third value should have a valid z-score
        assert not np.isnan(result[2])

    def test_invalid_min_samples(self):
        """Test error when min_samples < 1."""
        with pytest.raises(ValueError):
            safe_z_score([1, 2, 3], min_samples=0)

    def test_window_size_less_than_min_samples(self):
        """Test error when window_size < min_samples."""
        with pytest.raises(ValueError):
            safe_z_score([1, 2, 3], window_size=2, min_samples=3)


class TestRollingStdDev:
    """Tests for the rolling_std_dev function."""

    def test_basic_rolling_std(self):
        """Test basic rolling standard deviation."""
        data = [1, 2, 3, 4, 5]
        result = rolling_std_dev(data, window_size=3, min_samples=2)
        # Should have valid std values where window is sufficient
        assert len(result) == len(data)

    def test_zero_variance_handling(self):
        """Test that zero variance returns epsilon floor."""
        data = [5.0, 5.0, 5.0, 5.0, 5.0]
        result = rolling_std_dev(data, window_size=3, min_samples=2)
        # Should not be NaN, but should be at least epsilon
        for val in result:
            if not np.isnan(val):
                assert val >= 1e-9

    def test_insufficient_samples(self):
        """Test behavior with insufficient samples."""
        data = [1, 2, 3]
        result = rolling_std_dev(data, window_size=10, min_samples=5)
        assert all(np.isnan(result))


class TestPearsonCorrelation:
    """Tests for the calculate_pearson_correlation function."""

    def test_perfect_positive_correlation(self):
        """Test perfect positive correlation."""
        x = [1, 2, 3, 4, 5]
        y = [2, 4, 6, 8, 10]
        corr = calculate_pearson_correlation(x, y)
        assert abs(corr - 1.0) < 1e-6

    def test_perfect_negative_correlation(self):
        """Test perfect negative correlation."""
        x = [1, 2, 3, 4, 5]
        y = [5, 4, 3, 2, 1]
        corr = calculate_pearson_correlation(x, y)
        assert abs(corr - (-1.0)) < 1e-6

    def test_no_correlation(self):
        """Test no correlation."""
        x = [1, 2, 3, 4, 5]
        y = [5, 1, 4, 2, 3]
        corr = calculate_pearson_correlation(x, y)
        # Should be close to 0
        assert abs(corr) < 0.5

    def test_zero_variance(self):
        """Test behavior with zero variance in one array."""
        x = [1, 2, 3, 4, 5]
        y = [5, 5, 5, 5, 5]
        corr = calculate_pearson_correlation(x, y)
        assert np.isnan(corr)

    def test_different_lengths(self):
        """Test error when arrays have different lengths."""
        x = [1, 2, 3]
        y = [1, 2, 3, 4]
        with pytest.raises(ValueError):
            calculate_pearson_correlation(x, y)

    def test_short_arrays(self):
        """Test behavior with very short arrays."""
        x = [1, 2]
        y = [1, 2]
        corr = calculate_pearson_correlation(x, y)
        # With only 2 points, correlation should be 1 or -1 if perfectly aligned
        assert not np.isnan(corr)