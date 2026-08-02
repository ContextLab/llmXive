"""
Unit tests for mathematical utility functions in code/utils/math_utils.py.
"""
import numpy as np
import pytest
from code.utils.math_utils import (
    interpolate_missing_timesteps,
    safe_z_score,
    handle_nan,
    rolling_std_dev,
    calculate_pearson_correlation
)


class TestInterpolateMissingTimesteps:
    def test_linear_interpolation_simple(self):
        times = np.array([0, 2, 4])
        values = np.array([0, 2, 4])
        filled_times, filled_values = interpolate_missing_timesteps(times, values)

        assert len(filled_times) == 5  # 0, 1, 2, 3, 4
        assert filled_times[1] == 1
        assert filled_values[1] == 1.0

    def test_no_gaps(self):
        times = np.array([0, 1, 2, 3])
        values = np.array([0, 1, 2, 3])
        filled_times, filled_values = interpolate_missing_timesteps(times, values)

        np.testing.assert_array_equal(filled_times, times)
        np.testing.assert_array_almost_equal(filled_values, values)

    def test_mismatched_lengths_raises(self):
        times = np.array([0, 1, 2])
        values = np.array([0, 1])
        with pytest.raises(ValueError):
            interpolate_missing_timesteps(times, values)

    def test_single_element(self):
        times = np.array([5])
        values = np.array([10])
        filled_times, filled_values = interpolate_missing_timesteps(times, values)
        np.testing.assert_array_equal(filled_times, times)
        np.testing.assert_array_equal(filled_values, values)


class TestSafeZScore:
    def test_normal_case(self):
        values = np.array([1, 2, 3, 4, 5, 6, 7, 8, 9, 10])
        z_scores = safe_z_score(values, window_size=5, min_samples=3)

        assert len(z_scores) == len(values)
        # First few should be 0 due to min_samples constraint
        assert z_scores[0] == 0.0
        assert z_scores[1] == 0.0
        assert z_scores[2] == 0.0

    def test_zero_variance_returns_zero(self):
        values = np.array([5.0, 5.0, 5.0, 5.0, 5.0, 5.0, 5.0, 5.0, 5.0, 5.0])
        z_scores = safe_z_score(values, window_size=5, min_samples=3)

        assert np.all(z_scores == 0.0)

    def test_less_than_min_samples(self):
        values = np.array([1, 2, 3])
        z_scores = safe_z_score(values, window_size=5, min_samples=5)
        assert np.all(z_scores == 0.0)

    def test_epsilon_floor_prevents_division_by_zero(self):
        # Create a case where std is extremely small but not exactly zero
        values = np.array([1.0, 1.0 + 1e-15, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0])
        z_scores = safe_z_score(values, window_size=5, min_samples=3, epsilon=1e-9)
        # Should not raise, and should return 0 for near-zero std
        assert len(z_scores) == len(values)


class TestHandleNaN:
    def test_forward_fill(self):
        values = np.array([1.0, np.nan, np.nan, 4.0, 5.0])
        result = handle_nan(values, strategy='forward_fill')
        expected = np.array([1.0, 1.0, 1.0, 4.0, 5.0])
        np.testing.assert_array_almost_equal(result, expected)

    def test_backward_fill(self):
        values = np.array([1.0, np.nan, np.nan, 4.0, 5.0])
        result = handle_nan(values, strategy='backward_fill')
        expected = np.array([1.0, 4.0, 4.0, 4.0, 5.0])
        np.testing.assert_array_almost_equal(result, expected)

    def test_replace_with_mean(self):
        values = np.array([1.0, np.nan, 3.0, 4.0, 5.0])
        result = handle_nan(values, strategy='mean')
        expected_mean = (1 + 3 + 4 + 5) / 4
        assert result[1] == expected_mean

    def test_replace_with_zero(self):
        values = np.array([1.0, np.nan, 3.0])
        result = handle_nan(values, strategy='zero')
        expected = np.array([1.0, 0.0, 3.0])
        np.testing.assert_array_almost_equal(result, expected)

    def test_no_nan_unchanged(self):
        values = np.array([1.0, 2.0, 3.0])
        result = handle_nan(values)
        np.testing.assert_array_almost_equal(result, values)

    def test_all_nan(self):
        values = np.array([np.nan, np.nan, np.nan])
        result = handle_nan(values, strategy='forward_fill')
        # Should default to 0.0 if all are NaN
        assert np.all(result == 0.0)

    def test_invalid_strategy_raises(self):
        values = np.array([1.0, np.nan, 2.0])
        with pytest.raises(ValueError):
            handle_nan(values, strategy='invalid_strategy')


class TestRollingStdDev:
    def test_basic_calculation(self):
        values = np.array([1, 2, 3, 4, 5, 6, 7, 8, 9, 10])
        std_devs = rolling_std_dev(values, window_size=3, min_samples=2)
        assert len(std_devs) == len(values)
        assert std_devs[0] == 0.0  # Only 1 sample

    def test_mask_excludes_indices(self):
        values = np.array([1, 2, 3, 100, 5, 6, 7, 8, 9, 10])
        mask = np.array([False, False, False, True, False, False, False, False, False, False])
        std_devs = rolling_std_dev(values, window_size=5, min_samples=3, mask=mask)
        # The outlier at index 3 should be excluded from the window
        assert len(std_devs) == len(values)

    def test_insufficient_samples_returns_zero(self):
        values = np.array([1, 2, 3, 4, 5])
        mask = np.array([True, True, True, True, True])
        std_devs = rolling_std_dev(values, window_size=5, min_samples=3, mask=mask)
        # All indices masked, so no valid samples -> 0.0
        assert np.all(std_devs == 0.0)


class TestPearsonCorrelation:
    def test_perfect_positive_correlation(self):
        x = np.array([1, 2, 3, 4, 5])
        y = np.array([2, 4, 6, 8, 10])
        corr = calculate_pearson_correlation(x, y)
        assert np.isclose(corr, 1.0)

    def test_perfect_negative_correlation(self):
        x = np.array([1, 2, 3, 4, 5])
        y = np.array([5, 4, 3, 2, 1])
        corr = calculate_pearson_correlation(x, y)
        assert np.isclose(corr, -1.0)

    def test_no_correlation(self):
        x = np.array([1, 2, 3, 4, 5])
        y = np.array([5, 1, 4, 2, 3])
        corr = calculate_pearson_correlation(x, y)
        # Not exactly zero, but should be low
        assert abs(corr) < 0.5

    def test_mismatched_lengths_raises(self):
        x = np.array([1, 2, 3])
        y = np.array([1, 2])
        with pytest.raises(ValueError):
            calculate_pearson_correlation(x, y)

    def test_with_nan_values(self):
        x = np.array([1, np.nan, 3, 4, 5])
        y = np.array([2, 4, np.nan, 8, 10])
        corr = calculate_pearson_correlation(x, y)
        # Should handle NaNs gracefully
        assert -1.0 <= corr <= 1.0

    def test_single_element(self):
        x = np.array([1])
        y = np.array([2])
        corr = calculate_pearson_correlation(x, y)
        assert corr == 0.0