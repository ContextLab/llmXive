"""
Unit tests for preprocessing functions.
"""

import os
import sys
import tempfile
import pandas as pd
import numpy as np

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))

from preprocess import filter_genes_zero_expression, apply_log_pseudocount


def test_filter_genes_zero_expression():
    """Test that genes with all zeros are filtered out."""
    # Create test data
    data = {
        'gene_id': ['gene1', 'gene2', 'gene3', 'gene4'],
        'sample1': [0, 5, 0, 10],
        'sample2': [0, 3, 0, 0],
        'sample3': [0, 0, 0, 5]
    }
    df = pd.DataFrame(data)
    df = df.set_index('gene_id')

    # Filter
    result = filter_genes_zero_expression(df)

    # gene1 and gene3 should be removed (all zeros)
    # gene2 and gene4 should remain
    assert len(result) == 2
    assert 'gene2' in result.index
    assert 'gene4' in result.index
    assert 'gene1' not in result.index
    assert 'gene3' not in result.index

    print("✓ test_filter_genes_zero_expression passed")


def test_apply_log_pseudocount():
    """Test log transformation with pseudocount."""
    # Create test data
    data = {
        'gene_id': ['gene1', 'gene2'],
        'sample1': [0, 1],
        'sample2': [0, 10],
        'sample3': [1, 100]
    }
    df = pd.DataFrame(data)
    df = df.set_index('gene_id')

    # Apply transformation with pseudocount=1
    result = apply_log_pseudocount(df, pseudocount=1.0)

    # Check that log(0+1) = 0
    assert result.loc['gene1', 'sample1'] == np.log(1)  # Should be 0
    # Check that log(1+1) = log(2)
    assert result.loc['gene1', 'sample3'] == np.log(2)
    # Check that log(100+1) ≈ log(101)
    assert np.isclose(result.loc['gene2', 'sample3'], np.log(101))

    print("✓ test_apply_log_pseudocount passed")


def test_filter_and_transform_pipeline():
    """Test the combined filter and transform pipeline."""
    # Create test data with some genes having all zeros
    data = {
        'gene_id': ['gene1', 'gene2', 'gene3'],
        'sample1': [0, 5, 0],
        'sample2': [0, 3, 0],
        'sample3': [0, 0, 0]  # gene3 has all zeros
    }
    df = pd.DataFrame(data)
    df = df.set_index('gene_id')

    # Filter
    filtered = filter_genes_zero_expression(df)
    assert len(filtered) == 1  # Only gene2 should remain
    assert 'gene2' in filtered.index

    # Transform
    transformed = apply_log_pseudocount(filtered, pseudocount=1.0)
    assert transformed.loc['gene2', 'sample1'] == np.log(6)  # log(5+1)
    assert transformed.loc['gene2', 'sample2'] == np.log(4)  # log(3+1)

    print("✓ test_filter_and_transform_pipeline passed")


if __name__ == '__main__':
    test_filter_genes_zero_expression()
    test_apply_log_pseudocount()
    test_filter_and_transform_pipeline()
    print("\nAll tests passed!")