"""
Unit tests for collinearity diagnostics in code/diagnostics.py.
"""
import os
import json
import tempfile
from pathlib import Path

import pandas as pd
import numpy as np

# Import the module under test
from code.diagnostics import calculate_vif, calculate_correlation, run_collinearity_diagnostics


def test_calculate_vif_no_collinearity():
    """Test VIF calculation with uncorrelated features."""
    np.random.seed(42)
    n = 100
    df = pd.DataFrame({
        'A': np.random.randn(n),
        'B': np.random.randn(n),
        'C': np.random.randn(n),
        'D': np.random.randn(n)
    })
    
    vif_results = calculate_vif(df, ['A', 'B', 'C', 'D'])
    
    # With uncorrelated features, VIF should be close to 1
    for name, vif in vif_results.items():
        assert 0.9 < vif < 1.5, f"VIF for {name} should be near 1, got {vif}"


def test_calculate_vif_high_collinearity():
    """Test VIF calculation with highly correlated features."""
    np.random.seed(42)
    n = 100
    x = np.random.randn(n)
    df = pd.DataFrame({
        'A': x,
        'B': x * 2 + np.random.randn(n) * 0.1,  # Highly correlated with A
        'C': np.random.randn(n),
        'D': np.random.randn(n)
    })
    
    vif_results = calculate_vif(df, ['A', 'B', 'C', 'D'])
    
    # A and B should have high VIF (> 5) due to multicollinearity
    assert vif_results['A'] > 5, f"VIF for A should be > 5, got {vif_results['A']}"
    assert vif_results['B'] > 5, f"VIF for B should be > 5, got {vif_results['B']}"


def test_calculate_correlation():
    """Test Pearson correlation calculation."""
    np.random.seed(42)
    n = 100
    x = np.random.randn(n)
    y = x * 2 + np.random.randn(n) * 0.1  # Strong positive correlation
    
    df = pd.DataFrame({'X': x, 'Y': y})
    
    corr = calculate_correlation(df, 'X', 'Y')
    
    assert 0.8 < corr < 1.0, f"Correlation should be high positive, got {corr}"


def test_run_collinearity_diagnostics():
    """Test the full diagnostics pipeline."""
    # Create a temporary directory for test files
    with tempfile.TemporaryDirectory() as tmpdir:
        input_path = os.path.join(tmpdir, 'cleaned_data.csv')
        output_path = os.path.join(tmpdir, 'diagnostics.json')
        
        # Create synthetic data with known properties
        np.random.seed(42)
        n = 50
        gs_sd = np.random.randn(n) * 0.5 + 1.0
        fd = gs_sd * 0.3 + np.random.randn(n) * 0.1  # Moderate correlation
        dvars = np.random.randn(n) * 0.2 + 0.5
        age = np.random.randint(20, 50, n)
        sex = np.random.choice([0, 1], n)
        
        df = pd.DataFrame({
            'Subject_ID': [f'sub-{i:03d}' for i in range(n)],
            'Global_Signal_SD': gs_sd,
            'Mean_FD': fd,
            'Mean_DVARS': dvars,
            'Age': age,
            'Sex': sex
        })
        
        df.to_csv(input_path, index=False)
        
        # Run diagnostics
        results = run_collinearity_diagnostics(input_path, output_path)
        
        # Verify output file exists
        assert os.path.exists(output_path), "Output JSON file was not created"
        
        # Verify results structure
        assert 'vif' in results
        assert 'gs_fd_correlation' in results
        assert 'n_subjects' in results
        assert results['n_subjects'] == n
        
        # Verify VIF values are present for all predictors
        expected_predictors = ['Global_Signal_SD', 'Mean_FD', 'Mean_DVARS', 'Age', 'Sex']
        for pred in expected_predictors:
            assert pred in results['vif'], f"VIF missing for {pred}"
            assert isinstance(results['vif'][pred], (int, float)), f"VIF for {pred} is not numeric"
        
        # Verify correlation is a valid number
        assert isinstance(results['gs_fd_correlation'], float)
        assert -1.0 <= results['gs_fd_correlation'] <= 1.0


def test_run_collinearity_diagnostics_high_vif():
    """Test diagnostics with intentionally high collinearity."""
    with tempfile.TemporaryDirectory() as tmpdir:
        input_path = os.path.join(tmpdir, 'cleaned_data.csv')
        output_path = os.path.join(tmpdir, 'diagnostics.json')
        
        # Create data with high collinearity between Global_Signal_SD and Mean_FD
        np.random.seed(42)
        n = 50
        base = np.random.randn(n)
        
        df = pd.DataFrame({
            'Subject_ID': [f'sub-{i:03d}' for i in range(n)],
            'Global_Signal_SD': base * 2 + np.random.randn(n) * 0.1,
            'Mean_FD': base * 2.1 + np.random.randn(n) * 0.1,  # Highly correlated
            'Mean_DVARS': np.random.randn(n) * 0.2 + 0.5,
            'Age': np.random.randint(20, 50, n),
            'Sex': np.random.choice([0, 1], n)
        })
        
        df.to_csv(input_path, index=False)
        
        results = run_collinearity_diagnostics(input_path, output_path)
        
        # Should detect high VIF
        assert len(results['high_vif_features']) > 0, "Should detect high VIF features"
        assert results['status'] == 'warning', "Status should be warning when high VIF detected"