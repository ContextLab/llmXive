"""
Unit tests for numerical stability utilities in code/data_generation/utils.py.

This module verifies:
- apply_epsilon_floor behavior on scalars and arrays
- safe_log, safe_divide, and check_numerical_stability functions
- Drift model functions (linear, exponential, sinusoidal)
- get_drift_model factory function
"""
import pytest
import numpy as np
from data_generation.utils import (
    apply_epsilon_floor,
    safe_log,
    safe_divide,
    check_numerical_stability,
    linear_drift,
    exponential_drift,
    sinusoidal_drift,
    get_drift_model,
    DEFAULT_EPSILON
)

class TestApplyEpsilonFloor:
    """Tests for the apply_epsilon_floor function."""

    def test_apply_epsilon_floor_scalar_below_epsilon(self):
        """Test that a scalar below epsilon is floored to epsilon."""
        result = apply_epsilon_floor(1e-10, epsilon=1e-6)
        assert result == 1e-6
        assert isinstance(result, float)

    def test_apply_epsilon_floor_scalar_above_epsilon(self):
        """Test that a scalar above epsilon is unchanged."""
        result = apply_epsilon_floor(1e-4, epsilon=1e-6)
        assert result == 1e-4

    def test_apply_epsilon_floor_array_below_epsilon(self):
        """Test that array values below epsilon are floored."""
        arr = np.array([1e-10, 1e-12, 0.0])
        result = apply_epsilon_floor(arr, epsilon=1e-6)
        expected = np.array([1e-6, 1e-6, 1e-6])
        np.testing.assert_array_equal(result, expected)

    def test_apply_epsilon_floor_array_mixed(self):
        """Test array with mixed values (some above, some below epsilon)."""
        arr = np.array([1e-10, 1e-4, 0.0, 1e-3])
        result = apply_epsilon_floor(arr, epsilon=1e-6)
        expected = np.array([1e-6, 1e-4, 1e-6, 1e-3])
        np.testing.assert_array_equal(result, expected)

    def test_apply_epsilon_floor_default_epsilon(self):
        """Test that default epsilon is used when not specified."""
        arr = np.array([1e-10, 1e-9])
        result = apply_epsilon_floor(arr)
        expected = np.array([DEFAULT_EPSILON, DEFAULT_EPSILON])
        np.testing.assert_array_equal(result, expected)

    def test_apply_epsilon_floor_no_negative_values(self):
        """Test that negative values are also floored (not clamped to zero)."""
        arr = np.array([-1.0, -0.5])
        result = apply_epsilon_floor(arr, epsilon=1e-6)
        expected = np.array([1e-6, 1e-6])
        np.testing.assert_array_equal(result, expected)

class TestSafeLog:
    """Tests for the safe_log function."""

    def test_safe_log_zero(self):
        """Test that log(0) is handled safely by applying epsilon floor."""
        result = safe_log(0.0)
        assert not np.isnan(result)
        assert not np.isinf(result)
        # Should be log(epsilon)
        assert result == np.log(DEFAULT_EPSILON)

    def test_safe_log_small_value(self):
        """Test log of a very small positive value."""
        result = safe_log(1e-10, epsilon=1e-6)
        assert result == np.log(1e-6)

    def test_safe_log_normal_value(self):
        """Test log of a normal value."""
        result = safe_log(np.e)
        assert np.isclose(result, 1.0)

    def test_safe_log_array(self):
        """Test safe_log on an array with zeros."""
        arr = np.array([0.0, 1.0, np.e])
        result = safe_log(arr, epsilon=1e-6)
        expected = np.array([np.log(1e-6), 0.0, 1.0])
        np.testing.assert_array_almost_equal(result, expected)

class TestSafeDivide:
    """Tests for the safe_divide function."""

    def test_safe_divide_zero_denominator(self):
        """Test division by zero is handled safely."""
        result = safe_divide(1.0, 0.0, epsilon=1e-6)
        assert result == 1.0 / 1e-6

    def test_safe_divide_normal(self):
        """Test normal division."""
        result = safe_divide(10.0, 2.0)
        assert result == 5.0

    def test_safe_divide_array(self):
        """Test safe_divide on arrays."""
        num = np.array([1.0, 2.0, 3.0])
        denom = np.array([0.0, 1.0, 2.0])
        result = safe_divide(num, denom, epsilon=1e-6)
        expected = np.array([1.0/1e-6, 2.0, 1.5])
        np.testing.assert_array_almost_equal(result, expected)

class TestCheckNumericalStability:
    """Tests for the check_numerical_stability function."""

    def test_stable_array(self):
        """Test that a stable array returns True."""
        arr = np.array([1.0, 2.0, 3.0])
        assert check_numerical_stability(arr, name="test") is True

    def test_nan_array_raises(self):
        """Test that an array with NaN raises ValueError."""
        arr = np.array([1.0, np.nan, 3.0])
        with pytest.raises(ValueError, match="NaN values detected"):
            check_numerical_stability(arr, name="test")

    def test_inf_array_raises(self):
        """Test that an array with Inf raises ValueError."""
        arr = np.array([1.0, np.inf, 3.0])
        with pytest.raises(ValueError, match="Inf values detected"):
            check_numerical_stability(arr, name="test")

class TestDriftModels:
    """Tests for drift model functions."""

    def test_linear_drift_monotonicity(self):
        """Test that linear drift is monotonic with positive slope."""
        t = np.arange(0, 100)
        result = linear_drift(t, slope=0.01, intercept=1.0)
        assert np.all(np.diff(result) >= 0)

    def test_linear_drift_intercept(self):
        """Test that linear drift starts at intercept."""
        result = linear_drift(0, slope=0.01, intercept=5.0)
        assert result == 5.0

    def test_exponential_drift_growth(self):
        """Test that exponential drift grows with positive rate."""
        t = np.arange(0, 10)
        result = exponential_drift(t, rate=0.1, initial=1.0)
        assert np.all(np.diff(result) > 0)

    def test_exponential_drift_initial(self):
        """Test that exponential drift starts at initial value."""
        result = exponential_drift(0, rate=0.1, initial=2.0)
        assert result == 2.0

    def test_sinusoidal_drift_bounds(self):
        """Test that sinusoidal drift stays within expected bounds."""
        t = np.arange(0, 100)
        amplitude = 0.5
        offset = 1.0
        result = sinusoidal_drift(t, amplitude=amplitude, offset=offset)
        assert np.all(result >= offset - amplitude)
        assert np.all(result <= offset + amplitude)

    def test_sinusoidal_drift_periodicity(self):
        """Test that sinusoidal drift is periodic."""
        frequency = 0.1
        t = np.arange(0, 100)
        result = sinusoidal_drift(t, frequency=frequency)
        period = 1.0 / frequency
        # Check values at t=0 and t=period are approximately equal
        assert np.isclose(result[0], result[int(period)], atol=1e-10)

class TestGetDriftModel:
    """Tests for the get_drift_model factory function."""

    def test_get_linear_drift(self):
        """Test retrieving the linear drift model."""
        func = get_drift_model('linear')
        assert func is linear_drift

    def test_get_exponential_drift(self):
        """Test retrieving the exponential drift model."""
        func = get_drift_model('exponential')
        assert func is exponential_drift

    def test_get_sinusoidal_drift(self):
        """Test retrieving the sinusoidal drift model."""
        func = get_drift_model('sinusoidal')
        assert func is sinusoidal_drift

    def test_get_unknown_drift_raises(self):
        """Test that requesting an unknown drift model raises ValueError."""
        with pytest.raises(ValueError, match="Unknown drift model"):
            get_drift_model('unknown')