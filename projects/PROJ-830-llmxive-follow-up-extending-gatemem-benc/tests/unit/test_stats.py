"""
Unit tests for statistics module.
"""
import pytest
import pandas as pd
import numpy as np
from code.utils.stats import (
    shapiro_wilk_test,
    fit_lmm,
    run_post_hoc,
    domain_stratified_analysis,
    pair_episodes,
    InfeasibleError
)

def test_shapiro_wilk_returns_p_value():
    """Test that Shapiro-Wilk returns a valid p-value."""
    # Normal data
    data = np.random.normal(0, 1, 100)
    res = shapiro_wilk_test(data.tolist())
    
    assert 'p_value' in res
    assert 'statistic' in res
    assert 'is_normal' in res
    assert 0.0 <= res['p_value'] <= 1.0
    assert isinstance(res['is_normal'], bool)

def test_fit_lmm_returns_dict():
    """Test that LMM returns expected dictionary."""
    # Create dummy data
    np.random.seed(42)
    n = 50
    data = pd.DataFrame({
        'score': np.random.randn(n),
        'method': np.random.choice(['A', 'B'], n),
        'Domain': np.random.choice(['D1', 'D2', 'D3'], n)
    })
    
    res = fit_lmm(data)
    
    assert 'p_value' in res
    assert 'test_statistic' in res
    assert 'method_used' in res
    assert res['method_used'] == 'LMM'

def test_run_post_hoc_returns_dict():
    """Test post-hoc test selection and output."""
    g = [1, 2, 3, 4, 5]
    b = [1.1, 2.2, 3.1, 4.2, 5.1]
    
    # Normal
    res_normal = run_post_hoc(g, b, is_normal=True)
    assert res_normal['method_used'] == 'paired_t_test'
    assert 'p_value' in res_normal
    
    # Non-normal
    res_non_normal = run_post_hoc(g, b, is_normal=False)
    assert res_non_normal['method_used'] == 'wilcoxon'

def test_pair_episodes_returns_pairs():
    """Test episode pairing logic."""
    g_data = [
        {'episode_id': '1', 'score': 0.5},
        {'episode_id': '2', 'score': 0.6}
    ]
    b_data = [
        {'episode_id': '1', 'score': 0.4},
        {'episode_id': '2', 'score': 0.7}
    ]
    
    pairs = pair_episodes(g_data, b_data)
    assert len(pairs) == 2
    assert pairs[0] == (0.5, 0.4)
    assert pairs[1] == (0.6, 0.7)

def test_pair_episodes_mismatched_ids():
    """Test that mismatched IDs raise ValueError."""
    g_data = [{'episode_id': '1', 'score': 0.5}]
    b_data = [{'episode_id': '2', 'score': 0.4}]
    
    with pytest.raises(ValueError):
        pair_episodes(g_data, b_data)

def test_domain_stratified_analysis_returns_dict():
    """Test domain-stratified analysis returns expected structure."""
    # Create mock data with domain
    g_data = [
        {'episode_id': '1', 'score': 0.5, 'domain': 'med'},
        {'episode_id': '2', 'score': 0.6, 'domain': 'med'},
        {'episode_id': '3', 'score': 0.7, 'domain': 'off'},
        {'episode_id': '4', 'score': 0.8, 'domain': 'off'}
    ]
    b_data = [
        {'episode_id': '1', 'score': 0.4, 'domain': 'med'},
        {'episode_id': '2', 'score': 0.5, 'domain': 'med'},
        {'episode_id': '3', 'score': 0.6, 'domain': 'off'},
        {'episode_id': '4', 'score': 0.7, 'domain': 'off'}
    ]
    
    res = domain_stratified_analysis(g_data, b_data)
    
    assert 'p_value' in res
    assert 'test_statistic' in res
    assert 'method_used' in res
    assert 'fallback_reason' in res
    assert 'stratified_p_values' in res

def test_infeasible_error_raised():
    """Test that InfeasibleError is raised for insufficient data."""
    with pytest.raises(InfeasibleError):
        shapiro_wilk_test([1, 2]) # Too few samples

def test_lmm_infeasible_raises():
    """Test that LMM raises InfeasibleError for insufficient data."""
    data = pd.DataFrame({
        'score': [1.0],
        'method': ['A'],
        'Domain': ['D1']
    })
    with pytest.raises(InfeasibleError):
        fit_lmm(data)