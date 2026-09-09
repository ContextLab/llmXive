"""
Unit tests for preprocess.py functions, specifically normalize_counts.
"""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
import os

# Mock rpy2 to avoid R dependency in unit tests if needed, 
# but for this test we assume rpy2 is available or mock the specific function
from unittest.mock import patch, MagicMock
import rpy2.robjects as ro

from src.preprocess import normalize_counts, save_normalized_counts, calculate_isg_score, filter_samples
from src.config import DATA_PROCESSED_PATH

@pytest.fixture
def sample_counts_matrix():
    """Create a sample count matrix for testing."""
    data = {
        'sample_1': [100, 200, 150, 300],
        'sample_2': [110, 210, 160, 310],
        'sample_3': [90, 190, 140, 290]
    }
    index = ['GeneA', 'GeneB', 'GeneC', 'GeneD']
    return pd.DataFrame(data, index=index)

@pytest.fixture
def temp_processed_dir():
    """Create a temporary directory for processed data."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir

def test_normalize_counts_shape(sample_counts_matrix):
    """Test that output shape matches input shape."""
    result = normalize_counts(sample_counts_matrix)
    assert result.shape == sample_counts_matrix.shape
    assert list(result.index) == list(sample_counts_matrix.index)
    assert list(result.columns) == list(sample_counts_matrix.columns)

def test_normalize_counts_numeric(sample_counts_matrix):
    """Test that output contains numeric values."""
    result = normalize_counts(sample_counts_matrix)
    assert pd.api.types.is_numeric_dtype(result.values.dtype)
    assert not result.isnull().any().any()

def test_normalize_counts_non_empty(sample_counts_matrix):
    """Test that output is not empty."""
    result = normalize_counts(sample_counts_matrix)
    assert not result.empty

def test_normalize_counts_non_negative(sample_counts_matrix):
    """Test that normalized counts are non-negative (CPM can be float, but >= 0)."""
    result = normalize_counts(sample_counts_matrix)
    assert (result >= 0).all().all()

def test_save_normalized_counts(sample_counts_matrix, temp_processed_dir):
    """Test saving normalized counts to CSV."""
    output_path = str(Path(temp_processed_dir) / "test_normalized.csv")
    result = normalize_counts(sample_counts_matrix)
    saved_path = save_normalized_counts(result, output_path)
    
    assert Path(saved_path).exists()
    loaded = pd.read_csv(saved_path, index_col=0)
    assert loaded.shape == result.shape
    assert np.allclose(loaded.values, result.values)

def test_normalize_counts_values_reasonable(sample_counts_matrix):
    """Test that normalized values are in a reasonable range (not exploding)."""
    result = normalize_counts(sample_counts_matrix)
    # CPM values are typically in range 0-10000 for moderate expression
    # Allow a wide range for safety
    assert result.max().max() < 1e6
    assert result.min().min() >= 0

def test_normalize_counts_empty_input():
    """Test that empty input raises ValueError."""
    empty_df = pd.DataFrame()
    with pytest.raises(ValueError, match="empty"):
        normalize_counts(empty_df)

def test_normalize_counts_negative_input():
    """Test that negative input raises ValueError."""
    neg_df = pd.DataFrame({'s1': [-1, 0, 1]})
    with pytest.raises(ValueError, match="negative"):
        normalize_counts(neg_df)

def test_calculate_isg_score(sample_counts_matrix):
    """Test ISG score calculation."""
    isg_genes = ['GeneA', 'GeneB']
    scores = calculate_isg_score(sample_counts_matrix, isg_genes)
    assert len(scores) == sample_counts_matrix.shape[1]
    assert scores.name == "isg_score"
    assert not scores.isnull().any()

def test_filter_samples_removes_missing():
    """Test that filter_samples removes rows with missing strain links."""
    df = pd.DataFrame({
        'strain_accession': ['A', None, 'B', None],
        'value': [1, 2, 3, 4]
    })
    filtered = filter_samples(df)
    assert len(filtered) == 2
    assert filtered['strain_accession'].isnull().sum() == 0

def test_filter_samples_enforces_minimum():
    """Test that filter_samples raises error if < 30 samples remain."""
    df = pd.DataFrame({
        'strain_accession': [f'S{i}' for i in range(20)],
        'value': range(20)
    })
    with pytest.raises(ValueError, match="Minimum required: 30"):
        filter_samples(df)