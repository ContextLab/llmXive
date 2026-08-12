"""
Unit tests for correlation analysis module.
"""

import os
import pytest
import numpy as np
import pandas as pd
from pathlib import Path
from unittest.mock import patch, MagicMock
import tempfile
import shutil

from src.analysis.correlation import (
    CorrelationResult,
    CorrelationAnalysisResult,
    load_tree,
    load_merged_dataset,
    compute_phylogenetic_covariance,
    pgls_correlation,
    permutation_fdr,
    run_pgl_analysis,
    write_results
)

@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    temp = tempfile.mkdtemp()
    yield temp
    shutil.rmtree(temp)

@pytest.fixture
def sample_tree(temp_dir):
    """Create a sample Newick tree file."""
    tree_path = os.path.join(temp_dir, "test_tree.newick")
    newick_str = "((A:1.0,B:1.0):1.0,(C:1.0,D:1.0):1.0);"
    with open(tree_path, 'w') as f:
        f.write(newick_str)
    return tree_path

@pytest.fixture
def sample_dataset(temp_dir):
    """Create a sample merged dataset."""
    df = pd.DataFrame({
        'isolate_id': ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J'],
        'species': ['sp1', 'sp1', 'sp1', 'sp2', 'sp2', 'sp2', 'sp3', 'sp3', 'sp3', 'sp3'],
        'phenotype_score': [0.8, 0.7, 0.9, 0.3, 0.2, 0.4, 0.6, 0.5, 0.7, 0.6],
        'feature_1': [1, 1, 0, 0, 0, 1, 1, 0, 1, 0],
        'feature_2': [0.5, 0.6, 0.4, 0.2, 0.1, 0.3, 0.5, 0.4, 0.6, 0.5],
        'feature_3': [1, 0, 1, 0, 1, 0, 1, 0, 1, 0]
    })
    dataset_path = os.path.join(temp_dir, "merged_dataset.parquet")
    df.to_parquet(dataset_path)
    return dataset_path

def test_load_tree_success(sample_tree):
    """Test successful tree loading."""
    tree = load_tree(sample_tree)
    assert tree is not None
    assert "A" in tree or "B" in tree  # Check that tree contains expected taxa

def test_load_tree_missing_file():
    """Test loading a non-existent tree file."""
    with pytest.raises(FileNotFoundError):
        load_tree("non_existent_file.newick")

def test_load_merged_dataset_success(sample_dataset):
    """Test successful dataset loading."""
    df = load_merged_dataset(sample_dataset)
    assert len(df) == 10
    assert 'isolate_id' in df.columns
    assert 'phenotype_score' in df.columns

def test_load_merged_dataset_missing_file():
    """Test loading a non-existent dataset file."""
    with pytest.raises(FileNotFoundError):
        load_merged_dataset("non_existent_file.parquet")

def test_compute_phylogenetic_covariance(sample_tree):
    """Test phylogenetic covariance matrix computation."""
    taxa = ['A', 'B', 'C', 'D']
    cov_matrix = compute_phylogenetic_covariance(sample_tree, taxa)
    assert cov_matrix.shape == (4, 4)
    assert np.allclose(cov_matrix, np.eye(4))  # Placeholder implementation

def test_pgls_correlation_basic():
    """Test basic PGLS correlation computation."""
    y = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
    X = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
    phylo_cov = np.eye(5)  # Identity matrix (no phylogeny)
    
    coeff, se, t_stat, p_val = pgls_correlation(y, X, phylo_cov)
    
    assert coeff > 0  # Positive correlation
    assert se > 0
    assert t_stat > 0
    assert 0 <= p_val <= 1

def test_pgls_correlation_insufficient_data():
    """Test PGLS with insufficient data points."""
    y = np.array([1.0, 2.0])
    X = np.array([1.0, 2.0])
    phylo_cov = np.eye(2)
    
    with pytest.raises(ValueError, match="Need at least 3 observations"):
        pgls_correlation(y, X, phylo_cov)

def test_permutation_fdr_basic():
    """Test basic permutation FDR computation."""
    p_values = np.array([0.01, 0.05, 0.1, 0.2, 0.3])
    adj_p_values = permutation_fdr(p_values, n_permutations=100)
    
    assert len(adj_p_values) == len(p_values)
    assert all(0 <= p <= 1 for p in adj_p_values)
    # Check monotonicity
    sorted_adj = np.sort(adj_p_values)
    assert np.all(np.diff(sorted_adj) >= 0)

def test_permutation_fdr_empty():
    """Test permutation FDR with empty input."""
    p_values = np.array([])
    adj_p_values = permutation_fdr(p_values, n_permutations=100)
    assert len(adj_p_values) == 0

@patch('src.analysis.correlation.load_tree')
@patch('src.analysis.correlation.compute_phylogenetic_covariance')
@patch('src.analysis.correlation.pgls_correlation')
def test_run_pgl_analysis(mock_pgls, mock_compute_cov, mock_load_tree, 
                         sample_dataset, sample_tree, temp_dir):
    """Test full PGLS analysis pipeline."""
    # Mock dependencies
    mock_load_tree.return_value = "((A:1.0,B:1.0):1.0,(C:1.0,D:1.0):1.0);"
    mock_compute_cov.return_value = np.eye(10)
    mock_pgls.side_effect = [
        (0.5, 0.1, 5.0, 0.001),  # feature_1
        (0.3, 0.1, 3.0, 0.01),   # feature_2
        (-0.2, 0.1, -2.0, 0.05)  # feature_3
    ]
    
    results = run_pgl_analysis(
        load_merged_dataset(sample_dataset),
        sample_tree,
        n_permutations=100
    )
    
    assert len(results.results) == 3
    assert results.metadata['n_features_analyzed'] == 3
    assert results.metadata['n_observations'] == 10

def test_write_results(temp_dir, sample_dataset, sample_tree):
    """Test writing results to CSV."""
    # Run analysis
    results = run_pgl_analysis(
        load_merged_dataset(sample_dataset),
        sample_tree,
        n_permutations=100
    )
    
    # Write results
    output_path = os.path.join(temp_dir, "test_results.csv")
    write_results(results, output_path)
    
    # Verify file exists and can be read
    assert os.path.exists(output_path)
    df = pd.read_csv(output_path)
    assert len(df) == len(results.results)
    assert 'feature_id' in df.columns
    assert 'coefficient' in df.columns
    assert 'p_value' in df.columns
    assert 'adj_p_value' in df.columns