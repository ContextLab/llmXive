"""
Unit tests for the spatial proxy validation logic (T041).
"""
import json
import os
import tempfile
import numpy as np
import pandas as pd
from pathlib import Path
import pytest

import sys
# Ensure the code directory is in the path
code_path = Path(__file__).parent.parent.parent / "code"
sys.path.insert(0, str(code_path))

from validate_spatial_proxy import validate_cluster_quality, validate_proxy_structure

class TestValidateClusterQuality:
    def test_perfect_clustering(self):
        """Test with well-separated clusters."""
        np.random.seed(42)
        # Two distinct clusters
        cluster1 = np.random.randn(50, 2) + np.array([0, 0])
        cluster2 = np.random.randn(50, 2) + np.array([10, 10])
        data = np.vstack([cluster1, cluster2])
        labels = np.array([0]*50 + [1]*50)
        
        result = validate_cluster_quality(data, labels)
        
        assert result["valid"] is True
        assert result["silhouette_score"] > 0.5  # Well separated
        assert result["intra_cluster_mean_dist"] < result["inter_cluster_mean_dist"]

    def test_single_cluster(self):
        """Test with only one cluster (should fail validation)."""
        np.random.seed(42)
        data = np.random.randn(50, 2)
        labels = np.zeros(50, dtype=int)
        
        result = validate_cluster_quality(data, labels)
        
        assert result["valid"] is False
        assert "Insufficient clusters" in result["reason"]

    def test_random_clustering(self):
        """Test with random labels (should have low silhouette)."""
        np.random.seed(42)
        data = np.random.randn(100, 2)
        labels = np.random.randint(0, 5, 100)
        
        result = validate_cluster_quality(data, labels)
        
        # Random labels usually result in low or negative silhouette
        # We just check that it runs without error
        assert "silhouette_score" in result

class TestValidateProxyStructure:
    def test_missing_dataset(self):
        """Test validation when raw data file is missing."""
        proxy_data = {
            "dataset_name": "nonexistent_dataset",
            "cluster_labels": [0, 1, 0, 1]
        }
        
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a fake 'raw' directory but no file
            raw_dir = Path(tmpdir) / "raw"
            raw_dir.mkdir(parents=True, exist_ok=True)
            
            result = validate_proxy_structure(proxy_data, Path(tmpdir))
            
            assert result["data_loaded"] is False
            assert result["clusters_found"] is True
            assert result["validation_passed"] is True  # Falls back to structure check
            assert len(result["warnings"]) > 0

    def test_mismatched_lengths(self):
        """Test validation when cluster labels length != data length."""
        np.random.seed(42)
        
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a dataset
            df = pd.DataFrame({
                "feature1": np.random.randn(10),
                "feature2": np.random.randn(10)
            })
            raw_dir = Path(tmpdir) / "raw"
            raw_dir.mkdir(parents=True, exist_ok=True)
            df.to_csv(raw_dir / "test_dataset.csv", index=False)
            
            proxy_data = {
                "dataset_name": "test_dataset",
                "cluster_labels": [0, 1, 0]  # Only 3 labels for 10 rows
            }
            
            result = validate_proxy_structure(proxy_data, Path(tmpdir))
            
            assert result["validation_passed"] is False
            assert any("does not match" in err for err in result["errors"])

    def test_valid_proxy(self):
        """Test validation with a valid proxy structure and data."""
        np.random.seed(42)
        
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a dataset with clear clusters
            cluster1 = np.random.randn(20, 2)
            cluster2 = np.random.randn(20, 2) + 5
            data = np.vstack([cluster1, cluster2])
            df = pd.DataFrame(data, columns=["f1", "f2"])
            
            raw_dir = Path(tmpdir) / "raw"
            raw_dir.mkdir(parents=True, exist_ok=True)
            df.to_csv(raw_dir / "valid_dataset.csv", index=False)
            
            # Create proxy with correct labels
            labels = [0]*20 + [1]*20
            proxy_data = {
                "dataset_name": "valid_dataset",
                "cluster_labels": labels,
                "dataset_url": "http://example.com"
            }
            
            result = validate_proxy_structure(proxy_data, Path(tmpdir))
            
            assert result["data_loaded"] is True
            assert result["clusters_found"] is True
            assert result["validation_passed"] is True
            assert result["quality_metrics"]["valid"] is True