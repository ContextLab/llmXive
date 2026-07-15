"""
Unit tests for clustering module, specifically focusing on fallback logic.

Tests verify that:
1. Global average is generated when k < 2.
2. Global average is generated when silhouette score < 0.25.
3. System output flags the null result condition.
"""

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
    save_null_hypothesis_flag,
    run_clustering_analysis
)

class TestClusteringFallbackLogic:
    """Test cases for clustering fallback logic."""
    
    def test_perform_clustering_insufficient_timesteps(self):
        """Test clustering with only 1 timestep triggers null hypothesis."""
        # Create mean vectors with only 1 timestep
        mean_vectors = np.random.rand(1, 64)
        
        model, score, best_k = perform_clustering(mean_vectors, max_k=5)
        
        assert model is None
        assert score is None
        assert best_k == 0
        
    def test_perform_clustering_low_silhouette_score(self):
        """Test clustering with very low silhouette score triggers null hypothesis."""
        # Create mean vectors that will result in low silhouette score
        # Using identical vectors to force poor clustering
        mean_vectors = np.tile(np.random.rand(64), (10, 1))
        
        model, score, best_k = perform_clustering(mean_vectors, max_k=5)
        
        # Should trigger null hypothesis due to low score
        assert model is None
        assert best_k == 0
        
    def test_generate_global_average(self):
        """Test global average generation."""
        mean_vectors = np.random.rand(10, 64)
        global_avg = generate_global_average(mean_vectors)
        
        assert global_avg.shape == (64,)
        assert np.allclose(global_avg, np.mean(mean_vectors, axis=0))
        
    def test_save_null_hypothesis_flag(self):
        """Test saving null hypothesis flag."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_flag.json"
            
            save_null_hypothesis_flag(True, "Test reason", output_path)
            
            assert output_path.exists()
            
            with open(output_path, 'r') as f:
                data = json.load(f)
                
            assert data["is_null_hypothesis"] is True
            assert data["reason"] == "Test reason"
            
    def test_run_clustering_analysis_null_hypothesis_flag(self):
        """Test that run_clustering_analysis properly flags null hypothesis."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            
            # Create mock routing data with insufficient timesteps
            mock_data = {
                'data': np.random.rand(4, 2, 64),  # 4 blocks, 2 timesteps, 64 dim
                'file_path': str(tmpdir_path / "mock.npy"),
                'filename': "mock.npy"
            }
            
            # Create a dummy file
            np.save(mock_data['file_path'], mock_data['data'])
            
            # Run analysis with a configuration that forces null hypothesis
            # We'll patch perform_clustering to return None
            with patch('src.clustering.perform_clustering', return_value=(None, None, 0)):
                results = run_clustering_analysis(
                    cache_dir=tmpdir_path,
                    max_k=10,
                    random_state=42,
                    output_dir=tmpdir_path
                )
                
                assert results["is_null_hypothesis"] is True
                assert "reason" in results
                
                # Verify the flag file was created
                flag_path = tmpdir_path / "null_hypothesis_flag.json"
                assert flag_path.exists()
                
                with open(flag_path, 'r') as f:
                    flag_data = json.load(f)
                    
                assert flag_data["is_null_hypothesis"] is True
                
    def test_run_clustering_analysis_successful_clustering(self):
        """Test successful clustering without null hypothesis."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            
            # Create mock routing data with enough timesteps and variety
            # Generate data with clear cluster structure
            n_timesteps = 20
            history_dim = 64
            n_blocks = 4
            
            # Create data with two distinct groups
            data = np.zeros((n_blocks, n_timesteps, history_dim))
            for t in range(n_timesteps):
                if t < 10:
                    data[:, t, :] = np.random.rand(history_dim) * 0.1  # Cluster 1
                else:
                    data[:, t, :] = np.random.rand(history_dim) * 0.1 + 0.5  # Cluster 2
            
            mock_data = {
                'data': data,
                'file_path': str(tmpdir_path / "mock.npy"),
                'filename': "mock.npy"
            }
            
            np.save(mock_data['file_path'], mock_data['data'])
            
            # Run analysis
            results = run_clustering_analysis(
                cache_dir=tmpdir_path,
                max_k=5,
                random_state=42,
                output_dir=tmpdir_path
            )
            
            # Should not be null hypothesis
            assert results["is_null_hypothesis"] is False
            assert results["optimal_k"] >= 2
            assert results["silhouette_score"] is not None
            assert results["silhouette_score"] >= 0.25
            
            # Verify cluster centers file was created
            centers_path = tmpdir_path / "cluster_centers.json"
            assert centers_path.exists()
            
            with open(centers_path, 'r') as f:
                centers_data = json.load(f)
                
            assert "cluster_centers" in centers_data
            assert centers_data["is_null_hypothesis"] is False