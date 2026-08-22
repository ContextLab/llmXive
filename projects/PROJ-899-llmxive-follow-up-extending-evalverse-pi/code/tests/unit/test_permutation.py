import pytest
import numpy as np
import pandas as pd
from src.models.metrics import run_permutation_test, calculate_dimension_metrics, apply_fwer_correction

def test_permutation_test_basic():
    """Test that permutation test returns reasonable values for correlated data."""
    np.random.seed(42)
    n = 100
    x = np.random.randn(n)
    y = 0.8 * x + 0.2 * np.random.randn(n)
    
    corr_obs, p_val = run_permutation_test(x, y, n_permutations=1000, random_seed=42)
    
    assert abs(corr_obs) > 0.5, f"Expected strong correlation, got {corr_obs}"
    assert p_val < 0.1, f"Expected small p-value for correlated data, got {p_val}"
    assert 0 <= p_val <= 1, f"p-value must be in [0, 1], got {p_val}"

def test_permutation_test_uncorrelated():
    """Test that permutation test returns high p-value for uncorrelated data."""
    np.random.seed(42)
    n = 100
    x = np.random.randn(n)
    y = np.random.randn(n)
    
    corr_obs, p_val = run_permutation_test(x, y, n_permutations=1000, random_seed=42)
    
    # For uncorrelated data, p-value should be high (not significant)
    assert p_val > 0.05, f"Expected high p-value for uncorrelated data, got {p_val}"
    assert -0.3 < corr_obs < 0.3, f"Expected weak correlation, got {corr_obs}"

def test_calculate_dimension_metrics():
    """Test calculate_dimension_metrics with a mock DataFrame."""
    np.random.seed(42)
    n = 200
    
    data = {
        'dimension': ['dim1'] * 100 + ['dim2'] * 100,
        'human_score': np.concatenate([
            np.random.randn(100),
            np.random.randn(100)
        ]),
        'vlm_proxy_score': np.concatenate([
            0.7 * np.random.randn(100) + np.random.randn(100),
            np.random.randn(100)
        ])
    }
    df = pd.DataFrame(data)
    
    result_df = calculate_dimension_metrics(df, n_permutations=500, random_seed=42)
    
    assert len(result_df) == 2, f"Expected 2 dimensions, got {len(result_df)}"
    assert 'dimension' in result_df.columns
    assert 'pearson_r' in result_df.columns
    assert 'raw_p' in result_df.columns
    assert 'lower_ci' in result_df.columns
    assert 'upper_ci' in result_df.columns

def test_empty_arrays():
    """Test that empty arrays are handled gracefully."""
    x = np.array([])
    y = np.array([])
    
    corr_obs, p_val = run_permutation_test(x, y, n_permutations=100)
    
    assert corr_obs == 0.0
    assert p_val == 1.0

def test_mismatched_arrays():
    """Test that mismatched array lengths raise an error."""
    x = np.array([1, 2, 3])
    y = np.array([1, 2])
    
    with pytest.raises(ValueError):
        run_permutation_test(x, y)

def test_apply_fwer_correction():
    """Test FWER correction on a set of p-values."""
    df = pd.DataFrame({
        'dimension': ['d1', 'd2', 'd3', 'd4', 'd5'],
        'raw_p': [0.001, 0.01, 0.05, 0.2, 0.8]
    })
    
    corrected = apply_fwer_correction(df, 'raw_p', 'adjusted_p')
    
    assert 'adjusted_p' in corrected.columns
    assert len(corrected) == 5
    
    # Check monotonicity of adjusted p-values
    adj_p = corrected['adjusted_p'].values
    for i in range(1, len(adj_p)):
        assert adj_p[i] >= adj_p[i-1], "Adjusted p-values must be monotonically non-decreasing"
    
    # Check that adjusted p-values are in [0, 1]
    assert all(0 <= p <= 1 for p in adj_p)

def test_apply_fwer_correction_single():
    """Test FWER correction with a single p-value."""
    df = pd.DataFrame({
        'dimension': ['d1'],
        'raw_p': [0.05]
    })
    
    corrected = apply_fwer_correction(df, 'raw_p', 'adjusted_p')
    
    assert len(corrected) == 1
    # For a single test, adjusted p = raw p (or min(1, 1*raw_p))
    assert corrected['adjusted_p'].iloc[0] <= 1.0
    assert corrected['adjusted_p'].iloc[0] >= 0.0