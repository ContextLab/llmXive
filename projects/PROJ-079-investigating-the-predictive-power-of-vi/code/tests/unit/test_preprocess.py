"""
Unit tests for preprocess.py normalization functions.
"""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path

# Import the function to test
from src.preprocess import normalize_counts, save_normalized_counts

@pytest.fixture
def sample_counts_matrix():
    """
    Create a synthetic but realistic counts matrix for testing.
    Rows = Genes, Columns = Samples.
    """
    np.random.seed(42)
    n_genes = 100
    n_samples = 10
    # Generate counts (Poisson-like)
    data = np.random.poisson(lam=10, size=(n_genes, n_samples)).astype(int)
    # Add some variation in library size
    lib_sizes = np.random.uniform(0.5, 2.0, n_samples)
    data = (data.T * lib_sizes).T.astype(int)
    
    index = [f"GENE_{i}" for i in range(n_genes)]
    columns = [f"Sample_{i}" for i in range(n_samples)]
    return pd.DataFrame(data, index=index, columns=columns)

def test_normalize_counts_shape(sample_counts_matrix):
    """Test that output shape matches input shape."""
    result = normalize_counts(sample_counts_matrix)
    assert result.shape == sample_counts_matrix.shape
    assert list(result.index) == list(sample_counts_matrix.index)
    assert list(result.columns) == list(sample_counts_matrix.columns)

def test_normalize_counts_numeric(sample_counts_matrix):
    """Test that output is numeric."""
    result = normalize_counts(sample_counts_matrix)
    assert pd.api.types.is_numeric_dtype(result.values.flatten())
    assert not result.isnull().any().any()

def test_normalize_counts_non_empty(sample_counts_matrix):
    """Test that empty input raises ValueError."""
    with pytest.raises(ValueError, match="Input counts_matrix is empty"):
        normalize_counts(pd.DataFrame())

def test_normalize_counts_non_numeric():
    """Test that non-numeric input raises ValueError."""
    df = pd.DataFrame({"A": ["a", "b"], "B": ["c", "d"]})
    with pytest.raises(ValueError, match="Input contains NaN or non-numeric values"):
        normalize_counts(df)

def test_save_normalized_counts(tmp_path, sample_counts_matrix):
    """Test saving normalized counts to CSV."""
    normalized = normalize_counts(sample_counts_matrix)
    output_file = tmp_path / "test_output.csv"
    save_normalized_counts(normalized, output_file)
    assert output_file.exists()
    # Verify content
    saved_df = pd.read_csv(output_file, index_col=0)
    assert saved_df.shape == normalized.shape

def test_normalize_counts_values_reasonable(sample_counts_matrix):
    """
    Basic sanity check: normalized counts should not be negative or NaN.
    TMM normalization should result in positive values.
    """
    result = normalize_counts(sample_counts_matrix)
    assert (result > 0).all().all() # All values should be positive
    # CPM values can be small but not zero if original counts > 0
    # However, if original counts were 0, CPM is 0.
    # So we check for non-negative
    assert (result >= 0).all().all()
