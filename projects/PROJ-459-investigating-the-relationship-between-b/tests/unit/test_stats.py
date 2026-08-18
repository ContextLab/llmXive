"""
Unit tests for statistical analysis module.
"""
import pytest
import pandas as pd
import numpy as np
from scipy.stats import spearmanr
from analysis.stats import (
    compute_spearman_correlations,
    apply_bh_correction,
    compute_power,
    flag_underpowered,
    run_null_distribution_validation
)

@pytest.fixture
def sample_metrics():
    """Generate sample metrics DataFrame."""
    np.random.seed(42)
    n = 100
    data = {
        'subject_id': [f'sub-{i:03d}' for i in range(n)],
        'global_efficiency': np.random.rand(n) * 0.5 + 0.3,
        'modularity_Q': np.random.rand(n) * 0.4 + 0.4,
        'dynamic_reconfiguration_rate': np.random.rand(n) * 0.2 + 0.1
    }
    df = pd.DataFrame(data)
    df = df.set_index('subject_id')
    return df

@pytest.fixture
def sample_genres():
    """Generate sample genre preference Series."""
    np.random.seed(42)
    n = 100
    # Create a slight positive correlation with global_efficiency for testing
    base_eff = np.random.rand(n) * 0.5 + 0.3
    genre_score = base_eff * 0.3 + np.random.rand(n) * 0.1 + 1.0 
    df = pd.DataFrame({'subject_id': [f'sub-{i:03d}' for i in range(n)], 'score': genre_score})
    df = df.set_index('subject_id')
    return df['score']

def test_compute_spearman_correlations(sample_metrics, sample_genres):
    """Test Spearman correlation computation."""
    results = compute_spearman_correlations(sample_metrics, sample_genres)
    
    assert isinstance(results, pd.DataFrame)
    assert 'metric' in results.columns
    assert 'genre' in results.columns
    assert 'r' in results.columns
    assert 'p_raw' in results.columns
    assert 'n' in results.columns
    
    # Check that we got results for all metrics
    assert len(results) == len(sample_metrics.columns)
    
    # Check that r values are within [-1, 1]
    assert results['r'].between(-1, 1).all()
    
    # Check that p values are within [0, 1]
    assert results['p_raw'].between(0, 1).all()

def test_apply_bh_correction():
    """Test Benjamini-Hochberg correction."""
    p_values = [0.01, 0.04, 0.03, 0.005, 0.06, 0.02]
    adj_p = apply_bh_correction(p_values)
    
    assert len(adj_p) == len(p_values)
    assert all(0 <= p <= 1 for p in adj_p)
    
    # BH correction should generally increase p-values (or keep same) compared to raw
    # But not strictly for all cases in all implementations, so just check bounds and monotonicity relative to sorted
    # A key property: if p1 < p2, then p1_adj <= p2_adj (monotonicity)
    # We sort raw and check if adj are sorted (monotonicity of BH)
    sorted_indices = np.argsort(p_values)
    sorted_p = [p_values[i] for i in sorted_indices]
    sorted_adj = [adj_p[i] for i in sorted_indices]
    
    for i in range(len(sorted_adj) - 1):
        assert sorted_adj[i] <= sorted_adj[i+1]

def test_compute_power():
    """Test power analysis calculation."""
    # High sample size, large effect -> high power
    power_high = compute_power(sample_size=200, effect_size=0.5)
    assert power_high > 0.8
    
    # Low sample size, small effect -> low power
    power_low = compute_power(sample_size=20, effect_size=0.1)
    assert power_low < 0.5
    
    # Edge cases
    assert compute_power(2, 0.5) == 0.0
    assert 0 <= compute_power(50, 0.3) <= 1.0

def test_flag_underpowered():
    """Test underpowered flagging."""
    assert flag_underpowered(0.9) == "Adequate"
    assert flag_underpowered(0.79) == "Underpowered"
    assert flag_underpowered(0.8) == "Adequate"

def test_null_distribution_validation(sample_metrics, sample_genres):
    """Test null distribution validation."""
    report = run_null_distribution_validation(sample_metrics, sample_genres, n_permutations=100, seed=42)
    
    assert 'false_positive_rate' in report
    assert 'permutations_count' in report
    assert report['permutations_count'] == 100
    assert 0 <= report['false_positive_rate'] <= 1.0
    
    # With random data, FPR should be close to 0.05 (alpha)
    # Allow some variance due to randomness
    assert report['false_positive_rate'] < 0.15 # Loose bound for 100 permutations