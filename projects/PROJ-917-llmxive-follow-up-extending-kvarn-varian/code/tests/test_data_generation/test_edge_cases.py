"""
Tests for edge cases in data generation (NaN, Inf, extreme values).
"""
import pytest
import numpy as np
from data_generation.utils import apply_epsilon_floor, safe_log

def test_extreme_values():
    """Test handling of extreme values."""
    arr = np.array([1e300, 1e-300, np.inf, -np.inf, np.nan])
    result = apply_epsilon_floor(arr, 1e-8)
    # Should not crash
    assert len(result) == 5

def test_nan_handling():
    """Test that NaNs are handled or flagged."""
    arr = np.array([1.0, np.nan, 3.0])
    # safe_log should not crash
    result = safe_log(arr)
    assert len(result) == 3
