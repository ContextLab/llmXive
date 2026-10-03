import pytest
import pandas as pd
import numpy as np
import os
import tempfile
from pathlib import Path

# Import the function to test
from analysis import apply_bh_correction, calculate_partial_spearman

def test_apply_bh_correction():
    """Test that Benjamini-Hochberg correction is applied correctly."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create mock input file
        input_path = os.path.join(tmpdir, 'test_pvals.csv')
        df = pd.DataFrame({
            'feature': ['f1', 'f2', 'f3', 'f4'],
            'pval_raw': [0.01, 0.05, 0.10, 0.20]
        })
        df.to_csv(input_path, index=False)
        
        output_path = os.path.join(tmpdir, 'adjusted_pvals.csv')
        apply_bh_correction([input_path], output_path)
        
        # Verify output exists
        assert os.path.exists(output_path)
        result_df = pd.read_csv(output_path)
        
        # Check columns
        assert 'feature' in result_df.columns
        assert 'pval_raw' in result_df.columns
        assert 'pval_adj' in result_df.columns
        
        # Check that adjusted p-values are monotonically increasing with raw p-values
        # (BH property)
        sorted_df = result_df.sort_values('pval_raw')
        assert all(sorted_df['pval_adj'].diff().fillna(0) >= -1e-10), "Adjusted p-values should be non-decreasing"
        
        # Check that adjusted p-values are >= raw p-values
        assert all(result_df['pval_adj'] >= result_df['pval_raw']), "Adjusted p-values should be >= raw p-values"

def test_partial_spearman_with_covariates():
    """Test partial Spearman correlation with covariates."""
    x = np.random.randn(100)
    y = np.random.randn(100)
    covariates_df = pd.DataFrame({
        'age': np.random.randn(100),
        'bmi': np.random.randn(100)
    })
    
    corr, pval = calculate_partial_spearman(x, y, covariates_df, ['age', 'bmi'])
    
    assert isinstance(corr, float)
    assert 0 <= pval <= 1
    assert -1 <= corr <= 1

def test_partial_spearman_without_covariates():
    """Test partial Spearman correlation falls back to standard Spearman."""
    x = np.random.randn(100)
    y = np.random.randn(100)
    covariates_df = pd.DataFrame({})
    
    corr, pval = calculate_partial_spearman(x, y, covariates_df, [])
    
    assert isinstance(corr, float)
    assert 0 <= pval <= 1