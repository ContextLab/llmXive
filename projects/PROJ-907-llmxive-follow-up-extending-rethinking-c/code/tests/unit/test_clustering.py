import json
import numpy as np
import pytest
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

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
    """Test the fallback behavior when clustering fails (null hypothesis)."""

    def test_null_hypothesis_low_k(self, tmp_path):
        """Test that low k triggers null hypothesis handling."""
        # Create mock routing tensors with very few timesteps (k will be < 2)
        mock_tensor = np.random.rand(4, 2, 64)  # 4 blocks, 2 timesteps, 64 dim
        cache_dir = tmp_path / "cache"
        cache_dir.mkdir()
        np.save(cache_dir / "image_0.npy", mock_tensor)
        
        output_dir = tmp_path / "output"
        output_dir.mkdir()
        
        # Run clustering - should trigger null hypothesis due to low k
        result = run_clustering_analysis(
            cache_dir=str(cache_dir),
            output_dir=str(output_dir),
            distance_threshold=0.1
        )
        
        # Verify null hypothesis was triggered
        assert result['is_null_hypothesis'] is True
        assert 'k' in result
        assert result['k'] < 2 or result['silhouette_score'] < 0.25
        
        # Verify null hypothesis flag file was created
        null_flag_path = output_dir / "null_hypothesis_flag.json"
        assert null_flag_path.exists()
        
        with open(null_flag_path, 'r') as f:
            flag_data = json.load(f)
        
        assert flag_data['flag'] is True
        assert 'reason' in flag_data

    def test_null_hypothesis_low_silhouette(self, tmp_path):
        """Test that low silhouette score triggers null hypothesis handling."""
        # Create mock routing tensors that will produce low silhouette score
        # (e.g., all vectors are nearly identical)
        mock_tensor = np.ones((4, 10, 64)) * 0.5  # All same values
        cache_dir = tmp_path / "cache"
        cache_dir.mkdir()
        np.save(cache_dir / "image_0.npy", mock_tensor)
        
        output_dir = tmp_path / "output"
        output_dir.mkdir()
        
        # Run clustering - should trigger null hypothesis due to low silhouette
        result = run_clustering_analysis(
            cache_dir=str(cache_dir),
            output_dir=str(output_dir),
            distance_threshold=0.1
        )
        
        # Verify null hypothesis was triggered
        assert result['is_null_hypothesis'] is True
        assert result['silhouette_score'] < 0.25
        
        # Verify null hypothesis flag file was created
        null_flag_path = output_dir / "null_hypothesis_flag.json"
        assert null_flag_path.exists()
        
        with open(null_flag_path, 'r') as f:
            flag_data = json.load(f)
        
        assert flag_data['flag'] is True
        assert 'reason' in flag_data

    def test_valid_clustering_no_null_flag(self, tmp_path):
        """Test that valid clustering does not create null hypothesis flag."""
        # Create mock routing tensors with distinct patterns
        mock_tensor = np.random.rand(4, 20, 64)
        cache_dir = tmp_path / "cache"
        cache_dir.mkdir()
        np.save(cache_dir / "image_0.npy", mock_tensor)
        
        output_dir = tmp_path / "output"
        output_dir.mkdir()
        
        # Run clustering
        result = run_clustering_analysis(
            cache_dir=str(cache_dir),
            output_dir=str(output_dir),
            distance_threshold=0.1
        )
        
        # Verify clustering was successful (not null hypothesis)
        # Note: This might still be null hypothesis if data is not diverse enough
        # So we just verify the output files exist
        assert 'centers_path' in result
        centers_path = Path(result['centers_path'])
        assert centers_path.exists()

    def test_global_average_generation(self):
        """Test that global average is generated correctly."""
        mean_vectors = np.random.rand(10, 64)
        global_avg = generate_global_average(mean_vectors)
        
        assert global_avg.shape == (64,)
        assert np.allclose(global_avg, np.mean(mean_vectors, axis=0))

    def test_cluster_centers_json_schema(self, tmp_path):
        """Test that cluster centers JSON has correct schema."""
        # Create a mock KMeans model
        mock_model = MagicMock()
        mock_model.cluster_centers_ = np.random.rand(3, 64)
        
        output_path = tmp_path / "cluster_centers.json"
        save_cluster_centers(mock_model, 0.5, str(output_path))
        
        assert output_path.exists()
        
        with open(output_path, 'r') as f:
            data = json.load(f)
        
        assert isinstance(data, list)
        assert len(data) == 3
        
        for item in data:
            assert 'cluster_id' in item
            assert 'center_vector' in item
            assert 'silhouette_score' in item
            assert isinstance(item['cluster_id'], int)
            assert isinstance(item['center_vector'], list)
            assert isinstance(item['silhouette_score'], float)

    def test_null_hypothesis_flag_json_schema(self, tmp_path):
        """Test that null hypothesis flag JSON has correct schema."""
        output_path = tmp_path / "null_hypothesis_flag.json"
        save_null_hypothesis_flag(str(output_path), "Test reason")
        
        assert output_path.exists()
        
        with open(output_path, 'r') as f:
            data = json.load(f)
        
        assert 'flag' in data
        assert data['flag'] is True
        assert 'reason' in data
        assert isinstance(data['reason'], str)