"""
Unit tests for utils.metrics statistical functions.
"""
import pytest
import numpy as np
from code.utils.metrics import paired_t_test, bonferroni_correct, ks_test

def test_paired_t_test_identical():
    """Test that identical sequences yield p-value of 1.0."""
    a = [1.0, 2.0, 3.0, 4.0, 5.0]
    b = [1.0, 2.0, 3.0, 4.0, 5.0]
    t_stat, p_val = paired_t_test(a, b)
    assert np.isclose(p_val, 1.0)
    assert np.isclose(t_stat, 0.0)

def test_paired_t_test_different():
    """Test paired t-test with known distinct sequences."""
    # Known example: significant difference expected
    a = [10.0, 11.0, 12.0]
    b = [1.0, 2.0, 3.0]
    t_stat, p_val = paired_t_test(a, b)
    assert p_val < 0.05  # Should be significant
    assert t_stat > 0    # First group is larger

def test_paired_t_test_length_mismatch():
    """Test that length mismatch raises ValueError."""
    with pytest.raises(ValueError):
        paired_t_test([1, 2, 3], [1, 2])

def test_paired_t_test_empty():
    """Test that empty sequences raise ValueError."""
    with pytest.raises(ValueError):
        paired_t_test([], [])

def test_bonferroni_correct():
    """Test Bonferroni correction logic."""
    p_vals = [0.01, 0.04, 0.06]
    n = 5
    corrected = bonferroni_correct(p_vals, n)
    expected = [0.05, 0.20, 0.30] # 0.01*5, 0.04*5, 0.06*5
    assert corrected == expected

def test_bonferroni_cap():
    """Test that Bonferroni corrected values are capped at 1.0."""
    p_vals = [0.5, 0.6]
    n = 2
    corrected = bonferroni_correct(p_vals, n)
    assert corrected == [1.0, 1.0]

def test_ks_test_identical():
    """Test KS test on identical distributions."""
    a = [1, 2, 3, 4, 5]
    b = [1, 2, 3, 4, 5]
    ks_stat, p_val = ks_test(a, b)
    assert np.isclose(ks_stat, 0.0)
    assert np.isclose(p_val, 1.0)

def test_ks_test_different():
    """Test KS test on clearly different distributions."""
    a = [1, 2, 3]
    b = [100, 101, 102]
    ks_stat, p_val = ks_test(a, b)
    assert ks_stat > 0.9 # Should be very different
    assert p_val < 0.05