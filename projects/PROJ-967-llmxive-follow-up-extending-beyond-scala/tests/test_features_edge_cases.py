"""
Additional edge case tests for features module.
"""
import numpy as np
import pytest

from features import calculate_entropy, calculate_skewness_and_kurtosis


def test_entropy_with_nan():
    """Test entropy calculation with NaN values."""
    data = np.array([0.1, np.nan, 0.3, 0.6])
    # Should handle NaN gracefully (return NaN or 0, but not crash)
    result = calculate_entropy(data)
    # Depending on implementation, result might be NaN or 0.0
    # We just check it doesn't raise an exception
    assert result is not None


def test_skewness_with_zero_variance():
    """Test skewness with zero variance (all same values)."""
    data = np.array([5.0, 5.0, 5.0])
    skew, kurt = calculate_skewness_and_kurtosis(data)
    # Should not raise
    assert not np.isnan(skew)
    assert not np.isnan(kurt)
