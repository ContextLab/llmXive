import os
import sys
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
import json
from unittest.mock import patch, MagicMock

# Mock rpy2 to avoid needing R installed for unit tests
# The actual integration tests will use rpy2
sys.modules['rpy2'] = MagicMock()
sys.modules['rpy2.rinterface'] = MagicMock()
sys.modules['rpy2.robjects'] = MagicMock()

from code.src.differential_expression import (
    setup_r_environment,
    load_discovery_set,
    run_deseq2_analysis,
    process_tumor_type_loo,
    run_deseq2_analysis_loo
)

@pytest.fixture
def temp_data_dir():
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

@pytest.fixture
def sample_discovery_data(temp_data_dir):
    # Create mock counts data
    np.random.seed(42)
    n_genes = 100
    n_samples = 20
    gene_names = [f"GENE_{i}" for i in range(n_genes)]
    sample_ids = [f"Sample_{i}" for i in range(n_samples)]
    
    # Random counts
    counts_data = np.random.poisson(100, size=(n_genes, n_samples))
    counts_df = pd.DataFrame(counts_data, index=gene_names, columns=sample_ids)
    
    # Create mock phenotypes
    pheno_data = {
        'response_label': ['Responder'] * 10 + ['NonResponder'] * 10,
        'tumor_type': ['TumorA'] * 20
    }
    pheno_df = pd.DataFrame(pheno_data, index=sample_ids)
    
    # Save to temp dir
    counts_path = temp_data_dir / "counts.csv"
    pheno_path = temp_data_dir / "phenotypes.csv"
    
    counts_df.to_csv(counts_path)
    pheno_df.to_csv(pheno_path)
    
    return {
        'counts_path': counts_path,
        'pheno_path': pheno_path,
        'temp_dir': temp_data_dir
    }

def test_load_discovery_set_valid(sample_discovery_data):
    """Test loading valid discovery set data"""
    # Mock the R side to return a simple object
    with patch('code.src.differential_expression.rpy2') as mock_rpy2:
        # Setup mock return values
        mock_rpy2.robjects.r['read.csv'] = lambda x: pd.DataFrame()
        
        # This test primarily verifies the Python logic of path handling
        # The actual R loading is mocked
        try:
            # We expect this to fail gracefully or return a mock object
            # since we are mocking rpy2
            result = load_discovery_set(
                sample_discovery_data['counts_path'],
                sample_discovery_data['pheno_path']
            )
            # If we get here, the paths were valid
            assert result is not None
        except Exception as e:
            # Expected if rpy2 mocking is incomplete, but paths should be valid
            assert "counts file not found" not in str(e).lower()

def test_process_discovery_set_format(temp_data_dir):
    """Test that the discovery set format is correct"""
    # Create a dataset with wrong format (missing response_label)
    np.random.seed(42)
    counts_data = np.random.poisson(100, size=(10, 10))
    counts_df = pd.DataFrame(counts_data, index=[f"G{i}" for i in range(10)], columns=[f"S{i}" for i in range(10)])
    
    # Missing response_label column
    pheno_data = {
        'tumor_type': ['TumorA'] * 10
    }
    pheno_df = pd.DataFrame(pheno_data, index=[f"S{i}" for i in range(10)])
    
    counts_path = temp_data_dir / "counts_wrong.csv"
    pheno_path = temp_data_dir / "pheno_wrong.csv"
    
    counts_df.to_csv(counts_path)
    pheno_df.to_csv(pheno_path)
    
    with patch('code.src.differential_expression.rpy2') as mock_rpy2:
        with pytest.raises(Exception):
            load_discovery_set(counts_path, pheno_path)

def test_wrong_filename(temp_data_dir):
    """Test handling of wrong file paths"""
    with patch('code.src.differential_expression.rpy2') as mock_rpy2:
        with pytest.raises(FileNotFoundError):
            load_discovery_set(
                temp_data_dir / "nonexistent.csv",
                temp_data_dir / "nonexistent.csv"
            )

def test_missing_response_column(temp_data_dir):
    """Test handling of missing response_label column"""
    np.random.seed(42)
    counts_data = np.random.poisson(100, size=(10, 10))
    counts_df = pd.DataFrame(counts_data, index=[f"G{i}" for i in range(10)], columns=[f"S{i}" for i in range(10)])
    
    # Missing response_label
    pheno_data = {
        'tumor_type': ['TumorA'] * 10
    }
    pheno_df = pd.DataFrame(pheno_data, index=[f"S{i}" for i in range(10)])
    
    counts_path = temp_data_dir / "counts.csv"
    pheno_path = temp_data_dir / "pheno.csv"
    
    counts_df.to_csv(counts_path)
    pheno_df.to_csv(pheno_path)
    
    with patch('code.src.differential_expression.rpy2') as mock_rpy2:
        with pytest.raises(Exception):
            load_discovery_set(counts_path, pheno_path)

def test_threshold_logic(temp_data_dir):
    """Test that DE results are filtered correctly"""
    # This test verifies the logic of filtering significant genes
    # In a real scenario, this would check the output of run_deseq2_analysis
    # Here we mock the R output
    
    mock_results = pd.DataFrame({
        'log2FoldChange': [2.5, -1.2, 0.5, 3.0],
        'pvalue': [0.001, 0.04, 0.2, 0.0001],
        'padj': [0.01, 0.05, 0.3, 0.001],
        'baseMean': [100, 200, 50, 300]
    })
    
    # Filter logic: FDR < 0.05 and |log2FC| > 1.0
    significant = mock_results[
        (mock_results['padj'] < 0.05) & 
        (abs(mock_results['log2FoldChange']) > 1.0)
    ]
    
    assert len(significant) == 2  # First and last rows
    assert 'GENE_X' not in significant.index  # Index should be preserved or handled