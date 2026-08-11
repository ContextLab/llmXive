"""
Tests for the asymptotic baseline implementation (T005).
"""
import pytest
import numpy as np
import sys
import os

# Add the code directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))

from utils.asymptotic_baseline import compute_asymptotic_baseline, generate_asymptotic_series

def test_compute_asymptotic_baseline_small_n():
    """Test that small n values return 0 or very small positive numbers."""
    assert compute_asymptotic_baseline(0) == 0.0
    assert compute_asymptotic_baseline(1) == 0.0
    # For n=2, log(2) > 0, so it should return a small positive number
    val = compute_asymptotic_baseline(2)
    assert val >= 0.0
    # For very small n, the value should be small but positive
    assert val < 1.0

def test_compute_asymptotic_baseline_growth():
    """Test that the function grows with n."""
    val_100 = compute_asymptotic_baseline(100)
    val_1000 = compute_asymptotic_baseline(1000)
    val_10000 = compute_asymptotic_baseline(10000)

    # The function should be strictly increasing for large n
    assert val_100 < val_1000
    assert val_1000 < val_10000

def test_generate_asymptotic_series():
    """Test the series generation function."""
    series = generate_asymptotic_series(100, 10)
    assert len(series) == 10  # From 2 to 100 with step 10: 2, 12, ..., 92 (10 items)

    # Check structure
    for n, q_val in series:
        assert isinstance(n, int)
        assert isinstance(q_val, float)
        assert q_val >= 0.0

def test_asymptotic_formula_structure():
    """
    Verify the formula structure by checking intermediate values.
    This is a sanity check to ensure the formula is implemented correctly.
    """
    n = 1000
    log_n = np.log(n)
    exponent_arg = n / (3.0 * log_n)
    exponent = 2.0 * np.pi * np.sqrt(exponent_arg)
    denominator = (n ** 0.75) * (log_n ** 0.25)
    expected = ASYMPTOTIC_CONSTANT * np.exp(exponent) / denominator

    actual = compute_asymptotic_baseline(n)

    # Allow for small floating point differences
    assert np.isclose(actual, expected, rtol=1e-9)

# Import the constant to use in the test
from utils.asymptotic_baseline import ASYMPTOTIC_CONSTANT

def test_edge_case_very_large_n():
    """Test with a larger n to ensure no overflow and reasonable growth."""
    n = 50000
    val = compute_asymptotic_baseline(n)
    assert val > 0
    # Should be a large number but not infinity
    assert not np.isinf(val)
    assert not np.isnan(val)