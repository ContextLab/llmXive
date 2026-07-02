import pytest
import pandas as pd
import numpy as np
from code.feature_analysis import benjamini_hochberg, apply_bh_correction_to_df

def test_bh_correction_basic():
    """Test BH correction on a simple list of p-values."""
    p_vals = [0.01, 0.02, 0.03, 0.04, 0.10, 0.20]
    adj_p_vals, is_sig = benjamini_hochberg(p_vals, alpha=0.05)
    
    assert len(adj_p_vals) == len(p_vals)
    assert len(is_sig) == len(p_vals)
    
    # Check that adjusted p-values are >= original (conservative)
    for adj, orig in zip(adj_p_vals, p_vals):
        assert adj >= orig, f"Adjusted p-value {adj} should be >= original {orig}"
    
    # Check that adjusted p-values are <= 1.0
    for adj in adj_p_vals:
        assert adj <= 1.0, f"Adjusted p-value {adj} should be <= 1.0"
    
    # Check monotonicity (adjusted p-values should be non-decreasing when sorted by original)
    sorted_indices = np.argsort(p_vals)
    sorted_adj = [adj_p_vals[i] for i in sorted_indices]
    for i in range(1, len(sorted_adj)):
        assert sorted_adj[i] >= sorted_adj[i-1], "Adjusted p-values must be monotonic"

def test_bh_correction_empty():
    """Test BH correction on empty list."""
    adj_p_vals, is_sig = benjamini_hochberg([], alpha=0.05)
    assert adj_p_vals == []
    assert is_sig == []

def test_bh_correction_single():
    """Test BH correction on single p-value."""
    p_vals = [0.03]
    adj_p_vals, is_sig = benjamini_hochberg(p_vals, alpha=0.05)
    assert len(adj_p_vals) == 1
    assert len(is_sig) == 1
    assert adj_p_vals[0] == 0.03  # For n=1, adj = p * 1 / 1 = p

def test_bh_correction_all_significant():
    """Test when all p-values are small enough to be significant."""
    p_vals = [0.001, 0.002, 0.003]
    adj_p_vals, is_sig = benjamini_hochberg(p_vals, alpha=0.05)
    assert all(is_sig), "All should be significant with very small p-values"

def test_apply_bh_to_df():
    """Test applying BH correction to a DataFrame."""
    data = {
        'feature': ['A', 'B', 'C', 'D'],
        'p_value': [0.01, 0.04, 0.06, 0.20]
    }
    df = pd.DataFrame(data)
    
    result = apply_bh_correction_to_df(df, p_col='p_value', alpha=0.05)
    
    assert 'adj_p_value' in result.columns
    assert 'is_significant' in result.columns
    assert len(result) == 4
    
    # Check that some are significant
    assert result['is_significant'].sum() > 0

def test_apply_bh_to_df_missing_column():
    """Test error when p-value column is missing."""
    data = {'feature': ['A'], 'value': [0.01]}
    df = pd.DataFrame(data)
    
    with pytest.raises(ValueError):
        apply_bh_correction_to_df(df, p_col='p_value')
