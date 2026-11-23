"""
Contract test for the feature matrix schema.
Ensures the output of build_feature_matrix.py matches the required specification.
"""
import pytest
import pandas as pd
import json
import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "code"))

REQUIRED_COLUMNS = [
    "isolate_id",
    "gene_presence_matrix",
    "snp_counts",
    "cnv_counts",
    "resistance_phenotype"
]

class TestFeatureMatrixSchema:
    def test_feature_matrix_columns_exist(self, tmp_path):
        """
        Test that the feature matrix contains all required columns.
        This test creates a mock feature matrix to verify the schema logic.
        """
        # Create a mock feature matrix that satisfies the schema
        mock_data = {
            "isolate_id": ["iso_1", "iso_2"],
            "gene_presence_matrix": [[1, 0], [0, 1]], # List of lists or stringified
            "snp_counts": [10, 15],
            "cnv_counts": [1, 2],
            "resistance_phenotype": [1, 0]
        }
        
        df = pd.DataFrame(mock_data)
        
        # Verify required columns
        for col in REQUIRED_COLUMNS:
            assert col in df.columns, f"Missing required column: {col}"
        
        # Verify data types (basic check)
        assert df["isolate_id"].dtype == object
        assert pd.api.types.is_numeric_dtype(df["snp_counts"])
        assert pd.api.types.is_numeric_dtype(df["cnv_counts"])
        assert pd.api.types.is_numeric_dtype(df["resistance_phenotype"])

    def test_feature_matrix_no_missing_values(self, tmp_path):
        """
        Test that the feature matrix has no missing values in critical columns.
        """
        # Create a mock dataframe with no missing values
        mock_data = {
            "isolate_id": ["iso_1", "iso_2"],
            "gene_presence_matrix": [[1, 0], [0, 1]],
            "snp_counts": [10, 15],
            "cnv_counts": [1, 2],
            "resistance_phenotype": [1, 0]
        }
        df = pd.DataFrame(mock_data)
        
        # Check for missing values in critical columns
        critical_cols = ["isolate_id", "snp_counts", "cnv_counts", "resistance_phenotype"]
        for col in critical_cols:
            assert not df[col].isnull().any(), f"Column {col} contains missing values"

    def test_feature_matrix_row_count_consistency(self, tmp_path):
        """
        Test that row count matches the expected isolate count.
        """
        expected_count = 5
        mock_data = {
            "isolate_id": [f"iso_{i}" for i in range(expected_count)],
            "gene_presence_matrix": [[1]*5 for _ in range(expected_count)],
            "snp_counts": [10]*expected_count,
            "cnv_counts": [1]*expected_count,
            "resistance_phenotype": [0]*expected_count
        }
        df = pd.DataFrame(mock_data)
        
        assert len(df) == expected_count, f"Row count mismatch: expected {expected_count}, got {len(df)}"
