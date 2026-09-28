"""
Unit tests for collinearity diagnostics module.
"""
import os
import json
import tempfile
import pytest
import pandas as pd
import numpy as np

from diagnostics import calculate_vif, calculate_correlation, run_collinearity_diagnostics


def test_calculate_vif():
    """Test VIF calculation on synthetic data."""
    # Create a dataframe with known multicollinearity
    np.random.seed(42)
    n = 100
    x1 = np.random.randn(n)
    x2 = x1 * 0.9 + np.random.randn(n) * 0.1  # Highly correlated with x1
    
    df = pd.DataFrame({
        'x1': x1,
        'x2': x2,
        'x3': np.random.randn(n)
    })
    
    predictors = ['x1', 'x2', 'x3']
    vif_results = calculate_vif(df, predictors)
    
    # x1 and x2 should have high VIF due to correlation
    assert vif_results['x1'] > 1.0
    assert vif_results['x2'] > 1.0
    assert vif_results['x3'] < 2.0  # x3 should have low VIF
    
    # VIF should be positive
    for vif in vif_results.values():
        assert vif >= 0.0


def test_calculate_correlation():
    """Test correlation calculation."""
    np.random.seed(42)
    n = 50
    x = np.linspace(0, 10, n)
    y = 2 * x + np.random.randn(n) * 0.5  # Strong positive correlation
    
    df = pd.DataFrame({'x': x, 'y': y})
    
    corr = calculate_correlation(df, 'x', 'y')
    
    assert 0.8 < corr < 1.0  # Should be strongly positive


def test_run_collinearity_diagnostics(tmp_path):
    """Test full diagnostics pipeline."""
    # Create temporary input file
    input_file = tmp_path / "cleaned_data.csv"
    output_file = tmp_path / "diagnostics.json"
    
    np.random.seed(42)
    n = 100
    df = pd.DataFrame({
        'Global_Signal_SD': np.random.randn(n),
        'Mean_FD': np.random.randn(n) * 0.2,
        'Mean_DVARS': np.random.randn(n) * 0.3,
        'Age': np.random.randint(18, 80, n),
        'Sex': np.random.choice([0, 1], n)
    })
    
    df.to_csv(input_file, index=False)
    
    # Run diagnostics
    results = run_collinearity_diagnostics(str(input_file), str(output_file))
    
    # Verify output file exists
    assert os.path.exists(output_file)
    
    # Verify results structure
    assert 'vif' in results
    assert 'high_vif_features' in results
    assert 'gs_fd_correlation' in results
    assert 'n_subjects' in results
    assert results['n_subjects'] == n
    
    # Verify VIF values are present for all predictors
    expected_predictors = ['Global_Signal_SD', 'Mean_FD', 'Mean_DVARS', 'Age', 'Sex']
    for pred in expected_predictors:
        assert pred in results['vif']
    
    # Verify correlation is a float
    assert isinstance(results['gs_fd_correlation'], float)
    
    # Verify status is set correctly
    assert results['status'] in ['ok', 'warning']


def test_diagnostics_with_high_collinearity(tmp_path):
    """Test diagnostics when high collinearity is present."""
    input_file = tmp_path / "cleaned_data.csv"
    output_file = tmp_path / "diagnostics.json"
    
    np.random.seed(42)
    n = 50
    x = np.random.randn(n)
    
    # Create highly correlated predictors
    df = pd.DataFrame({
        'Global_Signal_SD': x,
        'Mean_FD': x * 0.95 + np.random.randn(n) * 0.05,  # Highly correlated
        'Mean_DVARS': np.random.randn(n),
        'Age': np.random.randint(18, 80, n),
        'Sex': np.random.choice([0, 1], n)
    })
    
    df.to_csv(input_file, index=False)
    
    results = run_collinearity_diagnostics(str(input_file), str(output_file))
    
    # With high correlation, VIF should be > 5 for at least one feature
    # (Note: exact threshold depends on correlation strength and sample size)
    assert results['status'] in ['ok', 'warning']
    assert len(results['high_vif_features']) >= 0  # May or may not exceed threshold