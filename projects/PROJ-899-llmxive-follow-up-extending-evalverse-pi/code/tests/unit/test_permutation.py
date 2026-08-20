"""
Unit tests for T020: Permutation-based multiple-comparison correction.
Tests the permutation logic on synthetic but deterministic data.
"""
import pytest
import numpy as np
import pandas as pd
from src.models.metrics import run_permutation_test, calculate_dimension_metrics

def test_permutation_test_basic():
    """Test that permutation test returns expected structure."""
    # Create simple correlated data
    np.random.seed(42)
    x = np.random.randn(100)
    y = x + np.random.randn(100) * 0.1  # Strong positive correlation
    
    obs_corr, p_val, fwer_thresh = run_permutation_test(x, y, n_permutations=100, random_seed=42)
    
    # Check types
    assert isinstance(obs_corr, float)
    assert isinstance(p_val, float)
    assert isinstance(fwer_thresh, float)
    
    # Check ranges
    assert -1.0 <= obs_corr <= 1.0
    assert 0.0 <= p_val <= 1.0
    assert 0.0 <= fwer_thresh <= 1.0
    
    # With strong correlation, p-value should be low
    assert p_val < 0.1

def test_permutation_test_uncorrelated():
    """Test that permutation test detects lack of correlation."""
    np.random.seed(42)
    x = np.random.randn(100)
    y = np.random.randn(100)  # Uncorrelated
    
    obs_corr, p_val, fwer_thresh = run_permutation_test(x, y, n_permutations=100, random_seed=42)
    
    # P-value should be high (not significant)
    assert p_val > 0.05

def test_calculate_dimension_metrics():
    """Test calculate_dimension_metrics function."""
    np.random.seed(42)
    n = 50
    
    # Create features
    data = {
        'clip_id': range(n),
        'dim_1': np.random.randn(n),
        'dim_2': np.random.randn(n),
        'dim_3': np.random.randn(n)
    }
    features_df = pd.DataFrame(data)
    
    # Create scores correlated with dim_1
    scores = features_df['dim_1'] + np.random.randn(n) * 0.1
    
    metrics_df = calculate_dimension_metrics(features_df.drop(columns=['clip_id']), scores, n_permutations=50, random_seed=42)
    
    # Check columns
    expected_cols = ['dimension', 'pearson_r', 'p_value', 'fwer_threshold', 'is_significant', 'n_samples']
    assert list(metrics_df.columns) == expected_cols
    
    # Check that dim_1 is significant (low p-value)
    dim_1_row = metrics_df[metrics_df['dimension'] == 'dim_1']
    assert len(dim_1_row) == 1
    assert dim_1_row['p_value'].values[0] < 0.1

def test_empty_arrays():
    """Test that empty arrays raise an error."""
    with pytest.raises(ValueError):
        run_permutation_test(np.array([]), np.array([]))

def test_mismatched_arrays():
    """Test that mismatched arrays raise an error."""
    with pytest.raises(ValueError):
        run_permutation_test(np.array([1, 2, 3]), np.array([1, 2]))
