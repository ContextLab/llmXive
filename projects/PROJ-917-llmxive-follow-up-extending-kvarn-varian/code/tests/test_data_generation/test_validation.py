"""
Tests for validation checks in data generation.
"""
import pytest
import numpy as np
from data_generation.utils import check_numerical_stability

def test_validation_pass():
    """Valid data should pass."""
    data = np.array([1.0, 2.0, 3.0])
    assert check_numerical_stability(data) is True

def test_validation_fail_nan():
    """Data with NaN should fail."""
    data = np.array([1.0, np.nan, 3.0])
    assert check_numerical_stability(data) is False

def test_validation_fail_inf():
    """Data with Inf should fail."""
    data = np.array([1.0, np.inf, 3.0])
    assert check_numerical_stability(data) is False
