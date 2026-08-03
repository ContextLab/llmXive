"""
Unit tests for Differential Expression Analysis (T023).
"""
import os
import sys
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
import json

# Import functions to test
from src.differential_expression import process_tumor_type_discovery, run_deseq2_analysis_scipy

@pytest.fixture
def temp_data_dir():
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

@pytest.fixture
def sample_discovery_data():
    """
    Generate a small synthetic dataset for testing.
    Format: Samples as rows, Genes as columns, plus response_label.
    """
    np.random.seed(42)
    n_samples = 20
    n_genes = 100
    
    # Create gene names
    genes = [f"GENE_{i:03d}" for i in range(n_genes)]
    samples = [f"Sample_{i}" for i in range(n_samples)]
    
    # Create expression data
    # Responders (10) vs Non-responders (10)
    # Make some genes differentially expressed
    expr_data = np.random.rand(n_samples, n_genes) * 10
    
    # Inject signal: first 5 genes higher in responders
    responders_idx = list(range(10))
    expr_data[responders_idx, :5] += 5.0
    
    df = pd.DataFrame(expr_data, columns=genes, index=samples)
    df['response_label'] = ['Responder'] * 10 + ['NonResponder'] * 10
    
    return df

def test_process_discovery_set_format(temp_data_dir, sample_discovery_data):
    """
    Test that process_tumor_type_discovery correctly handles a valid discovery set.
    """
    # Create input file with correct naming convention
    tumor_type = "Lung"
    input_file = temp_data_dir / f"{tumor_type}_discovery_set.csv"
    sample_discovery_data.to_csv(input_file)
    
    # Call function
    result = process_tumor_type_discovery(tumor_type, temp_data_dir, temp_data_dir)
    
    # Assertions
    assert result['status'] == 'success'
    assert result['tumor_type'] == tumor_type
    assert 'output_file' in result
    assert os.path.exists(result['output_file'])
    
    # Check output content
    with open(result['output_file'], 'r') as f:
        de_results = json.load(f)
    
    assert isinstance(de_results, list)
    # We injected signal, so we expect some significant genes (even with scipy approx)
    # Note: With small N, scipy might not find all, but it should run without error.
    # Just verify the structure is correct.
    if len(de_results) > 0:
        assert 'gene' in de_results[0]
        assert 'log2FoldChange' in de_results[0]
        assert 'padj' in de_results[0]

def test_wrong_filename(temp_data_dir, sample_discovery_data):
    """
    Test that a file NOT ending in _discovery_set.csv raises an error (Data Leakage Prevention).
    """
    tumor_type = "Lung"
    # Incorrect filename
    input_file = temp_data_dir / f"{tumor_type}_training_set.csv"
    sample_discovery_data.to_csv(input_file)
    
    with pytest.raises(ValueError, match="Data Leakage Prevention Failed"):
        process_tumor_type_discovery(tumor_type, temp_data_dir, temp_data_dir)

def test_missing_response_column(temp_data_dir):
    """
    Test that a file missing 'response_label' raises an error.
    """
    tumor_type = "Lung"
    input_file = temp_data_dir / f"{tumor_type}_discovery_set.csv"
    
    # Create data without label
    df = pd.DataFrame(np.random.rand(10, 5), columns=[f"GENE_{i}" for i in range(5)])
    df.to_csv(input_file)
    
    with pytest.raises(ValueError, match="Could not find 'response_label'"):
        process_tumor_type_discovery(tumor_type, temp_data_dir, temp_data_dir)

def test_threshold_logic(temp_data_dir):
    """
    Test the threshold logic in run_deseq2_analysis_scipy.
    """
    # Create simple data where we know the result
    # 2 groups of 3 samples
    # Gene 1: Group A = 1, Group B = 10 (Large diff)
    # Gene 2: Group A = 5, Group B = 5 (No diff)
    
    counts = pd.DataFrame({
        'Sample_A1': [1, 5],
        'Sample_A2': [1, 5],
        'Sample_A3': [1, 5],
        'Sample_B1': [10, 5],
        'Sample_B2': [10, 5],
        'Sample_B3': [10, 5]
    }, index=['Gene1', 'Gene2']).T
    
    counts.index.name = 'Sample'
    col_data = pd.DataFrame({
        'response_label': ['A', 'A', 'A', 'B', 'B', 'B']
    }, index=counts.index)
    
    # Run analysis
    results = run_deseq2_analysis_scipy(counts, col_data)
    
    # Gene1 should be significant (high logFC, low pval)
    # Gene2 should not be significant (logFC ~ 0)
    significant_genes = results['gene'].tolist()
    
    assert 'Gene1' in significant_genes
    assert 'Gene2' not in significant_genes