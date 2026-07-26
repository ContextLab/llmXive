"""
Unit tests for Differential Expression module.
Tests the logic of filtering and data preparation without running DESeq2 (mocked).
"""

import os
import sys
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile

# Mock rpy2 to avoid R dependency in unit tests
from unittest.mock import patch, MagicMock

# Import the function to test (we will test the logic inside process_tumor_type_discovery)
# Since rpy2 is heavy, we mock the run_deseq2_analysis function
from src.differential_expression import process_tumor_type_discovery

@pytest.fixture
def sample_discovery_data():
    """Generate a sample discovery set (Samples x Genes format)."""
    n_samples = 50
    n_genes = 100
    n_responders = 20
    
    # Create metadata
    responses = ['Responder'] * n_responders + ['NonResponder'] * (n_samples - n_responders)
    np.random.shuffle(responses)
    
    # Create random counts (integers)
    data = np.random.randint(10, 1000, size=(n_samples, n_genes))
    
    # Create DataFrame
    gene_names = [f"GENE_{i}" for i in range(n_genes)]
    df = pd.DataFrame(data, columns=gene_names)
    df['response'] = responses
    
    return df

@pytest.fixture
def temp_data_dir(sample_discovery_data):
    """Create a temporary directory with a sample discovery file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        data_dir = Path(tmpdir)
        tumor_type = "TEST_TY"
        file_path = data_dir / f"{tumor_type}_discovery_set.csv"
        sample_discovery_data.to_csv(file_path, index=False)
        yield data_dir, tumor_type

def test_process_discovery_set_format(temp_data_dir):
    """Test that the function correctly identifies Samples x Genes format."""
    data_dir, tumor_type = temp_data_dir
    results_dir = Path(temp_data_dir[0].parent) / "results"
    results_dir.mkdir(exist_ok=True)
    
    # Mock the run_deseq2_analysis to avoid R call
    with patch('src.differential_expression.run_deseq2_analysis') as mock_de:
        # Create a mock result DataFrame
        mock_result = pd.DataFrame({
            'gene': ['GENE_0', 'GENE_1'],
            'base_mean': [100.0, 200.0],
            'log2_fold_change': [2.5, -1.5],
            'pvalue': [0.01, 0.001],
            'padj': [0.02, 0.005],
            'significant': [True, True]
        })
        mock_de.return_value = mock_result
        
        result = process_tumor_type_discovery(tumor_type, data_dir, results_dir)
        
        assert result['status'] == 'success'
        assert result['tumor_type'] == tumor_type
        assert 'output_file' in result
        
        # Verify run_deseq2_analysis was called
        assert mock_de.called
        args, kwargs = mock_de.call_args
        # Check that counts and metadata were passed correctly
        assert 'counts_df' in kwargs
        assert 'metadata_df' in kwargs
        assert 'response' in kwargs['metadata_df'].columns

def test_threshold_logic():
    """Test the filtering logic for FDR and log2FC."""
    # This tests the logic inside run_deseq2_analysis (which we can't easily isolate without mocking R)
    # Instead, we test the pandas filtering logic directly here.
    
    df = pd.DataFrame({
        'padj': [0.01, 0.06, 0.03, 0.04],
        'log2_fold_change': [2.0, 1.5, 0.5, -2.0]
    })
    
    FDR_THRESHOLD = 0.05
    LOG2FC_THRESHOLD = 1.0
    
    mask = (
        (df['padj'] < FDR_THRESHOLD) & 
        (df['padj'].notna()) &
        (df['log2_fold_change'].abs() > LOG2FC_THRESHOLD)
    )
    
    assert mask.sum() == 2 # GENE_0 and GENE_3 should be significant
    # GENE_1: p=0.06 (fail)
    # GENE_2: p=0.03 (pass), log2FC=0.5 (fail)
    # GENE_0: p=0.01 (pass), log2FC=2.0 (pass)
    # GENE_3: p=0.04 (pass), log2FC=-2.0 (pass)

def test_missing_response_column(temp_data_dir):
    """Test handling of missing response column."""
    data_dir, _ = temp_data_dir
    # Modify the file to remove response
    file_path = data_dir / "TEST_TY_discovery_set.csv"
    df = pd.read_csv(file_path)
    df = df.drop(columns=['response'])
    df.to_csv(file_path, index=False)
    
    results_dir = Path(temp_data_dir[0].parent) / "results"
    results_dir.mkdir(exist_ok=True)
    
    result = process_tumor_type_discovery("TEST_TY", data_dir, results_dir)
    assert result['status'] == 'error'
    assert 'missing_response' in result['reason']
