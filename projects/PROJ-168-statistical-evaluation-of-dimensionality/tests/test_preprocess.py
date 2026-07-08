"""
Tests for preprocess.py module.
"""
import os
import sys
import tempfile
import shutil
from pathlib import Path
import numpy as np
import pandas as pd
from scipy import sparse
import pytest

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from preprocess import (
    load_count_matrix,
    filter_low_expr_genes,
    select_hvgs,
    deterministic_sample_cells,
    PreprocessingError
)

def create_test_matrix(n_genes=100, n_cells=50, density=0.1):
    """Create a random sparse count matrix for testing."""
    np.random.seed(42)
    nnz = int(n_genes * n_cells * density)
    rows = np.random.randint(0, n_genes, nnz)
    cols = np.random.randint(0, n_cells, nnz)
    data = np.random.randint(1, 10, nnz)
    matrix = sparse.csr_matrix((data, (rows, cols)), shape=(n_genes, n_cells))
    return matrix

def test_filter_low_expr_genes():
    """Test that genes expressed in <5% of cells are removed."""
    # Create matrix where first 5 genes are expressed in only 1 cell (2% of 50)
    # and the rest are expressed in 10 cells (20%)
    matrix = create_test_matrix(n_genes=20, n_cells=50, density=0.2)
    
    # Force first 5 genes to have only 1 non-zero entry
    for i in range(5):
        matrix[i, 0] = 1
        matrix[i, 1:] = 0
    
    filtered = filter_low_expr_genes(matrix, threshold_pct=5.0)
    
    # 5 genes should be removed (20% of 50 is 10 cells, 5% is 2.5 -> 3 cells? No, 5% of 50 is 2.5, ceil is 3)
    # Wait, 5% of 50 is 2.5. ceil(2.5) = 3. So genes with < 3 non-zeros are removed.
    # We set 1 non-zero for first 5. So they should be removed.
    # The rest have ~10 non-zeros (density 0.2 * 50 = 10). So they should be kept.
    expected_genes = 20 - 5
    assert filtered.shape[0] == expected_genes
    assert filtered.shape[1] == 50

def test_select_hvgs():
    """Test HVG selection logic."""
    # Create a matrix with clear variance differences
    # First 10 genes have high variance, rest have low
    matrix = create_test_matrix(n_genes=20, n_cells=50, density=0.5)
    # Increase variance for first 10 genes
    for i in range(10):
        matrix[i, :] = matrix[i, :] * 10
    
    filtered_matrix, indices = select_hvgs(matrix, target_n_genes=10)
    
    # Should select top 10
    assert filtered_matrix.shape[0] == 10
    assert len(indices) == 10

def test_deterministic_sample_cells():
    """Test deterministic cell sampling."""
    matrix = create_test_matrix(n_genes=10, n_cells=100, density=0.1)
    
    # Sample to 50 cells
    sampled = deterministic_sample_cells(matrix, max_cells=50, seed=42)
    
    assert sampled.shape[1] == 50
    assert sampled.shape[0] == 10
    
    # Determinism check
    sampled2 = deterministic_sample_cells(matrix, max_cells=50, seed=42)
    assert np.array_equal(sampled.data, sampled2.data)
    assert np.array_equal(sampled.indices, sampled2.indices)
    assert np.array_equal(sampled.indptr, sampled2.indptr)

def test_load_count_matrix_csv(tmp_path):
    """Test loading a CSV count matrix."""
    df = pd.DataFrame(np.random.randint(0, 10, (10, 20)))
    csv_path = tmp_path / "test.csv"
    df.to_csv(csv_path)
    
    matrix = load_count_matrix(csv_path)
    assert matrix.shape == (10, 20)
    assert matrix.shape[0] == 10
    assert matrix.shape[1] == 20

def test_load_count_matrix_missing_file():
    """Test error handling for missing file."""
    with pytest.raises(PreprocessingError):
        load_count_matrix(Path("nonexistent.csv"))