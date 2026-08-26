"""
Unit tests for permutation testing and Westfall-Young correction (T020).
"""
import pytest
import numpy as np
import pandas as pd
from src.models.metrics import run_permutation_test, calculate_dimension_metrics, apply_fwer_correction

def test_permutation_test_basic():
    """Test permutation test with correlated data."""
    np.random.seed(42)
    n = 50
    x = np.random.randn(n)
    y = x + np.random.randn(n) * 0.5  # Positive correlation
    
    p_value = run_permutation_test(x, y, n_permutations=1000)
    
    # With correlation, p-value should be low
    assert p_value < 0.1, f"Expected low p-value for correlated data, got {p_value}"

def test_permutation_test_uncorrelated():
    """Test permutation test with uncorrelated data."""
    np.random.seed(42)
    n = 50
    x = np.random.randn(n)
    y = np.random.randn(n)  # No correlation
    
    p_value = run_permutation_test(x, y, n_permutations=1000)
    
    # Without correlation, p-value should be high
    assert p_value > 0.1, f"Expected high p-value for uncorrelated data, got {p_value}"

def test_calculate_dimension_metrics():
    """Test dimension metrics calculation."""
    np.random.seed(42)
    n = 30
    x = np.random.randn(n)
    y = x + np.random.randn(n) * 0.5
    
    metrics = calculate_dimension_metrics(x, y)
    
    assert 'pearson_r' in metrics
    assert 'spearman_r' in metrics
    assert 'lower_ci' in metrics
    assert 'upper_ci' in metrics
    assert 'raw_p' in metrics
    
    # Pearson should be positive
    assert metrics['pearson_r'] > 0

def test_empty_arrays():
    """Test with empty arrays."""
    p_value = run_permutation_test(np.array([]), np.array([]))
    assert p_value == 1.0

def test_mismatched_arrays():
    """Test with mismatched array lengths."""
    x = np.array([1, 2, 3])
    y = np.array([1, 2])
    
    with pytest.raises(ValueError):
        run_permutation_test(x, y)

def test_apply_fwer_correction():
    """Test FWER correction."""
    p_values = [0.01, 0.05, 0.1, 0.5]
    adjusted = apply_fwer_correction(p_values)
    
    assert len(adjusted) == len(p_values)
    assert all(0 <= p <= 1 for p in adjusted)
    # Adjusted values should be >= original
    assert all(a >= o for a, o in zip(adjusted, p_values))

def test_apply_fwer_correction_single():
    """Test FWER correction with single p-value."""
    p_values = [0.05]
    adjusted = apply_fwer_correction(p_values)
    
    assert len(adjusted) == 1
    assert adjusted[0] == 0.05  # 0.05 * 1 = 0.05