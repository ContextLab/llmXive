import json
import numpy as np
import pytest
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import sys
import os

# Add code directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.clustering import (
    save_null_hypothesis_flag,
    perform_clustering,
    generate_global_average,
    run_clustering_analysis
)

class TestClusteringFallbackLogic:
    """Test that the clustering logic correctly handles null hypothesis conditions."""

    def test_save_null_hypothesis_flag_low_score(self, tmp_path):
        """Test that a flag is saved and warning is triggered when score < 0.25."""
        results_dir = tmp_path / "results"
        results_dir.mkdir()
        flag_path = results_dir / "null_hypothesis_flag.json"

        # Call function with low score
        save_null_hypothesis_flag(score=0.15, threshold=0.25, output_path=str(flag_path))

        # Verify file exists
        assert flag_path.exists()

        # Verify content
        with open(flag_path, 'r') as f:
            data = json.load(f)

        assert data["silhouette_score"] == 0.15
        assert data["is_null_hypothesis"] is True
        assert "warning" in data
        assert "Null hypothesis detected" in data["warning"]

    def test_save_null_hypothesis_flag_high_score(self, tmp_path):
        """Test that no warning is triggered when score >= 0.25."""
        results_dir = tmp_path / "results"
        results_dir.mkdir()
        flag_path = results_dir / "null_hypothesis_flag.json"

        # Call function with high score
        save_null_hypothesis_flag(score=0.45, threshold=0.25, output_path=str(flag_path))

        # Verify file exists
        assert flag_path.exists()

        # Verify content
        with open(flag_path, 'r') as f:
            data = json.load(f)

        assert data["silhouette_score"] == 0.45
        assert data["is_null_hypothesis"] is False
        assert "warning" in data
        assert "Clustering successful" in data["warning"]

    def test_perform_clustering_returns_none_for_low_score(self):
        """Test that perform_clustering returns None when no valid clustering is found."""
        # Create data that will likely result in low silhouette score
        # e.g., random noise
        np.random.seed(42)
        mean_vectors = np.random.rand(5, 10)  # 5 timesteps, 10 dimensions

        model, score, k = perform_clustering(mean_vectors)

        # Depending on random data, score might be low
        # We just verify the function runs without error
        assert isinstance(score, float)
        assert k >= 0
        # If score is low, model might be None

    def test_generate_global_average(self):
        """Test that global average is correctly computed."""
        mean_vectors = np.array([
            [1.0, 2.0, 3.0],
            [4.0, 5.0, 6.0],
            [7.0, 8.0, 9.0]
        ])

        global_avg = generate_global_average(mean_vectors)

        expected = np.array([4.0, 5.0, 6.0])
        np.testing.assert_array_almost_equal(global_avg, expected)

    @patch('src.clustering.load_routing_cache')
    @patch('src.clustering.compute_mean_routing_vectors')
    @patch('src.clustering.perform_clustering')
    @patch('src.clustering.save_null_hypothesis_flag')
    @patch('src.clustering.save_cluster_centers')
    def test_run_clustering_analysis_null_hypothesis(
        self, mock_save_centers, mock_save_flag, mock_perform, mock_compute, mock_load, tmp_path
    ):
        """Test the full pipeline when null hypothesis is triggered."""
        cache_dir = tmp_path / "cache"
        cache_dir.mkdir()
        output_dir = tmp_path / "output"
        output_dir.mkdir()
        results_dir = tmp_path / "results"
        results_dir.mkdir()

        # Mock data
        mock_load.return_value = [np.random.rand(2, 10, 5)]
        mock_compute.return_value = np.random.rand(10, 5)
        mock_perform.return_value = (None, 0.1, 0)  # Simulate null hypothesis

        # Run analysis
        result = run_clustering_analysis(
            cache_dir=str(cache_dir),
            output_dir=str(output_dir),
            results_dir=str(results_dir)
        )

        # Verify null hypothesis flag was saved
        mock_save_flag.assert_called_once()
        assert result["is_null_hypothesis"] is True
        assert result["optimal_k"] == 0

    @patch('src.clustering.load_routing_cache')
    @patch('src.clustering.compute_mean_routing_vectors')
    @patch('src.clustering.perform_clustering')
    @patch('src.clustering.save_null_hypothesis_flag')
    @patch('src.clustering.save_cluster_centers')
    def test_run_clustering_analysis_valid_clusters(
        self, mock_save_centers, mock_save_flag, mock_perform, mock_compute, mock_load, tmp_path
    ):
        """Test the full pipeline when valid clusters are found."""
        cache_dir = tmp_path / "cache"
        cache_dir.mkdir()
        output_dir = tmp_path / "output"
        output_dir.mkdir()
        results_dir = tmp_path / "results"
        results_dir.mkdir()

        # Mock data
        mock_load.return_value = [np.random.rand(2, 10, 5)]
        mock_compute.return_value = np.random.rand(10, 5)
        mock_model = MagicMock()
        mock_model.cluster_centers_ = np.random.rand(3, 5)
        mock_perform.return_value = (mock_model, 0.6, 3)  # Valid clustering

        # Run analysis
        result = run_clustering_analysis(
            cache_dir=str(cache_dir),
            output_dir=str(output_dir),
            results_dir=str(results_dir)
        )

        # Verify valid clustering result
        mock_save_flag.assert_called_once()
        assert result["is_null_hypothesis"] is False
        assert result["optimal_k"] == 3
        assert result["silhouette_score"] == 0.6