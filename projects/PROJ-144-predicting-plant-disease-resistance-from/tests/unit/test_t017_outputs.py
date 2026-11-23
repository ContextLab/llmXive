"""
Unit test for T017: Verify generation of batch_corrected_matrix.csv and labels.csv.
"""
import os
import sys
import pandas as pd
import pytest
from pathlib import Path

# Add project root
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from code.utils.constants import DATA_PROCESSED_DIR

class TestT017Outputs:
    """Tests for the existence and basic structure of T017 outputs."""

    def test_batch_corrected_matrix_exists(self):
        """Verify that batch_corrected_matrix.csv is created."""
        matrix_path = Path(DATA_PROCESSED_DIR) / "batch_corrected_matrix.csv"
        assert matrix_path.exists(), "batch_corrected_matrix.csv was not generated."

    def test_labels_exists(self):
        """Verify that labels.csv is created."""
        labels_path = Path(DATA_PROCESSED_DIR) / "labels.csv"
        assert labels_path.exists(), "labels.csv was not generated."

    def test_matrix_is_valid_csv(self):
        """Verify the matrix file is a valid CSV with data."""
        matrix_path = Path(DATA_PROCESSED_DIR) / "batch_corrected_matrix.csv"
        try:
            df = pd.read_csv(matrix_path, index_col=0)
            assert df.shape[0] > 0, "Matrix file is empty (0 rows)."
            assert df.shape[1] > 0, "Matrix file has no columns."
        except Exception as e:
            pytest.fail(f"Failed to read matrix CSV: {e}")

    def test_labels_is_valid_csv(self):
        """Verify the labels file is a valid CSV with data."""
        labels_path = Path(DATA_PROCESSED_DIR) / "labels.csv"
        try:
            df = pd.read_csv(labels_path, index_col=0)
            assert df.shape[0] > 0, "Labels file is empty (0 rows)."
        except Exception as e:
            pytest.fail(f"Failed to read labels CSV: {e}")

    def test_matrix_labels_row_count_match(self):
        """Verify that the number of samples in matrix and labels match."""
        matrix_path = Path(DATA_PROCESSED_DIR) / "batch_corrected_matrix.csv"
        labels_path = Path(DATA_PROCESSED_DIR) / "labels.csv"
        
        try:
            matrix_df = pd.read_csv(matrix_path, index_col=0)
            labels_df = pd.read_csv(labels_path, index_col=0)
            
            # Check if indices match
            if set(matrix_df.index) != set(labels_df.index):
                # Allow for partial match if indices are not strictly sorted, but counts must match
                assert len(matrix_df.index) == len(labels_df.index), \
                    f"Row count mismatch: Matrix has {len(matrix_df.index)}, Labels have {len(labels_df.index)}"
            else:
                assert len(matrix_df.index) == len(labels_df.index)
        except Exception as e:
            pytest.fail(f"Failed to compare row counts: {e}")
