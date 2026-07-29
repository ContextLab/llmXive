"""
tests/unit/test_analysis.py
Unit tests for code/analysis.py
"""
import pytest
import pandas as pd
import numpy as np
from scipy import stats
from code.analysis import _run_t_test, _run_linear_regression, _compute_cohens_d

def test_compute_cohens_d():
    # Group 1: mean=10, std=2, n=10
    g1 = pd.Series(np.random.RandomState(42).normal(10, 2, 100))
    # Group 2: mean=12, std=2, n=10
    g2 = pd.Series(np.random.RandomState(42).normal(12, 2, 100))
    
    d = _compute_cohens_d(g1, g2)
    # Expected approx -1.0
    assert -1.5 < d < -0.5

def test_run_t_test():
    # Create synthetic data
    np.random.seed(42)
    df = pd.DataFrame({
        'group': ['A'] * 50 + ['B'] * 50,
        'value': list(np.random.normal(10, 2, 50)) + list(np.random.normal(12, 2, 50))
    })
    
    res = _run_t_test(df, 'value', 'group')
    
    assert 'p_value' in res
    assert 'ci_lower' in res
    assert 'ci_upper' in res
    assert 'cohen_d' in res
    
    # P-value should be significant (small)
    assert 0 < res['p_value'] < 0.05

def test_run_linear_regression():
    np.random.seed(42)
    n = 100
    x = np.random.normal(0, 1, n)
    y = 2 * x + np.random.normal(0, 0.5, n)
    
    df = pd.DataFrame({'y': y, 'x': x})
    
    res = _run_linear_regression(df, 'y', ['x'])
    
    assert 'r_squared' in res
    assert 'p_values' in res
    assert 'x' in res['p_values']
    
    # R2 should be high
    assert res['r_squared'] > 0.8
    # P-value for x should be small
    assert 0 < res['p_values']['x'] < 0.05
