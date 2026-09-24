"""
Tests for User Story 2: Static Index Construction.

Tests include:
- Contract test for static index structure
- Integration test for K-Means convergence and retry logic
"""
import pytest
import numpy as np
import json
import tempfile
import os
from unittest.mock import patch, MagicMock
from src.models import RelevanceProfile
from src.clustering import (
    apply_pca,
    run_kmeans,
    generate_static_index,
    save_static_index,
    benchmark_lookup
)
from src.config import Config

class TestPCA:
    """Tests for PCA dimensionality reduction"""
    
    def test_apply_pca_empty_profiles(self):
        """Test that apply_pca raises ValueError for empty profiles"""
        with pytest.raises(ValueError, match="Cannot apply PCA to an empty list"):
            apply_pca([])
    
    def test_apply_pca_single_profile(self):
        """Test PCA with a single profile"""
        profile = RelevanceProfile(
            chunk_id="test-1",
            scores=[0.1, 0.2, 0.3, 0.4, 0.5],
            document_id="doc-1"
        )
        
        config = Config(seed=42, chunk_size=2048, model_path="test", k_clusters=10)
        result = apply_pca([profile], config)
        
        assert isinstance(result, np.ndarray)
        assert result.shape[0] == 1
        assert result.shape[1] <= 5  # n_components limited by features
    
    def test_apply_pca_multiple_profiles(self):
        """Test PCA with multiple profiles"""
        profiles = [
            RelevanceProfile(chunk_id=f"test-{i}", scores=[float(i), float(i+1), float(i+2)], document_id="doc-1")
            for i in range(10)
        ]
        
        config = Config(seed=42, chunk_size=2048, model_path="test", k_clusters=10)
        result = apply_pca(profiles, config)
        
        assert isinstance(result, np.ndarray)
        assert result.shape[0] == 10
        assert result.shape[1] <= 3  # n_components limited by features
    
    def test_apply_pca_inconsistent_lengths(self):
        """Test PCA handles inconsistent score lengths"""
        profiles = [
            RelevanceProfile(chunk_id="test-1", scores=[0.1, 0.2, 0.3], document_id="doc-1"),
            RelevanceProfile(chunk_id="test-2", scores=[0.4, 0.5], document_id="doc-1"),  # Different length
        ]
        
        config = Config(seed=42, chunk_size=2048, model_path="test", k_clusters=10)
        with pytest.raises(ValueError):
            apply_pca(profiles, config)

class TestKMeans:
    """Tests for K-Means clustering"""
    
    def test_run_kmeans_empty_data(self):
        """Test that run_kmeans raises ValueError for empty data"""
        with pytest.raises(ValueError, match="Cannot run K-Means on empty data"):
            run_kmeans(np.array([]), k=5)
    
    def test_run_kmeans_invalid_k(self):
        """Test that run_kmeans raises ValueError for invalid k"""
        data = np.random.rand(10, 5)
        with pytest.raises(ValueError, match="Invalid number of clusters"):
            run_kmeans(data, k=0)
    
    def test_run_kmeans_basic(self):
        """Test basic K-Means functionality"""
        # Create synthetic data with clear clusters
        np.random.seed(42)
        data = np.vstack([
            np.random.randn(30, 5) + [0, 0, 0, 0, 0],
            np.random.randn(30, 5) + [5, 5, 5, 5, 5],
            np.random.randn(30, 5) + [10, 10, 10, 10, 10]
        ])
        
        centroids, labels = run_kmeans(data, k=3, retry_count=3, random_state=42)
        
        assert centroids.shape == (3, 5)
        assert len(labels) == 90
        assert set(labels) == {0, 1, 2}
    
    def test_run_kmeans_retry_logic(self):
        """Test K-Means retry logic for convergence failures"""
        # Create data that might cause convergence issues
        np.random.seed(123)
        data = np.random.rand(20, 5)
        
        centroids, labels = run_kmeans(data, k=5, retry_count=5, random_state=42)
        
        assert centroids.shape == (5, 5)
        assert len(labels) == 20
        assert len(set(labels)) == 5  # All clusters should be used
    
    def test_run_kmeans_k_exceeds_samples(self):
        """Test K-Means when k exceeds number of samples"""
        data = np.random.rand(5, 3)
        
        centroids, labels = run_kmeans(data, k=10, retry_count=3, random_state=42)
        
        # Should adjust k to number of samples
        assert centroids.shape[0] == 5
        assert len(labels) == 5
        assert len(set(labels)) == 5

class TestStaticIndex:
    """Tests for static index generation and serialization"""
    
    def test_generate_static_index(self):
        """Test static index generation"""
        profiles = [
            RelevanceProfile(chunk_id=f"chunk-{i}", scores=[float(i)], document_id="doc-1")
            for i in range(5)
        ]
        centroids = np.array([[0.0], [1.0], [2.0], [3.0], [4.0]])
        labels = np.array([0, 1, 2, 3, 4])
        
        config = Config(seed=42, chunk_size=2048, model_path="test", k_clusters=5)
        index = generate_static_index(profiles, centroids, labels, config)
        
        assert 'centroids' in index
        assert 'chunk_to_cluster' in index
        assert 'k' in index
        assert 'metadata' in index
        assert index['k'] == 5
        assert len(index['chunk_to_cluster']) == 5
        assert index['chunk_to_cluster']['chunk-0'] == 0
    
    def test_save_static_index(self):
        """Test saving static index to JSON"""
        profiles = [
            RelevanceProfile(chunk_id=f"chunk-{i}", scores=[float(i)], document_id="doc-1")
            for i in range(3)
        ]
        centroids = np.array([[0.0], [1.0], [2.0]])
        labels = np.array([0, 1, 2])
        
        config = Config(seed=42, chunk_size=2048, model_path="test", k_clusters=3)
        index = generate_static_index(profiles, centroids, labels, config)
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_path = f.name
        
        try:
            save_static_index(index, temp_path)
            
            # Verify file exists and is valid JSON
            assert os.path.exists(temp_path)
            with open(temp_path, 'r') as f:
                loaded = json.load(f)
            
            assert 'centroids' in loaded
            assert 'chunk_to_cluster' in loaded
            assert 'k' in loaded
            assert isinstance(loaded['centroids'], list)  # Should be serialized as list
        finally:
            os.unlink(temp_path)
    
    def test_benchmark_lookup(self):
        """Test lookup benchmark"""
        index = {
            'centroids': np.array([[0.0], [1.0]]),
            'chunk_to_cluster': {'chunk-0': 0, 'chunk-1': 1},
            'k': 2,
            'metadata': {}
        }
        
        result = benchmark_lookup(index, token_count=100)
        assert isinstance(result, bool)
        # Should be True for small number of chunks

class TestIntegration:
    """Integration tests for the full clustering pipeline"""
    
    def test_end_to_end_clustering(self):
        """Test end-to-end clustering pipeline"""
        # Create test profiles
        profiles = [
            RelevanceProfile(
                chunk_id=f"chunk-{i}",
                scores=[float(i + j) for j in range(10)],
                document_id=f"doc-{i % 3}"
            )
            for i in range(20)
        ]
        
        config = Config(seed=42, chunk_size=2048, model_path="test", k_clusters=5)
        
        # Apply PCA
        reduced_data = apply_pca(profiles, config)
        assert reduced_data.shape[0] == 20
        
        # Run K-Means
        centroids, labels = run_kmeans(reduced_data, k=5, retry_count=3, random_state=42)
        assert centroids.shape == (5, reduced_data.shape[1])
        assert len(set(labels)) == 5
        
        # Generate index
        index = generate_static_index(profiles, centroids, labels, config)
        assert len(index['chunk_to_cluster']) == 20
        assert index['k'] == 5

if __name__ == "__main__":
    pytest.main([__file__, "-v"])