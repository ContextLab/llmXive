"""
Unit tests for clustering logic, specifically focusing on fallback behavior.
"""

import json
import numpy as np
import pytest
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from src.clustering import (
    load_routing_cache,
    compute_mean_routing_vectors,
    perform_clustering,
    generate_global_average,
    save_cluster_centers,
    save_null_hypothesis_flag,
    run_clustering_analysis
)


class TestClusteringFallbackLogic:
    """Tests for null hypothesis handling in clustering."""

    def test_perform_clustering_low_k(self):
        """Test that clustering returns None when k < 2."""
        mean_vectors = np.random.rand(10, 5)
        kmeans, score, k_used = perform_clustering(mean_vectors, k=1)
        assert kmeans is None
        assert score < 0
        assert k_used == 1

    def test_perform_clustering_low_silhouette(self):
        """Test that clustering returns None when silhouette score is low."""
        # Create data that will result in low silhouette score
        # (e.g., all points very similar)
        mean_vectors = np.ones((10, 5)) * 0.5
        kmeans, score, k_used = perform_clustering(mean_vectors, k=3)
        assert kmeans is None
        assert score < 0.25
        assert k_used == 3

    def test_save_null_hypothesis_flag_triggered(self):
        """Test saving null hypothesis flag when triggered."""
        with tempfile.TemporaryDirectory() as tmpdir:
            flag_path = Path(tmpdir) / "null_flag.json"
            save_null_hypothesis_flag(is_null=True, score=0.15, output_path=str(flag_path))

            with open(flag_path, "r") as f:
                data = json.load(f)

            assert data["null_hypothesis_triggered"] is True
            assert abs(data["silhouette_score"] - 0.15) < 1e-6
            assert "Silhouette score < 0.25" in data["reason"]

    def test_save_null_hypothesis_flag_not_triggered(self):
        """Test saving null hypothesis flag when not triggered."""
        with tempfile.TemporaryDirectory() as tmpdir:
            flag_path = Path(tmpdir) / "null_flag.json"
            save_null_hypothesis_flag(is_null=False, score=0.45, output_path=str(flag_path))

            with open(flag_path, "r") as f:
                data = json.load(f)

            assert data["null_hypothesis_triggered"] is False
            assert abs(data["silhouette_score"] - 0.45) < 1e-6
            assert data["reason"] == "N/A"

    def test_run_clustering_analysis_null_hypothesis(self):
        """Test that run_clustering_analysis handles null hypothesis correctly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create mock routing cache
            cache_dir = Path(tmpdir) / "cache"
            cache_dir.mkdir()
            # Create a dummy tensor file
            dummy_tensor = np.random.rand(100, 8)  # 100 timesteps, 8 history_dim
            np.save(cache_dir / "image_001.npy", dummy_tensor)

            results_dir = Path(tmpdir) / "results"
            results_dir.mkdir()
            centers_path = results_dir / "cluster_centers.json"
            flag_path = results_dir / "null_hypothesis_flag.json"

            # Force null hypothesis by using k=1
            result = run_clustering_analysis(
                cache_dir=str(cache_dir),
                cluster_centers_path=str(centers_path),
                null_flag_path=str(flag_path),
                k=1
            )

            assert result["status"] == "null_hypothesis"
            assert centers_path.exists()
            assert flag_path.exists()

            with open(flag_path, "r") as f:
                flag_data = json.load(f)
            assert flag_data["null_hypothesis_triggered"] is True

    def test_run_clustering_analysis_success(self):
        """Test that run_clustering_analysis succeeds when clustering is valid."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create mock routing cache with distinct clusters
            cache_dir = Path(tmpdir) / "cache"
            cache_dir.mkdir()
            # Create data with clear clusters
            timesteps = 100
            history_dim = 8
            # Create two distinct groups
            data = np.vstack([
                np.random.rand(timesteps // 2, history_dim) * 0.1,  # Cluster 1 near 0
                np.random.rand(timesteps - timesteps // 2, history_dim) * 0.1 + 0.9  # Cluster 2 near 1
            ])
            np.save(cache_dir / "image_001.npy", data)

            results_dir = Path(tmpdir) / "results"
            results_dir.mkdir()
            centers_path = results_dir / "cluster_centers.json"
            flag_path = results_dir / "null_hypothesis_flag.json"

            result = run_clustering_analysis(
                cache_dir=str(cache_dir),
                cluster_centers_path=str(centers_path),
                null_flag_path=str(flag_path),
                k=2
            )

            assert result["status"] == "clustering_success"
            assert result["silhouette_score"] >= 0.25
            assert centers_path.exists()
            assert flag_path.exists()

            with open(flag_path, "r") as f:
                flag_data = json.load(f)
            assert flag_data["null_hypothesis_triggered"] is False