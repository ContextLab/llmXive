"""
Unit tests for stats_engine.py
"""
import pytest
import pandas as pd
import numpy as np
from scipy import stats
from code.stats_engine import (
    compute_correlation,
    construct_graph,
    calculate_stats,
    adjust_permutation_count,
    generate_null_distribution
)

def test_adjust_permutation_count_small_n():
    """Test that N is capped for small datasets."""
    # n=5, max permutations = 120
    assert adjust_permutation_count(5, 200) == 120
    assert adjust_permutation_count(5, 100) == 100 # 100 < 120, no change
    
    # n=3, max permutations = 6
    assert adjust_permutation_count(3, 10) == 6
    
    # n=10, max permutations = 3,628,800
    assert adjust_permutation_count(10, 1000) == 1000

def test_adjust_permutation_count_large_n():
    """Test that N is not capped for large datasets."""
    # n=100, max permutations is huge, so 1000 should be returned
    assert adjust_permutation_count(100, 1000) == 1000

def test_adjust_permutation_count_edge_cases():
    """Test edge cases for dataset size."""
    # n=0 or negative
    assert adjust_permutation_count(0, 100) == 100
    assert adjust_permutation_count(-1, 100) == 100
    # n=1
    assert adjust_permutation_count(1, 100) == 1

def test_generate_null_distribution_small_dataset():
    """Test that generate_null_distribution uses adjusted N for small datasets."""
    # Create a small dataset (n=4)
    np.random.seed(42)
    df = pd.DataFrame(np.random.randn(4, 5), columns=['a', 'b', 'c', 'd', 'e'])
    
    # Define a simple stats function
    def dummy_stats_func(data):
        corr = data.corr()
        edges = [abs(corr.iloc[i, j]) for i in range(len(corr)) for j in range(i+1, len(corr))]
        return {'mean_absolute_correlation': np.mean(edges)}
    
    # Request 100 permutations, but n=4 means max 24 permutations
    result = generate_null_distribution(df, n_permutations=100, stats_func=dummy_stats_func, dataset_id="test_small")
    
    # Check that actual permutations used is 24 (4!)
    assert result['n_permutations_actual'] == 24
    assert len(result['distribution']) == 24

def test_correlation_method_consistency_perfectly_linear():
    """
    Verify that Pearson and Spearman correlation calculations produce identical results
    for perfectly linear data, ensuring the scipy.stats implementation is correct and consistent.
    
    For perfectly linear data (y = ax + b), the rank order is preserved (if a > 0) or
    perfectly inverted (if a < 0). In both cases, the magnitude of the correlation
    should be 1.0 for both Pearson and Spearman.
    """
    np.random.seed(42)
    
    # Case 1: Perfect positive linear relationship (y = 2x + 1)
    x = np.random.randn(100)
    y = 2 * x + 1
    df_pos = pd.DataFrame({'x': x, 'y': y})
    
    corr_pos_pearson = compute_correlation(df_pos, method='pearson')
    corr_pos_spearman = compute_correlation(df_pos, method='spearman')
    
    # Extract the correlation between x and y
    r_pearson_pos = corr_pos_pearson.loc['x', 'y']
    r_spearman_pos = corr_pos_spearman.loc['x', 'y']
    
    # Both should be 1.0 (or extremely close due to floating point)
    assert np.isclose(r_pearson_pos, 1.0, atol=1e-10), f"Pearson should be 1.0, got {r_pearson_pos}"
    assert np.isclose(r_spearman_pos, 1.0, atol=1e-10), f"Spearman should be 1.0, got {r_spearman_pos}"
    assert np.isclose(r_pearson_pos, r_spearman_pos, atol=1e-10), "Pearson and Spearman should be identical for positive linear data"
    
    # Case 2: Perfect negative linear relationship (y = -3x + 5)
    y_neg = -3 * x + 5
    df_neg = pd.DataFrame({'x': x, 'y': y_neg})
    
    corr_neg_pearson = compute_correlation(df_neg, method='pearson')
    corr_neg_spearman = compute_correlation(df_neg, method='spearman')
    
    r_pearson_neg = corr_neg_pearson.loc['x', 'y']
    r_spearman_neg = corr_neg_spearman.loc['x', 'y']
    
    # Both should be -1.0
    assert np.isclose(r_pearson_neg, -1.0, atol=1e-10), f"Pearson should be -1.0, got {r_pearson_neg}"
    assert np.isclose(r_spearman_neg, -1.0, atol=1e-10), f"Spearman should be -1.0, got {r_spearman_neg}"
    assert np.isclose(r_pearson_neg, r_spearman_neg, atol=1e-10), "Pearson and Spearman should be identical for negative linear data"
    
    # Case 3: Multiple variables with perfect linear relationships
    z = 0.5 * x - 2
    df_multi = pd.DataFrame({'x': x, 'y': y, 'z': z})
    
    corr_multi_pearson = compute_correlation(df_multi, method='pearson')
    corr_multi_spearman = compute_correlation(df_multi, method='spearman')
    
    # Check all pairs
    pairs = [('x', 'y'), ('x', 'z'), ('y', 'z')]
    for var1, var2 in pairs:
        r_p = corr_multi_pearson.loc[var1, var2]
        r_s = corr_multi_spearman.loc[var1, var2]
        assert np.isclose(r_p, r_s, atol=1e-10), f"Pearson ({r_p}) and Spearman ({r_s}) should match for {var1}-{var2}"
        assert np.isclose(abs(r_p), 1.0, atol=1e-10), f"Correlation should be +/- 1.0 for {var1}-{var2}, got {r_p}"

def test_correlation_method_consistency_random_data():
    """
    Verify that for random independent data, Pearson and Spearman are generally
    different (as expected), but both return valid correlation values.
    """
    np.random.seed(42)
    df = pd.DataFrame(np.random.randn(100, 3), columns=['a', 'b', 'c'])
    
    corr_pearson = compute_correlation(df, method='pearson')
    corr_spearman = compute_correlation(df, method='spearman')
    
    # Both should be valid correlation matrices (values between -1 and 1)
    assert corr_pearson.values.min() >= -1.0 and corr_pearson.values.max() <= 1.0
    assert corr_spearman.values.min() >= -1.0 and corr_spearman.values.max() <= 1.0
    
    # They should generally differ for random data
    # (though they might coincidentally be close, they are unlikely to be identical)
    # We check that the matrices are not exactly equal
    assert not np.allclose(corr_pearson.values, corr_spearman.values), \
        "Pearson and Spearman should generally differ for random independent data"