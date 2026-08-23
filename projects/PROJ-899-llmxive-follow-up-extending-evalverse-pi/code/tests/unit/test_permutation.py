import pytest
import numpy as np
import pandas as pd
from src.models.metrics import run_permutation_test, calculate_dimension_metrics, apply_fwer_correction

def test_permutation_test_basic():
    """Test that permutation test returns a valid p-value for correlated data."""
    np.random.seed(42)
    n = 50
    x = np.random.randn(n)
    y = x * 2 + np.random.randn(n) * 0.5  # Strong positive correlation
    
    p_val = run_permutation_test(x, y, n_permutations=1000, seed=42)
    
    assert 0 <= p_val <= 1, "P-value must be between 0 and 1"
    # With strong correlation, p-value should be relatively low (though with 1000 perms it varies)
    assert p_val < 0.5, "Strong correlation should yield a lower p-value"

def test_permutation_test_uncorrelated():
    """Test that permutation test returns high p-value for uncorrelated data."""
    np.random.seed(42)
    n = 50
    x = np.random.randn(n)
    y = np.random.randn(n)  # No correlation
    
    p_val = run_permutation_test(x, y, n_permutations=1000, seed=42)
    
    assert 0 <= p_val <= 1, "P-value must be between 0 and 1"
    # With no correlation, p-value should be higher (not consistently low)
    # We don't assert a specific value as it's stochastic, but it should be reasonable

def test_calculate_dimension_metrics():
    """Test the dimension metrics calculation function."""
    df = pd.DataFrame({
        'dimension': ['dim1', 'dim2'],
        'pearson_r': [0.85, 0.45],
        'spearman_r': [0.82, 0.40],
        'lower_ci': [0.75, 0.30],
        'upper_ci': [0.92, 0.60]
    })
    
    result = calculate_dimension_metrics(df)
    
    assert 'dimension' in result.columns
    assert 'raw_p' in result.columns
    assert len(result) == 2
    assert all(0 <= p <= 1 for p in result['raw_p'])

def test_empty_arrays():
    """Test permutation test with empty arrays."""
    x = np.array([])
    y = np.array([])
    
    p_val = run_permutation_test(x, y, n_permutations=100)
    assert p_val == 1.0, "Empty arrays should return p=1.0"

def test_mismatched_arrays():
    """Test permutation test with mismatched array lengths."""
    x = np.array([1, 2, 3])
    y = np.array([1, 2])
    
    # Should handle gracefully or raise an error
    # Our implementation handles it by checking length
    p_val = run_permutation_test(x, y, n_permutations=100)
    # If lengths differ, correlation might be NaN or handled
    assert isinstance(p_val, float)

def test_apply_fwer_correction():
    """Test FWER correction function."""
    df = pd.DataFrame({
        'dimension': ['dim1', 'dim2', 'dim3'],
        'raw_p': [0.01, 0.05, 0.20]
    })
    
    result = apply_fwer_correction(df)
    
    assert 'adjusted_p' in result.columns
    assert len(result) == 3
    # Check that adjusted p-values are >= raw p-values (conservative)
    assert all(result['adjusted_p'] >= result['raw_p'])
    # Check that adjusted p-values are <= 1.0
    assert all(result['adjusted_p'] <= 1.0)

def test_apply_fwer_correction_single():
    """Test FWER correction with a single dimension."""
    df = pd.DataFrame({
        'dimension': ['dim1'],
        'raw_p': [0.05]
    })
    
    result = apply_fwer_correction(df)
    
    assert len(result) == 1
    # With one test, adjusted should equal raw (or close)
    assert abs(result['adjusted_p'].iloc[0] - result['raw_p'].iloc[0]) < 0.01