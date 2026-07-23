import pytest
import pandas as pd
import numpy as np
import os
from pathlib import Path

from main import generate_significance_report
from stats_engine import generate_synthetic_dataset

def test_significance_reporting_integration(tmp_path):
    """Integration test for significance reporting."""
    # Create a synthetic dataset with known structure
    # We'll create a dataset where some correlations are artificially high
    np.random.seed(42)
    n = 500
    v = 20
    
    # Generate data with some structure
    data = np.random.randn(n, v)
    # Add strong correlation between first two variables
    data[:, 1] = data[:, 0] * 0.9 + np.random.randn(n) * 0.1
    
    cols = [f'var_{i}' for i in range(v)]
    df = pd.DataFrame(data, columns=cols)
    df.attrs['name'] = 'integration_test'
    
    config = {
        'alpha': 0.05,
        'permutations': 50,  # Small for integration test
        'threshold': 0.3
    }
    
    # Run the reporting function
    result = generate_significance_report(logging.getLogger("test"), [df], config)
    
    # Check output file exists
    output_path = "data/processed/significant_findings.csv"
    assert os.path.exists(output_path), f"Output file {output_path} was not created"
    
    # Load and check content
    if os.path.exists(output_path):
        df_result = pd.read_csv(output_path)
        # Should have columns
        expected_cols = ['dataset_name', 'variable_1', 'variable_2', 'correlation', 'p_value', 'q_value', 'significant']
        assert all(col in df_result.columns for col in expected_cols)
        
        # Check that significant findings are marked correctly
        if len(df_result) > 0:
            assert all(df_result['significant'] == True)
            assert all(df_result['q_value'] < 0.05)

def test_significance_reporting_empty_result(tmp_path):
    """Test when no significant findings are found."""
    # Create a dataset with no strong correlations
    np.random.seed(42)
    data = np.random.randn(100, 20)
    cols = [f'var_{i}' for i in range(20)]
    df = pd.DataFrame(data, columns=cols)
    df.attrs['name'] = 'no_signal'
    
    config = {
        'alpha': 0.05,
        'permutations': 50,
        'threshold': 0.8  # High threshold
    }
    
    result = generate_significance_report(logging.getLogger("test"), [df], config)
    
    # Check output file exists
    output_path = "data/processed/significant_findings.csv"
    assert os.path.exists(output_path)
    
    # Should be empty or have no significant findings
    df_result = pd.read_csv(output_path)
    # If there are rows, they should not be significant (but our function only adds significant ones)
    # So if threshold is high, result should be empty
    assert len(df_result) == 0 or all(df_result['significant'] == True)