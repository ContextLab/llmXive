import pytest
import numpy as np
import json
import tempfile
import os
from unittest.mock import patch, MagicMock

from src.clustering import (
    apply_pca,
    run_kmeans,
    generate_static_index,
    save_static_index,
    benchmark_lookup
)
from src.models import StaticIndex, RelevanceProfile
from src.config import Config

class TestApplyPCA:
    def test_apply_pca_basic(self):
        """Test basic PCA application"""
        profiles = [
            RelevanceProfile(chunk_id="c1", scores=[1.0, 2.0, 3.0, 4.0], document_id="d1"),
            RelevanceProfile(chunk_id="c2", scores=[2.0, 3.0, 4.0, 5.0], document_id="d1"),
            RelevanceProfile(chunk_id="c3", scores=[3.0, 4.0, 5.0, 6.0], document_id="d1")
        ]
        
        result = apply_pca(profiles, n_components=2)
        
        assert result.shape == (3, 2)
        assert isinstance(result, np.ndarray)
    
    def test_apply_pca_empty_list(self):
        """Test that PCA raises error on empty list"""
        with pytest.raises(ValueError, match="Cannot apply PCA to empty list"):
            apply_pca([])
    
    def test_apply_pca_zero_dimension(self):
        """Test that PCA raises error on zero-dimensional scores"""
        profiles = [
            RelevanceProfile(chunk_id="c1", scores=[], document_id="d1")
        ]
        with pytest.raises(ValueError, match="Score vectors are empty"):
            apply_pca(profiles)

class TestRunKMeans:
    def test_run_kmeans_basic(self):
        """Test basic K-Means execution"""
        data = np.array([
            [1.0, 2.0],
            [1.5, 1.8],
            [5.0, 8.0],
            [8.0, 8.0],
            [1.0, 0.6],
            [9.0, 11.0]
        ])
        
        centroids, labels = run_kmeans(data, k=2)
        
        assert centroids.shape == (2, 2)
        assert len(labels) == 6
        assert set(labels) == {0, 1}
    
    def test_run_kmeans_insufficient_samples(self):
        """Test that K-Means raises error when samples < clusters"""
        data = np.array([[1.0, 2.0], [3.0, 4.0]])
        with pytest.raises(ValueError, match="Cannot create"):
            run_kmeans(data, k=5)
    
    def test_run_kmeans_retry_logic(self):
        """Test that retry logic works for bad initializations"""
        data = np.random.rand(100, 10)
        centroids, labels = run_kmeans(data, k=5, retry_count=5)
        
        assert len(set(labels)) == 5  # All clusters should be formed

class TestGenerateStaticIndex:
    def test_generate_static_index_basic(self):
        """Test basic static index generation"""
        profiles = [
            RelevanceProfile(chunk_id="c1", scores=[1.0, 2.0], document_id="d1"),
            RelevanceProfile(chunk_id="c2", scores=[3.0, 4.0], document_id="d1"),
            RelevanceProfile(chunk_id="c3", scores=[5.0, 6.0], document_id="d1")
        ]
        centroids = np.array([[1.5, 3.0], [5.0, 6.0]])
        labels = np.array([0, 0, 1])
        config = Config()
        
        index = generate_static_index(profiles, centroids, labels, k=2, config=config)
        
        assert isinstance(index, StaticIndex)
        assert index.k == 2
        assert len(index.chunk_to_cluster) == 3
        assert index.chunk_to_cluster["c1"] == 0
        assert index.chunk_to_cluster["c3"] == 1

class TestSaveStaticIndex:
    def test_save_static_index_creates_file(self):
        """Test that save_static_index creates a valid JSON file"""
        index = StaticIndex(
            centroids=np.array([[1.0, 2.0], [3.0, 4.0]]),
            chunk_to_cluster={"c1": 0, "c2": 1},
            k=2
        )
        config = Config()
        
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as tmp:
            tmp_path = tmp.name
        
        try:
            save_static_index(index, tmp_path, config)
            
            assert os.path.exists(tmp_path)
            
            with open(tmp_path, 'r') as f:
                data = json.load(f)
            
            assert "metadata" in data
            assert "centroids" in data
            assert "chunk_to_cluster" in data
            assert data["metadata"]["k"] == 2
            assert data["metadata"]["n_samples"] == 2
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
    
    def test_save_static_index_invalid_path(self):
        """Test that save_static_index raises error for non-JSON path"""
        index = StaticIndex(
            centroids=np.array([[1.0]]),
            chunk_to_cluster={"c1": 0},
            k=1
        )
        config = Config()
        
        with pytest.raises(ValueError, match="must be a .json file"):
            save_static_index(index, "output.txt", config)
    
    def test_save_static_index_none_index(self):
        """Test that save_static_index raises error for None index"""
        config = Config()
        with pytest.raises(ValueError, match="Cannot save None"):
            save_static_index(None, "output.json", config)

class TestBenchmarkLookup:
    def test_benchmark_lookup_basic(self):
        """Test basic benchmark lookup"""
        index = StaticIndex(
            centroids=np.array([[1.0, 2.0]]),
            chunk_to_cluster={"c1": 0, "c2": 0, "c3": 0},
            k=1
        )
        
        result = benchmark_lookup(index, token_count=32000)
        
        # Should return True if latency < 50ms (which it should be for small index)
        assert isinstance(result, bool)
    
    def test_benchmark_lookup_empty_index(self):
        """Test benchmark with empty index"""
        index = StaticIndex(
            centroids=np.array([]),
            chunk_to_cluster={},
            k=0
        )
        
        result = benchmark_lookup(index)
        assert result is True  # Should return True with warning

class TestKMeansConvergenceAndRetry:
    def test_kmeans_convergence_with_retry(self):
        """Test that K-Means converges even with bad initializations"""
        # Create data that might cause convergence issues
        np.random.seed(42)
        data = np.random.rand(50, 5)
        
        centroids, labels = run_kmeans(data, k=5, retry_count=3)
        
        # Verify all clusters are populated
        unique_labels = np.unique(labels)
        assert len(unique_labels) == 5
        assert centroids.shape == (5, 5)
    
    def test_kmeans_fails_after_max_retries(self):
        """Test that K-Means raises error after max retries"""
        # This is hard to trigger artificially, so we test the logic
        # by mocking KMeans to always fail
        with patch('src.clustering.KMeans') as mock_kmeans:
            mock_kmeans.return_value.fit_predict.side_effect = Exception("Convergence failed")
            
            data = np.random.rand(10, 5)
            with pytest.raises(RuntimeError, match="failed to converge"):
                run_kmeans(data, k=2, retry_count=2)
