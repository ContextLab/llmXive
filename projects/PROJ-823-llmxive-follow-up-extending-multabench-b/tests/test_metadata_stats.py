"""
Unit tests for metadata statistics computation.
"""
import os
import sys
import tempfile
import pandas as pd
import numpy as np
from pathlib import Path
import pytest

# Add project root to path
project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root))

from analysis.metadata_stats import compute_feature_stats, process_single_dataset

class TestMetadataStats:
    """Test cases for metadata statistics computation."""

    def test_compute_feature_stats_basic(self):
        """Test basic statistics computation on a simple DataFrame."""
        data = {
            "feature1": [1.0, 2.0, 3.0, 4.0, 5.0],
            "feature2": [10.0, 20.0, 30.0, 40.0, 50.0],
            "feature3": [1.0, 1.0, 1.0, 1.0, 1.0]  # Zero variance
        }
        df = pd.DataFrame(data)
        
        stats = compute_feature_stats(df, "test_dataset")
        
        assert stats["dataset_id"] == "test_dataset"
        assert stats["cardinality"] > 0
        assert stats["missingness"] == 0.0
        assert stats["sparsity"] == 0.0
        assert stats["variance"] > 0

    def test_compute_feature_stats_missing_values(self):
        """Test statistics computation with missing values."""
        data = {
            "feature1": [1.0, np.nan, 3.0, 4.0, 5.0],
            "feature2": [10.0, 20.0, np.nan, 40.0, 50.0]
        }
        df = pd.DataFrame(data)
        
        stats = compute_feature_stats(df, "test_dataset_missing")
        
        assert stats["dataset_id"] == "test_dataset_missing"
        assert stats["missingness"] > 0.0
        assert stats["missingness"] < 1.0

    def test_compute_feature_stats_sparsity(self):
        """Test statistics computation with zero values."""
        data = {
            "feature1": [0.0, 2.0, 0.0, 4.0, 0.0],
            "feature2": [0.0, 0.0, 30.0, 0.0, 50.0]
        }
        df = pd.DataFrame(data)
        
        stats = compute_feature_stats(df, "test_dataset_sparse")
        
        assert stats["dataset_id"] == "test_dataset_sparse"
        assert stats["sparsity"] > 0.0

    def test_compute_feature_stats_empty_dataframe(self):
        """Test statistics computation on an empty DataFrame."""
        df = pd.DataFrame()
        
        stats = compute_feature_stats(df, "empty_dataset")
        
        assert stats["dataset_id"] == "empty_dataset"
        assert stats["cardinality"] == 0.0
        assert stats["missingness"] == 0.0
        assert stats["sparsity"] == 0.0
        assert stats["variance"] == 0.0

    def test_compute_feature_stats_non_numeric(self):
        """Test that non-numeric columns are ignored."""
        data = {
            "numeric1": [1.0, 2.0, 3.0],
            "numeric2": [10.0, 20.0, 30.0],
            "categorical": ["a", "b", "c"]
        }
        df = pd.DataFrame(data)
        
        stats = compute_feature_stats(df, "mixed_dataset")
        
        assert stats["dataset_id"] == "mixed_dataset"
        # Should only consider numeric columns
        assert stats["cardinality"] > 0

    def test_process_single_dataset_csv(self, tmp_path):
        """Test processing a dataset from a CSV file."""
        # Create a temporary directory structure
        dataset_dir = tmp_path / "test_dataset"
        dataset_dir.mkdir()
        
        # Create a CSV file
        csv_path = dataset_dir / "data.csv"
        data = {
            "feature1": [1.0, 2.0, 3.0, 4.0, 5.0],
            "feature2": [10.0, 20.0, 30.0, 40.0, 50.0]
        }
        pd.DataFrame(data).to_csv(csv_path, index=False)
        
        dataset_info = {
            "dataset_id": "test_dataset",
            "path": str(dataset_dir),
            "tabular_files": [str(csv_path)]
        }
        
        stats = process_single_dataset(dataset_info)
        
        assert stats is not None
        assert stats["dataset_id"] == "test_dataset"
        assert stats["cardinality"] > 0

    def test_process_single_dataset_parquet(self, tmp_path):
        """Test processing a dataset from a Parquet file."""
        # Create a temporary directory structure
        dataset_dir = tmp_path / "test_dataset_parquet"
        dataset_dir.mkdir()
        
        # Create a Parquet file
        parquet_path = dataset_dir / "data.parquet"
        data = {
            "feature1": [1.0, 2.0, 3.0, 4.0, 5.0],
            "feature2": [10.0, 20.0, 30.0, 40.0, 50.0]
        }
        pd.DataFrame(data).to_parquet(parquet_path)
        
        dataset_info = {
            "dataset_id": "test_dataset_parquet",
            "path": str(dataset_dir),
            "tabular_files": [str(parquet_path)]
        }
        
        stats = process_single_dataset(dataset_info)
        
        assert stats is not None
        assert stats["dataset_id"] == "test_dataset_parquet"
        assert stats["cardinality"] > 0

    def test_process_single_dataset_missing_file(self, tmp_path):
        """Test processing a dataset with missing files."""
        dataset_dir = tmp_path / "test_dataset_missing"
        dataset_dir.mkdir()
        
        dataset_info = {
            "dataset_id": "test_dataset_missing",
            "path": str(dataset_dir),
            "tabular_files": [str(dataset_dir / "nonexistent.csv")]
        }
        
        stats = process_single_dataset(dataset_info)
        
        # Should handle gracefully and return zero stats
        assert stats is not None
        assert stats["dataset_id"] == "test_dataset_missing"