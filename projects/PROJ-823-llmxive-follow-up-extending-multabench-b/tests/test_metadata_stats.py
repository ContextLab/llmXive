"""
Tests for metadata_stats.py
"""

import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys
import os

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from analysis.metadata_stats import compute_feature_stats, process_single_dataset, save_summary_csv

class TestComputeFeatureStats:
    def test_empty_dataframe(self):
        """Test with empty DataFrame"""
        df = pd.DataFrame()
        stats = compute_feature_stats(df)
        assert stats["cardinality"] == 0.0
        assert stats["missingness"] == 0.0
        assert stats["sparsity"] == 0.0
        assert stats["variance"] == 0.0

    def test_single_feature_no_missing(self):
        """Test with single feature, no missing values"""
        df = pd.DataFrame({
            'feature1': [1, 2, 3, 4, 5]
        })
        stats = compute_feature_stats(df)
        assert stats["cardinality"] == 5.0  # 5 unique values
        assert stats["missingness"] == 0.0
        assert stats["sparsity"] == 0.0  # No zeros
        assert stats["variance"] > 0  # Should have variance

    def test_missing_values(self):
        """Test with missing values"""
        df = pd.DataFrame({
            'feature1': [1, 2, np.nan, 4, 5],
            'feature2': [1, 2, 3, np.nan, 5]
        })
        stats = compute_feature_stats(df)
        assert stats["missingness"] > 0.0
        assert stats["missingness"] <= 0.5  # Max 40% missing

    def test_zero_values_sparsity(self):
        """Test sparsity calculation with zero values"""
        df = pd.DataFrame({
            'feature1': [0, 0, 1, 0, 0],
            'feature2': [0, 1, 0, 1, 0]
        })
        stats = compute_feature_stats(df)
        # feature1: 4/5 zeros, feature2: 3/5 zeros -> avg = 0.7
        assert stats["sparsity"] == 0.7

    def test_variance_calculation(self):
        """Test variance calculation"""
        df = pd.DataFrame({
            'feature1': [1, 2, 3, 4, 5],
            'feature2': [10, 20, 30, 40, 50]
        })
        stats = compute_feature_stats(df)
        # feature1 var = 2.5, feature2 var = 250 -> avg = 126.25
        assert stats["variance"] > 0

    def test_non_numeric_columns_ignored(self):
        """Test that non-numeric columns are handled appropriately"""
        df = pd.DataFrame({
            'numeric1': [1, 2, 3, 4, 5],
            'string_col': ['a', 'b', 'c', 'd', 'e']
        })
        stats = compute_feature_stats(df)
        # Should only consider numeric columns
        assert stats["cardinality"] == 5.0  # Only numeric1

class TestSaveSummaryCsv:
    def test_save_with_results(self, tmp_path):
        """Test saving results to CSV"""
        results = [
            {"dataset_id": "test1", "cardinality": 10.0, "missingness": 0.1, "sparsity": 0.2, "variance": 5.0},
            {"dataset_id": "test2", "cardinality": 20.0, "missingness": 0.2, "sparsity": 0.3, "variance": 10.0}
        ]
        output_path = tmp_path / "test_output.csv"
        save_summary_csv(results, str(output_path))
        
        assert output_path.exists()
        df = pd.read_csv(output_path)
        assert len(df) == 2
        assert list(df.columns) == ["dataset_id", "cardinality", "missingness", "sparsity", "variance"]
        assert df.iloc[0]["dataset_id"] == "test1"

    def test_save_empty_results(self, tmp_path):
        """Test saving empty results"""
        results = []
        output_path = tmp_path / "empty_output.csv"
        save_summary_csv(results, str(output_path))
        
        assert output_path.exists()
        df = pd.read_csv(output_path)
        assert len(df) == 0
        assert list(df.columns) == ["dataset_id", "cardinality", "missingness", "sparsity", "variance"]

class TestProcessSingleDataset:
    def test_process_valid_parquet(self, tmp_path):
        """Test processing a valid parquet file"""
        # Create test data
        df = pd.DataFrame({
            'feature1': [1, 2, 3, 4, 5],
            'feature2': [10, 20, 30, 40, 50]
        })
        file_path = tmp_path / "test.parquet"
        df.to_parquet(file_path)
        
        dataset_info = {
            "dataset_id": "test_dataset",
            "path": str(file_path)
        }
        
        result = process_single_dataset(dataset_info)
        
        assert result is not None
        assert result["dataset_id"] == "test_dataset"
        assert result["cardinality"] > 0
        assert result["variance"] > 0

    def test_process_missing_file(self, tmp_path):
        """Test processing a non-existent file"""
        dataset_info = {
            "dataset_id": "missing_dataset",
            "path": str(tmp_path / "nonexistent.parquet")
        }
        
        result = process_single_dataset(dataset_info)
        assert result is None

    def test_process_invalid_format(self, tmp_path):
        """Test processing an unsupported file format"""
        file_path = tmp_path / "test.txt"
        file_path.write_text("test content")
        
        dataset_info = {
            "dataset_id": "invalid_dataset",
            "path": str(file_path)
        }
        
        result = process_single_dataset(dataset_info)
        assert result is None