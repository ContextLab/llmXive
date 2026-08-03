"""
Unit tests for the Benjamini-Hochberg FDR correction module.
"""
import pytest
import numpy as np
import pandas as pd
from code.fdr_correction import apply_benjamini_hochberg, apply_fdr_to_model_results

def test_bh_independent_uniform():
    """
    Test BH procedure with uniformly distributed p-values.
    Under the null, we expect roughly alpha proportion of rejections if we set alpha high,
    but for uniform(0,1), the number of rejections should be controlled.
    Specifically, if all nulls are true, FDR <= alpha.
    """
    np.random.seed(42)
    n = 1000
    p_vals = np.random.uniform(0, 1, n)
    
    rejected, adj_p, _ = apply_benjamini_hochberg(p_vals, alpha=0.05)
    
    # Check monotonicity of adjusted p-values
    assert np.all(np.diff(adj_p) >= -1e-9), "Adjusted p-values must be monotonic non-decreasing"
    
    # Check that adjusted p-values are in [0, 1]
    assert np.all((adj_p >= 0) & (adj_p <= 1))
    
    # Check that rejections correspond to adj_p <= alpha
    assert np.all((adj_p <= 0.05) == rejected)

def test_bh_small_set_known():
    """
    Test BH on a small set of p-values with known outcome.
    P-values: [0.001, 0.01, 0.02, 0.03, 0.04, 0.5, 0.6]
    m = 7
    Sorted: same
    Thresholds: (i/7)*0.05
    i=1: 0.001 <= 0.0071 (True)
    i=2: 0.01 <= 0.0142 (True)
    i=3: 0.02 <= 0.0214 (True)
    i=4: 0.03 <= 0.0285 (False) -> Stop. Rejection set: 1, 2, 3.
    """
    p_vals = np.array([0.001, 0.01, 0.02, 0.03, 0.04, 0.5, 0.6])
    rejected, adj_p, _ = apply_benjamini_hochberg(p_vals, alpha=0.05)
    
    expected_rejected = [True, True, True, False, False, False, False]
    assert np.array_equal(rejected, expected_rejected), f"Expected {expected_rejected}, got {rejected}"
    
    # Verify adjusted p-values are calculated correctly
    # adj_p[0] should be (7/1)*0.001 = 0.007
    # adj_p[1] should be (7/2)*0.01 = 0.035
    # adj_p[2] should be (7/3)*0.02 = 0.0466...
    # Check approximate values
    assert abs(adj_p[0] - 0.007) < 1e-4
    assert abs(adj_p[1] - 0.035) < 1e-4
    assert adj_p[2] < 0.05 # Must be rejected

def test_bh_empty_array():
    """Test with empty array."""
    p_vals = np.array([])
    rejected, adj_p, _ = apply_benjamini_hochberg(p_vals)
    assert len(rejected) == 0
    assert len(adj_p) == 0

def test_bh_with_nans():
    """Test behavior with NaN values (should be handled in the wrapper, but core might not)."""
    # The core function assumes valid floats. The wrapper handles NaNs.
    # We test the wrapper here.
    df = pd.DataFrame({
        'p_val': [0.01, np.nan, 0.05, 0.99],
        'other': [1, 2, 3, 4]
    })
    result = apply_fdr_to_model_results(df, ['p_val'], alpha=0.05)
    
    assert 'p_val_adj' in result.columns
    assert 'p_val_reject' in result.columns
    assert pd.isna(result.loc[1, 'p_val_adj'])
    assert result.loc[1, 'p_val_reject'] == False

def test_bh_monotonicity_property():
    """
    Ensure that if p_i < p_j, then adj_p_i <= adj_p_j.
    """
    np.random.seed(123)
    p_vals = np.random.uniform(0, 1, 100)
    _, adj_p, _ = apply_benjamini_hochberg(p_vals, alpha=0.05)
    
    # Sort by original p-values and check adjusted p-values are sorted
    sorted_indices = np.argsort(p_vals)
    sorted_adj = adj_p[sorted_indices]
    
    assert np.all(np.diff(sorted_adj) >= -1e-9), "Adjusted p-values must be monotonic with respect to sorted p-values"
