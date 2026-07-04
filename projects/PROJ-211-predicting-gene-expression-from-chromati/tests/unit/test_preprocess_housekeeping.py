"""
Unit tests for housekeeping gene definition functionality.
"""
import pytest
import pandas as pd
import numpy as np
import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from preprocess import (
    calculate_coefficient_of_variation,
    define_housekeeping_genes
)

def test_calculate_cv_all_zero():
    """Test CV calculation when all values are zero."""
    df = pd.DataFrame({
        'gene_id': ['gene1', 'gene2'],
        'cell1': [0, 0],
        'cell2': [0, 0],
        'cell3': [0, 0]
    })
    cv_df = calculate_coefficient_of_variation(df, 'gene_id')
    # When mean is 0, CV should be inf
    assert cv_df['cv'].iloc[0] == np.inf
    assert cv_df['cv'].iloc[1] == np.inf

def test_calculate_cv_normal():
    """Test CV calculation with normal data."""
    df = pd.DataFrame({
        'gene_id': ['gene1', 'gene2'],
        'cell1': [10, 100],
        'cell2': [12, 110],
        'cell3': [11, 105]
    })
    cv_df = calculate_coefficient_of_variation(df, 'gene_id')
    
    # gene1: mean=11, std=1, CV=1/11=0.0909
    # gene2: mean=105, std=5, CV=5/105=0.0476
    expected_cv1 = 1 / 11
    expected_cv2 = 5 / 105
    
    assert abs(cv_df['cv'].iloc[0] - expected_cv1) < 1e-6
    assert abs(cv_df['cv'].iloc[1] - expected_cv2) < 1e-6

def test_define_housekeeping_genes_basic():
    """Test basic housekeeping gene definition."""
    # Create data with known CVs
    np.random.seed(42)
    n_genes = 10
    n_cells = 5
    
    data = {'gene_id': [f'gene{i}' for i in range(n_genes)]}
    for i in range(n_cells):
        # Gene 0-4: low variance (CV < 0.2)
        # Gene 5-9: high variance (CV > 0.2)
        if i < 5:
            data[f'cell{i}'] = np.random.normal(100, 5, n_genes)
        else:
            data[f'cell{i}'] = np.random.normal(100, 20, n_genes)
    
    df = pd.DataFrame(data)
    
    # Test with threshold 0.2, should select genes 0-4
    housekeeping = define_housekeeping_genes(df, n_genes=5, cv_threshold=0.2, gene_col='gene_id')
    
    assert len(housekeeping) <= 5
    assert all(housekeeping['gene_id'].isin([f'gene{i}' for i in range(5)]))

def test_define_housekeeping_genes_limit():
    """Test that housekeeping gene selection respects n_genes limit."""
    np.random.seed(42)
    n_genes = 20
    n_cells = 5
    
    # All genes have low CV
    data = {'gene_id': [f'gene{i}' for i in range(n_genes)]}
    for i in range(n_cells):
        data[f'cell{i}'] = np.random.normal(100, 5, n_genes)
    
    df = pd.DataFrame(data)
    
    # Request only 5 genes, even though all qualify
    housekeeping = define_housekeeping_genes(df, n_genes=5, cv_threshold=0.5, gene_col='gene_id')
    
    assert len(housekeeping) == 5

def test_define_housekeeping_genes_empty():
    """Test when no genes meet the CV threshold."""
    np.random.seed(42)
    n_genes = 10
    n_cells = 5
    
    # All genes have high CV
    data = {'gene_id': [f'gene{i}' for i in range(n_genes)]}
    for i in range(n_cells):
        data[f'cell{i}'] = np.random.normal(100, 50, n_genes)
    
    df = pd.DataFrame(data)
    
    # With very strict threshold, no genes should qualify
    housekeeping = define_housekeeping_genes(df, n_genes=5, cv_threshold=0.01, gene_col='gene_id')
    
    assert len(housekeeping) == 0

if __name__ == "__main__":
    pytest.main([__file__, "-v"])