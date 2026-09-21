import pytest
import pandas as pd
import numpy as np
from analysis.correlation import calculate_spearman_correlation, run_correlation_analysis, check_multicollinearity

def test_calculate_spearman_correlation_basic():
    """Test basic correlation calculation with known data."""
    x = pd.Series([1, 2, 3, 4, 5])
    y = pd.Series([2, 4, 6, 8, 10])
    
    result = calculate_spearman_correlation(x, y, seed=42, iterations=100)
    
    assert result['r'] is not None
    assert result['r'] > 0.9  # Strong positive correlation
    assert result['p_value'] < 0.05
    assert result['ci_lower'] is not None
    assert result['ci_upper'] is not None
    assert result['ci_lower'] <= result['r'] <= result['ci_upper']

def test_calculate_spearman_correlation_negative():
    """Test negative correlation."""
    x = pd.Series([1, 2, 3, 4, 5])
    y = pd.Series([5, 4, 3, 2, 1])
    
    result = calculate_spearman_correlation(x, y, seed=42, iterations=100)
    
    assert result['r'] is not None
    assert result['r'] < -0.9  # Strong negative correlation
    assert result['p_value'] < 0.05

def test_correlation_with_nan():
    """Test handling of NaN values."""
    x = pd.Series([1.0, 2.0, np.nan, 4.0, 5.0])
    y = pd.Series([2.0, 4.0, 6.0, 8.0, 10.0])
    
    result = calculate_spearman_correlation(x, y, seed=42, iterations=100)
    
    # Should ignore NaN and calculate on remaining
    assert result['r'] is not None
    assert result['r'] > 0.9

def test_run_correlation_analysis_stratified():
    """Test stratified analysis logic."""
    df = pd.DataFrame({
        'density': [1, 2, 3, 4, 5, 6, 7, 8],
        'tau_e': [10, 20, 30, 40, 12, 22, 32, 42],
        'confinement_mode': ['L-mode', 'L-mode', 'L-mode', 'L-mode', 'H-mode', 'H-mode', 'H-mode', 'H-mode']
    })
    
    results = run_correlation_analysis(df, 'density', 'tau_e', 'confinement_mode')
    
    assert 'results' in results
    assert 'L-mode' in results['results']
    assert 'H-mode' in results['results']

def test_run_correlation_analysis_insufficient_stratification():
    """Test global correlation when stratification is not possible."""
    df = pd.DataFrame({
        'density': [1, 2, 3],
        'tau_e': [10, 20, 30],
        'confinement_mode': ['L-mode', 'L-mode', 'H-mode']  # H-mode has N=1
    })
    
    results = run_correlation_analysis(df, 'density', 'tau_e', 'confinement_mode')
    
    assert 'warning' in str(results.get('warning_flags', [])) or 'global' in results.get('results', {})
    # Should fall back to global or warn

def test_multicollinearity_check():
    """Test multicollinearity detection."""
    df = pd.DataFrame({
        'A': [1, 2, 3, 4, 5],
        'B': [2, 4, 6, 8, 10]  # Perfectly correlated
    })
    
    is_collinear, corr = check_multicollinearity(df, 'A', 'B')
    
    assert is_collinear is True
    assert corr > 0.99
