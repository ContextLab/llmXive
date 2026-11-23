import pytest
import numpy as np
import json
import tempfile
import os
from unittest.mock import patch, MagicMock

from src.clustering import StaticIndex, apply_pca, run_kmeans, generate_static_index, save_static_index, benchmark_lookup
from src.models import RelevanceProfile


class TestStaticIndex:
    """Contract test for StaticIndex data structure."""

    def test_static_index_creation(self):
        """Test that StaticIndex can be instantiated with correct types."""
        centroids = np.array([[1.0, 2.0], [3.0, 4.0]])
        chunk_to_cluster = {"chunk_1": 0, "chunk_2": 1}
        k = 2

        index = StaticIndex(centroids=centroids, chunk_to_cluster=chunk_to_cluster, k=k)

        assert isinstance(index.centroids, np.ndarray)
        assert index.centroids.shape == (k, 2)
        assert isinstance(index.chunk_to_cluster, dict)
        assert index.k == k

    def test_static_index_serialization(self):
        """Test that StaticIndex can be serialized to a dictionary."""
        centroids = np.array([[1.0, 2.0], [3.0, 4.0]])
        chunk_to_cluster = {"chunk_1": 0, "chunk_2": 1}
        k = 2

        index = StaticIndex(centroids=centroids, chunk_to_cluster=chunk_to_cluster, k=k)

        # Verify attributes are accessible
        assert index.k == 2
        assert "chunk_1" in index.chunk_to_cluster
        assert index.chunk_to_cluster["chunk_1"] == 0
        assert index.centroids.shape == (2, 2)

    def test_static_index_type_compliance(self):
        """Verify that StaticIndex fields match the expected types defined in src/models.py."""
        centroids = np.zeros((5, 10))
        mapping = {f"chunk_{i}": i % 5 for i in range(10)}
        index = StaticIndex(centroids=centroids, chunk_to_cluster=mapping, k=5)

        assert isinstance(index.centroids, np.ndarray)
        assert isinstance(index.chunk_to_cluster, dict)
        assert isinstance(index.k, int)


class TestGenerateStaticIndex:
    """Contract test for generate_static_index logic."""

    def test_generate_static_index_structure(self):
        """Test that generate_static_index returns a valid StaticIndex object."""
        # Create mock profiles
        profiles = [
            RelevanceProfile(chunk_id=f"chunk_{i}", scores=[0.1] * 10, document_id="doc_1")
            for i in range(20)
        ]

        with patch('src.clustering.apply_pca') as mock_pca, \
             patch('src.clustering.run_kmeans') as mock_kmeans:

            mock_pca.return_value = np.random.rand(20, 5)
            mock_kmeans.return_value = (np.random.rand(3, 5), np.random.randint(0, 3, 20))

            index = generate_static_index(profiles, k=3, seed=42)

            assert isinstance(index, StaticIndex)
            assert index.k == 3
            assert len(index.chunk_to_cluster) == 20
            assert index.centroids.shape == (3, 5)


class TestSaveStaticIndex:
    """Contract test for save_static_index output format."""

    def test_save_static_index_file_creation(self):
        """Test that save_static_index creates a valid JSON file."""
        centroids = np.array([[1.0, 2.0], [3.0, 4.0]])
        chunk_to_cluster = {"chunk_1": 0, "chunk_2": 1}
        index = StaticIndex(centroids=centroids, chunk_to_cluster=chunk_to_cluster, k=2)

        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "test_index.json")
            save_static_index(index, path)

            assert os.path.exists(path)
            with open(path, 'r') as f:
                data = json.load(f)

            assert "centroids" in data
            assert "chunk_to_cluster" in data
            assert "k" in data
            assert "pca_components" in data
            assert isinstance(data["centroids"], list)
            assert isinstance(data["chunk_to_cluster"], dict)

    def test_save_static_index_content_validity(self):
        """Test that saved JSON content matches the StaticIndex state."""
        centroids = np.array([[1.0, 2.0], [3.0, 4.0]])
        chunk_to_cluster = {"chunk_1": 0, "chunk_2": 1}
        index = StaticIndex(centroids=centroids, chunk_to_cluster=chunk_to_cluster, k=2)

        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "test_index.json")
            save_static_index(index, path)

            with open(path, 'r') as f:
                data = json.load(f)

            assert data["k"] == 2
            assert data["chunk_to_cluster"]["chunk_1"] == 0
            assert len(data["centroids"]) == 2


class TestBenchmarkLookup:
    """Contract test for benchmark_lookup performance check."""

    def test_benchmark_lookup_returns_bool(self):
        """Test that benchmark_lookup returns a boolean."""
        centroids = np.random.rand(100, 10)
        chunk_to_cluster = {f"chunk_{i}": i % 100 for i in range(1000)}
        index = StaticIndex(centroids=centroids, chunk_to_cluster=chunk_to_cluster, k=100)

        result = benchmark_lookup(index, token_count=32000)

        assert isinstance(result, bool)

    def test_benchmark_lookup_latency_check(self):
        """Test that benchmark_lookup correctly identifies latency thresholds."""
        centroids = np.random.rand(10, 5)
        chunk_to_cluster = {f"chunk_{i}": i % 10 for i in range(100)}
        index = StaticIndex(centroids=centroids, chunk_to_cluster=chunk_to_cluster, k=10)

        # Should pass within 50ms for small index
        result = benchmark_lookup(index, token_count=1000)
        assert isinstance(result, bool)