"""
Unit tests for clustering module fallback logic.
"""

import json
import numpy as np
import pytest
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import sys
import os

# Add code/src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from clustering import (
    perform_clustering,
    generate_global_average,
    compute_canonical_map,
    save_cluster_centers,
    save_null_hypothesis_flag
)

class TestClusteringFallbackLogic:
    """Tests for the null hypothesis fallback behavior in clustering."""

    def test_fallback_on_low_silhouette(self):
        """Test that global average is used when silhouette score is too low."""
        # Create mock data: 10 images, 100 timesteps, 2 blocks, 64 history_dim
        # We'll craft data such that clustering is poor (e.g., all same values)
        num_images = 10
        num_timesteps = 100
        num_blocks = 2
        history_dim = 64
        
        # Create uniform data (no variation -> poor clustering)
        routing_tensor = np.ones((num_images, num_timesteps, num_blocks, history_dim))
        
        # Run clustering with a strict threshold
        results = perform_clustering(routing_tensor, distance_threshold=0.5)
        
        # Check that null hypothesis was triggered for both blocks
        for block_key in results:
            assert results[block_key]["null_hypothesis_triggered"] is True
            # The centers should be the global average (all 1.0s)
            expected_avg = [1.0] * history_dim
            assert np.allclose(results[block_key]["centers"], expected_avg)

    def test_fallback_on_insufficient_samples(self):
        """Test fallback when there are fewer samples than clusters."""
        # Create data with only 1 sample (image=1, timestep=1)
        num_images = 1
        num_timesteps = 1
        num_blocks = 2
        history_dim = 64
        
        routing_tensor = np.random.rand(num_images, num_timesteps, num_blocks, history_dim)
        
        results = perform_clustering(routing_tensor, distance_threshold=0.25)
        
        for block_key in results:
            assert results[block_key]["null_hypothesis_triggered"] is True
            assert "Insufficient samples" in results[block_key]["null_reason"]

    def test_fallback_on_single_cluster(self):
        """Test fallback when clustering results in only 1 cluster."""
        # Create data where all points are identical -> KMeans will put them in 1 cluster
        num_images = 5
        num_timesteps = 50
        num_blocks = 2
        history_dim = 64
        
        # All values same -> only 1 cluster
        routing_tensor = np.ones((num_images, num_timesteps, num_blocks, history_dim))
        
        results = perform_clustering(routing_tensor, distance_threshold=0.25)
        
        for block_key in results:
            assert results[block_key]["null_hypothesis_triggered"] is True
            # Reason should mention cluster count
            assert "cluster" in results[block_key]["null_reason"].lower()

    def test_compute_canonical_map_returns_fallback(self):
        """Test that compute_canonical_map returns global average on null hypothesis."""
        num_images = 5
        num_timesteps = 50
        num_blocks = 2
        history_dim = 64
        
        routing_tensor = np.ones((num_images, num_timesteps, num_blocks, history_dim))
        
        canonical_map = compute_canonical_map(routing_tensor, distance_threshold=0.5)
        
        for block_key in canonical_map:
            expected = [1.0] * history_dim
            assert np.allclose(canonical_map[block_key], expected)

    def test_save_null_hypothesis_flag_creates_file(self):
        """Test that save_null_hypothesis_flag creates the expected JSON file."""
        mock_results = {
            "block_0": {
                "centers": [0.5] * 10,
                "silhouette": 0.1,
                "null_hypothesis_triggered": True,
                "null_reason": "Low silhouette"
            },
            "block_1": {
                "centers": [0.5] * 10,
                "silhouette": 0.6,
                "null_hypothesis_triggered": False,
                "null_reason": None
            }
        }
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_flag.json"
            save_null_hypothesis_flag(mock_results, str(output_path))
            
            assert output_path.exists()
            
            with open(output_path) as f:
                data = json.load(f)
            
            assert data["null_hypothesis_triggered_globally"] is True
            assert data["details"]["block_0"]["null_hypothesis_triggered"] is True
            assert data["details"]["block_1"]["null_hypothesis_triggered"] is False

    def test_save_cluster_centers_creates_file(self):
        """Test that save_cluster_centers creates the expected JSON file."""
        mock_results = {
            "block_0": {
                "centers": [0.5] * 10,
                "silhouette": 0.1,
                "null_hypothesis_triggered": True,
                "null_reason": "Low silhouette"
            }
        }
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_centers.json"
            save_cluster_centers(mock_results, str(output_path))
            
            assert output_path.exists()
            
            with open(output_path) as f:
                data = json.load(f)
            
            assert "block_0" in data
            assert data["block_0"]["centers"] == [0.5] * 10
            assert data["block_0"]["null_hypothesis_triggered"] is True