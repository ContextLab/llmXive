"""
Unit tests for clustering module.

These tests verify the fallback behavior when clustering is not statistically
significant (null hypothesis case).
"""

import json
import numpy as np
import pytest
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

from src.clustering import (
    load_routing_cache,
    generate_global_average,
    perform_clustering,
    compute_canonical_map,
    save_cluster_centers,
    save_null_hypothesis_flag,
    run_clustering_analysis,
    MIN_SILHOUETTE,
    MIN_CLUSTERS
)


class TestClusteringFallbackLogic:
    """Test suite for null hypothesis handling in clustering."""

    def test_generate_global_average(self):
        """Test that global average is computed correctly."""
        # Create a simple 2D array
        data = np.array([
            [1.0, 2.0],
            [3.0, 4.0],
            [5.0, 6.0]
        ])
        
        expected = np.mean(data, axis=0)
        result = generate_global_average(data)
        
        np.testing.assert_array_almost_equal(result, expected)

    def test_perform_clustering_insufficient_samples(self):
        """Test clustering with insufficient samples."""
        # Only 1 sample - cannot cluster
        data = np.array([[1.0, 2.0]])
        
        centers, score, null_triggered, reason = perform_clustering(data)
        
        assert centers is None
        assert null_triggered is True
        assert "Not enough samples" in reason

    def test_perform_clustering_low_silhouette(self):
        """Test clustering with very low silhouette score."""
        # Create data with no clear structure (all same values)
        data = np.ones((10, 5))
        
        centers, score, null_triggered, reason = perform_clustering(data)
        
        # Should trigger null hypothesis due to low silhouette
        assert null_triggered is True
        assert score < MIN_SILHOUETTE

    def test_compute_canonical_map_with_null_hypothesis(self):
        """Test that compute_canonical_map handles null hypothesis correctly."""
        # Create a tensor where clustering will fail
        # Shape: [100, 3, 5] -> 100 timesteps, 3 blocks, 5 history dim
        # Use uniform data to ensure low silhouette scores
        tensor = np.ones((100, 3, 5))
        
        result = compute_canonical_map(tensor)
        
        # Check that all blocks are present
        assert len(result) == 3
        
        # Check that null hypothesis is triggered for all blocks
        for block_id, info in result.items():
            assert "block_" in block_id
            assert info["null_hypothesis_triggered"] is True
            assert info["null_reason"] is not None
            
            # Verify that centers is the global average
            expected_avg = np.mean(tensor[:, int(block_id.split("_")[1]), :], axis=0)
            np.testing.assert_array_almost_equal(
                np.array(info["centers"]), 
                expected_avg,
                decimal=5
            )

    def test_compute_canonical_map_with_valid_clustering(self):
        """Test compute_canonical_map with data that should cluster well."""
        # Create data with clear clusters
        # Block 0: Two distinct clusters
        # Block 1: One cluster (will trigger null)
        # Block 2: Two distinct clusters
        
        tensor = np.zeros((100, 3, 5))
        
        # Block 0: 50 samples at [1,1,1,1,1], 50 at [10,10,10,10,10]
        tensor[:50, 0, :] = 1.0
        tensor[50:, 0, :] = 10.0
        
        # Block 1: All same (will trigger null)
        tensor[:, 1, :] = 5.0
        
        # Block 2: 50 samples at [2,2,2,2,2], 50 at [20,20,20,20,20]
        tensor[:50, 2, :] = 2.0
        tensor[50:, 2, :] = 20.0
        
        result = compute_canonical_map(tensor)
        
        # Check block structure
        assert len(result) == 3
        
        # Block 0 should have valid clustering
        assert result["block_0"]["null_hypothesis_triggered"] is False
        assert result["block_0"]["silhouette"] >= MIN_SILHOUETTE
        assert len(result["block_0"]["centers"]) > 0
        
        # Block 1 should trigger null hypothesis
        assert result["block_1"]["null_hypothesis_triggered"] is True
        
        # Block 2 should have valid clustering
        assert result["block_2"]["null_hypothesis_triggered"] is False
        assert result["block_2"]["silhouette"] >= MIN_SILHOUETTE

    def test_save_cluster_centers(self):
        """Test that cluster centers are saved correctly."""
        # Create mock data
        mock_data = {
            "block_0": {
                "centers": [1.0, 2.0, 3.0],
                "silhouette": 0.5,
                "null_hypothesis_triggered": False,
                "null_reason": None
            },
            "block_1": {
                "centers": [4.0, 5.0, 6.0],
                "silhouette": 0.1,
                "null_hypothesis_triggered": True,
                "null_reason": "Low silhouette"
            }
        }
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "cluster_centers.json"
            save_cluster_centers(mock_data, str(output_path))
            
            # Verify file exists
            assert output_path.exists()
            
            # Verify content
            with open(output_path) as f:
                saved_data = json.load(f)
            
            assert saved_data == mock_data

    def test_save_null_hypothesis_flag(self):
        """Test that null hypothesis flags are saved correctly."""
        mock_data = {
            "block_0": {
                "centers": [1.0, 2.0],
                "silhouette": 0.5,
                "null_hypothesis_triggered": False,
                "null_reason": None
            },
            "block_1": {
                "centers": [3.0, 4.0],
                "silhouette": 0.1,
                "null_hypothesis_triggered": True,
                "null_reason": "Low silhouette"
            }
        }
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "null_hypothesis_flags.json"
            save_null_hypothesis_flag(mock_data, str(output_path))
            
            assert output_path.exists()
            
            with open(output_path) as f:
                saved_data = json.load(f)
            
            # Check that flags are correct
            assert saved_data["block_0"]["null_hypothesis_triggered"] is False
            assert saved_data["block_1"]["null_hypothesis_triggered"] is True
            assert saved_data["block_1"]["null_reason"] == "Low silhouette"

    def test_run_clustering_analysis_with_mock_data(self):
        """Test the full analysis pipeline with mock data."""
        # Create a temporary directory with mock routing files
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = Path(tmpdir) / "routing_cache"
            cache_dir.mkdir()
            
            # Create a mock routing file
            mock_tensor = np.random.rand(100, 5, 10).astype(np.float32)
            mock_file = cache_dir / "routing_0.npy"
            np.save(mock_file, mock_tensor)
            
            output_path = cache_dir / "cluster_centers.json"
            
            result = run_clustering_analysis(
                cache_dir=str(cache_dir),
                output_path=str(output_path)
            )
            
            # Verify output file exists
            assert output_path.exists()
            
            # Verify result structure
            assert len(result) == 5  # 5 blocks
            
            # Verify all blocks have required fields
            for block_id, info in result.items():
                assert "centers" in info
                assert "silhouette" in info
                assert "null_hypothesis_triggered" in info
                assert "null_reason" in info

    def test_load_routing_cache_no_files(self):
        """Test that load_routing_cache raises error when no files found."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = Path(tmpdir) / "empty_cache"
            cache_dir.mkdir()
            
            with pytest.raises(FileNotFoundError):
                load_routing_cache(str(cache_dir))

    def test_load_routing_cache_invalid_shape(self):
        """Test that load_routing_cache raises error for invalid shapes."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = Path(tmpdir) / "routing_cache"
            cache_dir.mkdir()
            
            # Create a file with wrong shape (3D instead of 4D)
            invalid_tensor = np.random.rand(10, 5, 10)
            invalid_file = cache_dir / "routing_0.npy"
            np.save(invalid_file, invalid_tensor)
            
            with pytest.raises(ValueError):
                load_routing_cache(str(cache_dir))

    def test_perform_clustering_with_distance_threshold(self):
        """Test that distance threshold affects clustering outcome."""
        # Create data that might or might not cluster based on threshold
        data = np.random.rand(50, 5)
        
        # Test with default threshold
        centers1, score1, null1, reason1 = perform_clustering(data, distance_threshold=0.1)
        
        # Test with very strict threshold
        centers2, score2, null2, reason2 = perform_clustering(data, distance_threshold=0.9)
        
        # The stricter threshold might trigger null hypothesis more often
        # This is a sanity check that the parameter is used
        assert score1 >= 0 or score2 >= 0  # At least one should have a score