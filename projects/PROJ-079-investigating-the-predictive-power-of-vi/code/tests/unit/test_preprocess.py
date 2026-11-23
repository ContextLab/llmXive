import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
import os
from unittest.mock import patch, MagicMock
import rpy2.robjects as ro
from rpy2.robjects import pandas2ri
from rpy2.robjects.packages import importr

from src.preprocess import normalize_counts, save_normalized_counts, run_normalize_pipeline
from src.config import DATA_PROCESSED_PATH

# Mock edgeR for unit tests to avoid R dependency issues in pure unit test context
# unless the environment actually has R installed.
# We will test the logic flow and input validation primarily.

@pytest.fixture
def sample_counts_matrix():
    """Create a sample counts matrix (samples x genes)."""
    data = {
        'GeneA': [100, 200, 150, 300],
        'GeneB': [50, 100, 75, 120],
        'GeneC': [200, 400, 300, 600],
        'GeneD': [10, 20, 15, 30]
    }
    index = ['Sample1', 'Sample2', 'Sample3', 'Sample4']
    return pd.DataFrame(data, index=index)

@pytest.fixture
def temp_processed_dir():
    """Create a temporary directory for processed data."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a mock DATA_PROCESSED_PATH
        mock_path = Path(tmpdir)
        yield mock_path

def test_normalize_counts_shape(sample_counts_matrix):
    """Test that normalize_counts returns a DataFrame of the same shape."""
    # Mock edgeR operations to return a dummy matrix of the same shape
    with patch('src.preprocess.edgeR') as mock_edgeR:
        mock_dge = MagicMock()
        mock_edgeR.DGEList.return_value = mock_dge
        mock_edgeR.calcNormFactors.return_value = mock_dge

        # Create a mock matrix that looks like the transposed input
        mock_matrix = np.ones(sample_counts_matrix.T.shape)
        mock_r_matrix = ro.IntMatrix(mock_matrix)
        mock_edgeR.getNormalizedCounts.return_value = mock_r_matrix

        result = normalize_counts(sample_counts_matrix)

        assert isinstance(result, pd.DataFrame)
        assert result.shape == sample_counts_matrix.shape

def test_normalize_counts_numeric(sample_counts_matrix):
    """Test that normalize_counts raises on non-numeric input."""
    non_numeric = sample_counts_matrix.copy()
    non_numeric['GeneA'] = non_numeric['GeneA'].astype(str)

    with pytest.raises(ValueError, match="All columns in counts_matrix must be numeric"):
        normalize_counts(non_numeric)

def test_normalize_counts_non_empty(sample_counts_matrix):
    """Test that normalize_counts raises on empty input."""
    empty_df = pd.DataFrame()
    with pytest.raises(ValueError, match="cannot be empty"):
        normalize_counts(empty_df)

def test_normalize_counts_non_negative(sample_counts_matrix):
    """Test that normalize_counts handles negative values (edgeR might warn, but we check shape)."""
    # edgeR typically expects non-negative counts, but we test the function flow.
    # If edgeR raises on negative, we catch it.
    neg_df = sample_counts_matrix.copy()
    neg_df.iloc[0, 0] = -10

    with patch('src.preprocess.edgeR') as mock_edgeR:
        mock_dge = MagicMock()
        mock_edgeR.DGEList.return_value = mock_dge
        mock_edgeR.calcNormFactors.return_value = mock_dge
        mock_matrix = np.ones(sample_counts_matrix.T.shape)
        mock_r_matrix = ro.IntMatrix(mock_matrix)
        mock_edgeR.getNormalizedCounts.return_value = mock_r_matrix

        # Should not raise ValueError for non-numeric, but might raise R error if edgeR is strict
        # We assume the mock handles it gracefully for shape check
        result = normalize_counts(neg_df)
        assert result.shape == neg_df.shape

def test_save_normalized_counts(sample_counts_matrix, temp_processed_dir):
    """Test that save_normalized_counts writes a CSV file."""
    with patch('src.preprocess.edgeR') as mock_edgeR:
        mock_dge = MagicMock()
        mock_edgeR.DGEList.return_value = mock_dge
        mock_edgeR.calcNormFactors.return_value = mock_dge
        mock_matrix = np.ones(sample_counts_matrix.T.shape)
        mock_r_matrix = ro.IntMatrix(mock_matrix)
        mock_edgeR.getNormalizedCounts.return_value = mock_r_matrix

        norm_df = normalize_counts(sample_counts_matrix)
        output_path = temp_processed_dir / "test_norm.csv"
        saved_path = save_normalized_counts(norm_df, str(output_path))

        assert saved_path.exists()
        assert saved_path == output_path

        # Verify content
        loaded = pd.read_csv(saved_path, index_col=0)
        assert loaded.shape == norm_df.shape
        assert list(loaded.columns) == list(norm_df.columns)

def test_normalize_counts_values_reasonable(sample_counts_matrix):
    """Test that normalized values are reasonable (positive, similar magnitude)."""
    with patch('src.preprocess.edgeR') as mock_edgeR:
        mock_dge = MagicMock()
        mock_edgeR.DGEList.return_value = mock_dge
        mock_edgeR.calcNormFactors.return_value = mock_dge
        # Return a matrix that is slightly different from input to simulate normalization
        mock_matrix = sample_counts_matrix.T.values * 1.1
        mock_r_matrix = ro.FloatMatrix(mock_matrix)
        mock_edgeR.getNormalizedCounts.return_value = mock_r_matrix

        result = normalize_counts(sample_counts_matrix)

        assert (result > 0).all().all()
        # Check that values are not identical to input (simulating normalization effect)
        assert not result.equals(sample_counts_matrix)

def test_normalize_counts_empty_input():
    """Test that empty DataFrame raises ValueError."""
    empty_df = pd.DataFrame()
    with pytest.raises(ValueError, match="cannot be empty"):
        normalize_counts(empty_df)

def test_normalize_counts_negative_input(sample_counts_matrix):
    """Test behavior with negative inputs (mocked to pass)."""
    neg_df = sample_counts_matrix.copy()
    neg_df.iloc[0, 0] = -5

    with patch('src.preprocess.edgeR') as mock_edgeR:
        mock_dge = MagicMock()
        mock_edgeR.DGEList.return_value = mock_dge
        mock_edgeR.calcNormFactors.return_value = mock_dge
        mock_matrix = np.ones(sample_counts_matrix.T.shape)
        mock_r_matrix = ro.IntMatrix(mock_matrix)
        mock_edgeR.getNormalizedCounts.return_value = mock_r_matrix

        result = normalize_counts(neg_df)
        assert result.shape == neg_df.shape

def test_calculate_isg_score():
    """Placeholder for ISG score test (not implemented in this task)."""
    # This test exists to satisfy the test file structure if referenced elsewhere
    # but the logic is in T016.
    pass

def test_filter_samples_removes_missing():
    """Placeholder for filter_samples test (not implemented in this task)."""
    pass

def test_filter_samples_enforces_minimum():
    """Placeholder for filter_samples test (not implemented in this task)."""
    pass

def test_run_isg_score_pipeline():
    """Placeholder for ISG pipeline test (not implemented in this task)."""
    pass

def test_save_isg_scores():
    """Placeholder for ISG save test (not implemented in this task)."""
    pass

def test_filter_samples_preserves_other_columns():
    """Placeholder for filter_samples test (not implemented in this task)."""
    pass

def test_filter_samples_with_alternative_column_names():
    """Placeholder for filter_samples test (not implemented in this task)."""
    pass
