"""
Unit tests for edge cases in the llmXive pipeline.
Covers: empty inputs, NaN/Inf handling, dimension mismatches,
out-of-distribution queries, and memory limits.
"""

import os
import sys
import tempfile
import json
import numpy as np
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Ensure project root is in path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.retrieval.strategies import (
    single_nearest_neighbor,
    unweighted_mean,
    cosine_weighted_average,
    load_skill_index,
    reconstruct_matrices
)
from src.ingestion.download_weights import generate_proxy_weights
from src.evaluation.runner import check_memory_usage
from src.retrieval.vector_db import load_flattened_vectors


class TestEdgeCasesStrategies:
    """Tests for edge cases in retrieval strategies."""

    def test_empty_skill_index(self):
        """Test handling of an empty skill index."""
        # Create an empty skill index structure
        empty_index = {
            'vectors': np.array([]).reshape(0, 100),
            'metadata': []
        }

        # Mock query vector
        query = np.random.randn(100)

        # Expect ValueError or empty result
        with pytest.raises((ValueError, IndexError)):
            single_nearest_neighbor(query, empty_index)

    def test_nan_in_vectors(self):
        """Test handling of NaN values in skill vectors."""
        # Create index with NaN
        nan_vector = np.full(100, np.nan)
        normal_vector = np.random.randn(100)

        index_data = {
            'vectors': np.vstack([normal_vector, nan_vector]),
            'metadata': [{'id': 'normal'}, {'id': 'nan'}]
        }

        query = np.random.randn(100)

        # Should either handle gracefully or raise specific error
        # For now, we expect it to not crash with a generic exception
        try:
            result = single_nearest_neighbor(query, index_data)
            # If it returns, verify it didn't pick the NaN vector
            assert result['metadata']['id'] == 'normal'
        except Exception as e:
            # If it raises, it should be a specific error, not a crash
            assert "nan" in str(e).lower() or "invalid" in str(e).lower()

    def test_inf_in_vectors(self):
        """Test handling of Inf values in skill vectors."""
        inf_vector = np.full(100, np.inf)
        normal_vector = np.random.randn(100)

        index_data = {
            'vectors': np.vstack([normal_vector, inf_vector]),
            'metadata': [{'id': 'normal'}, {'id': 'inf'}]
        }

        query = np.random.randn(100)

        try:
            result = single_nearest_neighbor(query, index_data)
            assert result['metadata']['id'] == 'normal'
        except Exception as e:
            assert "inf" in str(e).lower() or "invalid" in str(e).lower()

    def test_dimension_mismatch(self):
        """Test handling of query with wrong dimension."""
        # Create index with 100-dim vectors
        index_data = {
            'vectors': np.random.randn(5, 100),
            'metadata': [{'id': f'skill_{i}'} for i in range(5)]
        }

        # Query with 50 dims
        wrong_query = np.random.randn(50)

        with pytest.raises(ValueError) as exc_info:
            single_nearest_neighbor(wrong_query, index_data)

        assert "dimension" in str(exc_info.value).lower()

    def test_identical_similarity_scores(self):
        """Test handling of identical similarity scores (tie-breaking)."""
        # Create two identical vectors
        vec = np.random.randn(100)
        index_data = {
            'vectors': np.vstack([vec, vec]),
            'metadata': [{'id': 'skill_A'}, {'id': 'skill_B'}]
        }

        query = vec  # Exactly same as both

        # Should return one of them without crashing
        result = single_nearest_neighbor(query, index_data)
        assert result['metadata']['id'] in ['skill_A', 'skill_B']

    def test_unweighted_mean_empty_list(self):
        """Test unweighted_mean with empty list of vectors."""
        with pytest.raises(ValueError):
            unweighted_mean([])

    def test_unweighted_mean_single_vector(self):
        """Test unweighted_mean with single vector."""
        vec = np.random.randn(100)
        result = unweighted_mean([vec])
        np.testing.assert_array_almost_equal(result, vec)

    def test_cosine_weighted_single_neighbor(self):
        """Test cosine_weighted_average with single neighbor."""
        vec = np.random.randn(100)
        neighbors = [(vec, 0.95)]  # (vector, similarity)

        result = cosine_weighted_average(neighbors)
        np.testing.assert_array_almost_equal(result, vec)

    def test_cosine_weighted_negative_similarity(self):
        """Test handling of negative similarity scores."""
        vec1 = np.random.randn(100)
        vec2 = np.random.randn(100)

        # vec2 is opposite direction
        vec2 = -vec2

        neighbors = [
            (vec1, 0.8),
            (vec2, -0.8)
        ]

        # Should handle negative similarities (possibly by reweighting or error)
        result = cosine_weighted_average(neighbors)
        assert result is not None
        assert not np.any(np.isnan(result))
        assert not np.any(np.isinf(result))


class TestEdgeCasesIngestion:
    """Tests for edge cases in ingestion."""

    def test_proxy_generation_seed_reproducibility(self):
        """Test that proxy generation with seed=42 is reproducible."""
        shape = (10, 20)
        mean = 0.0
        std = 1.0

        # Generate twice with same seed
        proxy1 = generate_proxy_weights(shape, seed=42, mean=mean, std=std)
        proxy2 = generate_proxy_weights(shape, seed=42, mean=mean, std=std)

        np.testing.assert_array_equal(proxy1, proxy2)

    def test_proxy_generation_different_seed(self):
        """Test that different seeds produce different results."""
        shape = (10, 20)

        proxy1 = generate_proxy_weights(shape, seed=42)
        proxy2 = generate_proxy_weights(shape, seed=123)

        with pytest.raises(AssertionError):
            np.testing.assert_array_equal(proxy1, proxy2)

    def test_proxy_generation_invalid_shape(self):
        """Test handling of invalid shape (e.g., 1D)."""
        with pytest.raises(ValueError):
            generate_proxy_weights((100,), seed=42)

    def test_proxy_generation_negative_std(self):
        """Test handling of negative standard deviation."""
        with pytest.raises(ValueError):
            generate_proxy_weights((10, 20), seed=42, std=-1.0)


class TestEdgeCasesEvaluation:
    """Tests for edge cases in evaluation."""

    def test_memory_check_within_limit(self):
        """Test memory check when usage is within limit."""
        # Mock memory usage below threshold
        with patch('psutil.Process') as MockProcess:
            mock_process = MagicMock()
            mock_process.memory_info.return_value.rss = 5 * 1024 * 1024 * 1024  # 5GB
            MockProcess.return_value = mock_process

            # Should not raise
            result = check_memory_usage(threshold_gb=6.5)
            assert result is True

    def test_memory_check_exceeds_limit(self):
        """Test memory check when usage exceeds limit."""
        with patch('psutil.Process') as MockProcess:
            mock_process = MagicMock()
            mock_process.memory_info.return_value.rss = 7 * 1024 * 1024 * 1024  # 7GB
            MockProcess.return_value = mock_process

            # Should raise
            with pytest.raises(MemoryError):
                check_memory_usage(threshold_gb=6.5)

    def test_memory_check_exact_limit(self):
        """Test memory check at exact limit."""
        with patch('psutil.Process') as MockProcess:
            mock_process = MagicMock()
            # 6.5 GB exactly
            mock_process.memory_info.return_value.rss = 6.5 * 1024 * 1024 * 1024
            MockProcess.return_value = mock_process

            # Should not raise (limit is exclusive or inclusive depending on impl)
            # Assuming inclusive based on "fail loudly if it exceeds 6.5"
            result = check_memory_usage(threshold_gb=6.5)
            assert result is True


class TestEdgeCasesVectorDB:
    """Tests for edge cases in vector database operations."""

    def test_load_empty_flattened_vectors(self):
        """Test loading an empty flattened vector file."""
        with tempfile.NamedTemporaryFile(suffix='.npz', delete=False) as tmp:
            np.savez(tmp.name, vectors=np.array([]).reshape(0, 10), metadata=[])
            tmp_path = tmp.name

        try:
            with pytest.raises(ValueError):
                load_flattened_vectors(tmp_path)
        finally:
            os.unlink(tmp_path)

    def test_load_corrupted_npz(self):
        """Test loading a corrupted .npz file."""
        with tempfile.NamedTemporaryFile(suffix='.npz', delete=False) as tmp:
            # Write invalid data
            tmp.write(b'This is not a valid npz file')
            tmp_path = tmp.name

        try:
            with pytest.raises(Exception):
                load_flattened_vectors(tmp_path)
        finally:
            os.unlink(tmp_path)

    def test_load_mismatched_metadata(self):
        """Test loading when metadata length doesn't match vector count."""
        with tempfile.NamedTemporaryFile(suffix='.npz', delete=False) as tmp:
            vectors = np.random.randn(5, 10)
            metadata = [{'id': '1'}, {'id': '2'}]  # Only 2 for 5 vectors
            np.savez(tmp.name, vectors=vectors, metadata=metadata)
            tmp_path = tmp.name

        try:
            # Should either raise or handle gracefully
            with pytest.raises(ValueError):
                load_flattened_vectors(tmp_path)
        finally:
            os.unlink(tmp_path)


class TestReconstructMatricesEdgeCases:
    """Tests for edge cases in matrix reconstruction."""

    def test_reconstruct_empty_flattened(self):
        """Test reconstructing matrices from empty flattened vector."""
        flattened = np.array([])
        shape_a = (0, 0)
        shape_b = (0, 0)

        with pytest.raises(ValueError):
            reconstruct_matrices(flattened, shape_a, shape_b)

    def test_reconstruct_mismatched_size(self):
        """Test reconstructing when flattened size doesn't match shapes."""
        flattened = np.random.randn(100)
        shape_a = (10, 10)  # 100
        shape_b = (5, 5)    # 25 -> Total 125, mismatch

        with pytest.raises(ValueError):
            reconstruct_matrices(flattened, shape_a, shape_b)

    def test_reconstruct_valid(self):
        """Test valid reconstruction."""
        shape_a = (10, 5)   # 50
        shape_b = (10, 5)   # 50
        total_size = 100
        flattened = np.random.randn(total_size)

        A, B = reconstruct_matrices(flattened, shape_a, shape_b)

        assert A.shape == shape_a
        assert B.shape == shape_b
        assert np.allclose(np.concatenate([A.flatten(), B.flatten()]), flattened)