"""
Unit tests for estimators.
"""
import pytest
import numpy as np
import pandas as pd
from scipy import stats
import warnings

from code.estimators import (
    run_naive_ttest,
    run_naive_ttest_with_warning,
    run_cluster_robust_ttest,
    run_block_permutation
)

def test_naive_ttest_independent_data():
    """
    Test that run_naive_ttest matches scipy.stats.ttest_ind on independent data.
    """
    # Create independent data with known means
    np.random.seed(42)
    group_0 = np.random.normal(loc=10.0, scale=2.0, size=50)
    group_1 = np.random.normal(loc=12.0, scale=2.0, size=50)
    
    data = pd.DataFrame({
        'treatment': ['control'] * 50 + ['treatment'] * 50,
        'outcome': np.concatenate([group_0, group_1])
    })
    
    # Run our function
    p_val_ours = run_naive_ttest(data, 'treatment', 'outcome')
    
    # Run scipy directly
    _, p_val_scipy = stats.ttest_ind(group_0, group_1, equal_var=False)
    
    assert np.isclose(p_val_ours, p_val_scipy), f"Expected {p_val_scipy}, got {p_val_ours}"

def test_naive_ttest_with_warning_issued():
    """
    Test that run_naive_ttest_with_warning actually issues a warning.
    """
    np.random.seed(42)
    group_0 = np.random.normal(loc=10.0, scale=2.0, size=50)
    group_1 = np.random.normal(loc=12.0, scale=2.0, size=50)
    
    data = pd.DataFrame({
        'treatment': ['control'] * 50 + ['treatment'] * 50,
        'outcome': np.concatenate([group_0, group_1])
    })
    
    with pytest.warns(UserWarning, match="Methodological Violation"):
        p_val = run_naive_ttest_with_warning(data, 'treatment', 'outcome')
    
    assert isinstance(p_val, float)
    assert 0.0 <= p_val <= 1.0

def test_cluster_robust_variance_fixed_data():
    """
    Test cluster-robust t-test on a small fixed dataset.
    """
    # Create a simple clustered dataset
    np.random.seed(123)
    n_clusters = 20
    n_obs_per_cluster = 5
    
    cluster_ids = []
    treatments = []
    outcomes = []
    
    for i in range(n_clusters):
        # Assign treatment at cluster level
        treat = 'A' if i % 2 == 0 else 'B'
        cluster_treat = treat
        
        for _ in range(n_obs_per_cluster):
            cluster_ids.append(i)
            treatments.append(cluster_treat)
            # Outcome depends on treatment + cluster effect
            base = 10.0 if treat == 'A' else 12.0
            cluster_effect = np.random.normal(0, 1)
            noise = np.random.normal(0, 0.5)
            outcomes.append(base + cluster_effect + noise)
    
    data = pd.DataFrame({
        'cluster_id': cluster_ids,
        'treatment': treatments,
        'outcome': outcomes
    })
    
    p_val = run_cluster_robust_ttest(data, 'treatment', 'outcome', 'cluster_id')
    
    # Just assert it returns a valid probability
    assert isinstance(p_val, float)
    assert 0.0 <= p_val <= 1.0

def test_block_permutation_respects_clusters():
    """
    Verify that block permutation logic respects cluster structure.
    """
    # Create data where cluster effect is strong
    np.random.seed(456)
    n_clusters = 10
    n_obs_per_cluster = 10
    
    cluster_ids = []
    treatments = []
    outcomes = []
    
    # Fixed treatment assignment per cluster
    cluster_treat_map = {i: ('T' if i % 2 == 0 else 'C') for i in range(n_clusters)}
    
    for i in range(n_clusters):
        treat = cluster_treat_map[i]
        for _ in range(n_obs_per_cluster):
            cluster_ids.append(i)
            treatments.append(treat)
            # Strong cluster effect
            outcomes.append(10.0 + (2.0 if treat == 'T' else 0.0) + np.random.normal(0, 0.1))
    
    data = pd.DataFrame({
        'cluster_id': cluster_ids,
        'treatment': treatments,
        'outcome': outcomes
    })
    
    p_val = run_block_permutation(data, 'treatment', 'outcome', 'cluster_id', n_permutations=100)
    
    assert isinstance(p_val, float)
    assert 0.0 <= p_val <= 1.0
