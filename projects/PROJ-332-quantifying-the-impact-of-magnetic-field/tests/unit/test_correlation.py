"""
Unit Tests for Correlation Analysis Module.

This module contains unit tests for the correlation and stratification logic.
"""
import pytest
import pandas as pd
import numpy as np
from analysis.correlation import stratify_by_mode, check_multicollinearity

def test_stratify_by_mode():
    """
    Test stratification logic.
    """
    df = pd.DataFrame({
        'value': [1, 2, 3, 4, 5],
        'mode': ['H-mode', 'L-mode', 'H-mode', 'L-mode', 'H-mode']
    })
    
    groups = stratify_by_mode(df)
    
    assert 'H-mode' in groups
    assert 'L-mode' in groups
    assert len(groups['H-mode']) == 3
    assert len(groups['L-mode']) == 2

def test_check_multicollinearity():
    """
    Test multicollinearity check.
    """
    # Create highly correlated variables
    x = np.linspace(0, 10, 100)
    y = x * 2 + np.random.normal(0, 0.1, 100)
    df = pd.DataFrame({'var1': x, 'var2': y})
    
    result = check_multicollinearity(df, 'var1', 'var2', threshold=0.9)
    
    assert result['collinearity_flag'] is True
    assert 'var2' in result['excluded_variables']

def test_bootstrap_reproducibility():
    """
    Test that bootstrap results are reproducible with fixed seed.
    """
    np.random.seed(42)
    x = np.random.normal(0, 1, 50)
    y = np.random.normal(0, 1, 50)
    
    from analysis.correlation import calculate_spearman_correlation
    result1 = calculate_spearman_correlation(x, y, bootstrap_iterations=100, random_seed=42)
    result2 = calculate_spearman_correlation(x, y, bootstrap_iterations=100, random_seed=42)
    
    assert result1['r'] == result2['r']
    assert result1['ci_lower'] == result2['ci_lower']
