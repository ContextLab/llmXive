"""
Unit tests for edge cases in the llmXive pipeline.
Covers: empty inputs, dimension mismatches, NaN/Inf values,
single-item inputs, and boundary conditions for k-NN.
"""
import os
import sys
import tempfile
import numpy as np
import pytest
from pathlib import Path

# Import from existing API surface
from src.retrieval.strategies import (
    single_nearest_neighbor,
    unweighted_mean,
    cosine_weighted_average,
    reconstruct_matrices,
    load_skill_index,
)
from src.retrieval.vector_db import load_flattened_vectors
from src.validation.reconstruction_error import cosine_distance, load_npz_safe
from src.utils.config import get_project_root, ensure_directories


class TestEmptyInputs:
    """Tests for handling empty inputs."""

    def test_empty_skill_index(self):
        """Test that single_nearest_neighbor raises error on empty index."""
        with pytest.raises(ValueError, match="Skill index is empty"):
            single_nearest_neighbor(np.array([]), np.array([]), {}, 1)

    def test_empty_query_vector(self):
        """Test that strategies handle empty query vector."""
        skill_vectors = np.random.rand(5, 100).astype(np.float32)
        metadata = [{"id": f"skill_{i}"} for i in range(5)]

        with pytest.raises(ValueError, match="Query vector is empty"):
            single_nearest_neighbor(skill_vectors, np.array([]), metadata, 1)

    def test_empty_list_for_mean(self):
        """Test unweighted_mean with empty list."""
        with pytest.raises(ValueError, match="Cannot compute mean of empty list"):
            unweighted_mean([], np.array([]), {})

class TestDimensionMismatches:
    """Tests for dimension mismatch handling."""

    def test_query_vector_dimension_mismatch(self):
        """Test that dimension mismatch raises ValueError."""
        skill_vectors = np.random.rand(5, 100).astype(np.float32)
        query_vector = np.random.rand(50).astype(np.float32)  # Wrong dimension
        metadata = [{"id": f"skill_{i}"} for i in range(5)]

        with pytest.raises(ValueError, match="Dimension mismatch"):
            single_nearest_neighbor(skill_vectors, query_vector, metadata, 1)

    def test_reconstruct_dimension_mismatch(self):
        """Test reconstruct_matrices with mismatched A/B dimensions."""
        A = np.random.rand(10, 5).astype(np.float32)
        B = np.random.rand(7, 10).astype(np.float32)  # Mismatched

        with pytest.raises(ValueError, match="Dimension mismatch in A and B"):
            reconstruct_matrices(A, B)

class TestNaNInfValues:
    """Tests for handling NaN and Inf values."""

    def test_nan_in_query_vector(self):
        """Test that NaN in query vector raises error."""
        skill_vectors = np.random.rand(5, 100).astype(np.float32)
        query_vector = np.full(100, np.nan, dtype=np.float32)
        metadata = [{"id": f"skill_{i}"} for i in range(5)]

        with pytest.raises(ValueError, match="Query vector contains NaN or Inf"):
            single_nearest_neighbor(skill_vectors, query_vector, metadata, 1)

    def test_inf_in_skill_index(self):
        """Test that Inf in skill index raises error."""
        skill_vectors = np.random.rand(5, 100).astype(np.float32)
        skill_vectors[0] = np.inf
        query_vector = np.random.rand(100).astype(np.float32)
        metadata = [{"id": f"skill_{i}"} for i in range(5)]

        with pytest.raises(ValueError, match="Skill index contains NaN or Inf"):
            single_nearest_neighbor(skill_vectors, query_vector, metadata, 1)

    def test_cosine_distance_with_nan(self):
        """Test cosine_distance with NaN values."""
        v1 = np.array([1.0, 2.0, np.nan])
        v2 = np.array([1.0, 2.0, 3.0])

        with pytest.raises(ValueError, match="Input vectors contain NaN or Inf"):
            cosine_distance(v1, v2)

    def test_cosine_distance_with_inf(self):
        """Test cosine_distance with Inf values."""
        v1 = np.array([1.0, 2.0, np.inf])
        v2 = np.array([1.0, 2.0, 3.0])

        with pytest.raises(ValueError, match="Input vectors contain NaN or Inf"):
            cosine_distance(v1, v2)

class TestSingleItemInputs:
    """Tests for single-item inputs."""

    def test_single_skill_k1(self):
        """Test single nearest neighbor with exactly one skill."""
        skill_vectors = np.random.rand(1, 100).astype(np.float32)
        query_vector = np.random.rand(100).astype(np.float32)
        metadata = [{"id": "single_skill"}]

        idx, similarity = single_nearest_neighbor(skill_vectors, query_vector, metadata, 1)
        assert idx == 0
        assert 0 <= similarity <= 1

    def test_single_skill_k_greater_than_available(self):
        """Test k > available skills."""
        skill_vectors = np.random.rand(3, 100).astype(np.float32)
        query_vector = np.random.rand(100).astype(np.float32)
        metadata = [{"id": f"skill_{i}"} for i in range(3)]

        # Should return all 3 skills when k=10
        idxs, similarities = single_nearest_neighbor(skill_vectors, query_vector, metadata, 10)
        assert len(idxs) == 3
        assert len(similarities) == 3

    def test_unweighted_mean_single_item(self):
        """Test unweighted_mean with single item."""
        vectors = [np.random.rand(100).astype(np.float32)]
        result = unweighted_mean(vectors, np.zeros(100), {})
        assert np.allclose(result, vectors[0])

    def test_cosine_weighted_single_item(self):
        """Test cosine_weighted_average with single item."""
        vectors = [np.random.rand(100).astype(np.float32)]
        similarities = [0.9]
        result = cosine_weighted_average(vectors, similarities, np.zeros(100), {})
        # Should be normalized version of the single vector
        assert result.shape == vectors[0].shape

class TestBoundaryConditions:
    """Tests for boundary conditions."""

    def test_k_equals_one(self):
        """Test k=1 explicitly."""
        skill_vectors = np.random.rand(5, 100).astype(np.float32)
        query_vector = np.random.rand(100).astype(np.float32)
        metadata = [{"id": f"skill_{i}"} for i in range(5)]

        idx, similarity = single_nearest_neighbor(skill_vectors, query_vector, metadata, 1)
        assert isinstance(idx, (int, np.integer))
        assert 0 <= idx < 5

    def test_k_equals_total_skills(self):
        """Test k equals total number of skills."""
        n_skills = 5
        skill_vectors = np.random.rand(n_skills, 100).astype(np.float32)
        query_vector = np.random.rand(100).astype(np.float32)
        metadata = [{"id": f"skill_{i}"} for i in range(n_skills)]

        idxs, similarities = single_nearest_neighbor(
            skill_vectors, query_vector, metadata, n_skills
        )
        assert len(idxs) == n_skills
        assert len(similarities) == n_skills
        # All indices should be unique
        assert len(set(idxs)) == n_skills

    def test_zero_similarity(self):
        """Test when query is orthogonal to all skills."""
        # Create orthogonal vectors
        skill_vectors = np.eye(100, dtype=np.float32)[:5]  # 5 orthogonal unit vectors
        query_vector = np.zeros(100, dtype=np.float32)
        # Normalize query to avoid zero vector error
        query_vector = np.ones(100, dtype=np.float32) / np.sqrt(100)

        metadata = [{"id": f"skill_{i}"} for i in range(5)]
        idxs, similarities = single_nearest_neighbor(skill_vectors, query_vector, metadata, 5)

        # Similarities should be non-negative (cosine similarity)
        assert all(s >= -1e-6 for s in similarities)  # Small tolerance for float errors

    def test_identical_vectors(self):
        """Test when all skill vectors are identical."""
        identical_vector = np.random.rand(100).astype(np.float32)
        skill_vectors = np.tile(identical_vector, (5, 1))
        query_vector = identical_vector.copy()
        metadata = [{"id": f"skill_{i}"} for i in range(5)]

        idxs, similarities = single_nearest_neighbor(skill_vectors, query_vector, metadata, 5)
        # All similarities should be 1.0 (or very close)
        assert all(abs(s - 1.0) < 1e-5 for s in similarities)

    def test_negative_k(self):
        """Test that negative k raises error."""
        skill_vectors = np.random.rand(5, 100).astype(np.float32)
        query_vector = np.random.rand(100).astype(np.float32)
        metadata = [{"id": f"skill_{i}"} for i in range(5)]

        with pytest.raises(ValueError, match="k must be positive"):
            single_nearest_neighbor(skill_vectors, query_vector, metadata, -1)

    def test_zero_k(self):
        """Test that k=0 raises error."""
        skill_vectors = np.random.rand(5, 100).astype(np.float32)
        query_vector = np.random.rand(100).astype(np.float32)
        metadata = [{"id": f"skill_{i}"} for i in range(5)]

        with pytest.raises(ValueError, match="k must be positive"):
            single_nearest_neighbor(skill_vectors, query_vector, metadata, 0)

class TestLoadNpzSafeEdgeCases:
    """Tests for load_npz_safe edge cases."""

    def test_load_npz_with_zero_size_array(self):
        """Test loading NPZ with zero-size array."""
        with tempfile.NamedTemporaryFile(suffix='.npz', delete=False) as tmp:
            np.savez(tmp.name, empty_array=np.array([]))
            tmp_path = Path(tmp.name)

        try:
            data = load_npz_safe(tmp_path)
            assert 'empty_array' in data
            assert data['empty_array'].shape == (0,)
        finally:
            tmp_path.unlink()

    def test_load_npz_with_multidimensional_array(self):
        """Test loading NPZ with multi-dimensional array."""
        with tempfile.NamedTemporaryFile(suffix='.npz', delete=False) as tmp:
            np.savez(tmp.name, matrix=np.random.rand(5, 5, 5))
            tmp_path = Path(tmp.name)

        try:
            data = load_npz_safe(tmp_path)
            assert 'matrix' in data
            assert data['matrix'].shape == (5, 5, 5)
        finally:
            tmp_path.unlink()

class TestReconstructMatricesEdgeCases:
    """Tests for reconstruct_matrices edge cases."""

    def test_reconstruct_with_small_matrices(self):
        """Test reconstruction with minimal valid dimensions."""
        A = np.random.rand(2, 2).astype(np.float32)
        B = np.random.rand(2, 2).astype(np.float32)

        result = reconstruct_matrices(A, B)
        assert result.shape == (2, 2)

    def test_reconstruct_preserves_dtype(self):
        """Test that reconstruction preserves float32."""
        A = np.random.rand(10, 5).astype(np.float32)
        B = np.random.rand(5, 10).astype(np.float32)

        result = reconstruct_matrices(A, B)
        assert result.dtype == np.float32

    def test_reconstruct_with_very_small_values(self):
        """Test reconstruction with very small values."""
        A = np.random.rand(10, 5).astype(np.float32) * 1e-10
        B = np.random.rand(5, 10).astype(np.float32) * 1e-10

        result = reconstruct_matrices(A, B)
        assert not np.any(np.isnan(result))
        assert not np.any(np.isinf(result))

class TestUnweightedMeanEdgeCases:
    """Tests for unweighted_mean edge cases."""

    def test_unweighted_mean_with_two_identical_vectors(self):
        """Test mean of two identical vectors."""
        v = np.random.rand(100).astype(np.float32)
        result = unweighted_mean([v, v], np.zeros(100), {})
        assert np.allclose(result, v)

    def test_unweighted_mean_with_orthogonal_vectors(self):
        """Test mean of orthogonal vectors."""
        v1 = np.array([1.0, 0.0] * 50, dtype=np.float32)
        v2 = np.array([0.0, 1.0] * 50, dtype=np.float32)
        result = unweighted_mean([v1, v2], np.zeros(100), {})
        expected = (v1 + v2) / 2
        assert np.allclose(result, expected)

    def test_unweighted_mean_with_negative_values(self):
        """Test mean with negative values."""
        v1 = np.random.rand(100).astype(np.float32) - 0.5  # Range [-0.5, 0.5]
        v2 = np.random.rand(100).astype(np.float32) - 0.5
        result = unweighted_mean([v1, v2], np.zeros(100), {})
        expected = (v1 + v2) / 2
        assert np.allclose(result, expected)

class TestCosineWeightedAverageEdgeCases:
    """Tests for cosine_weighted_average edge cases."""

    def test_cosine_weighted_with_equal_similarities(self):
        """Test weighted average with equal similarities."""
        v1 = np.random.rand(100).astype(np.float32)
        v2 = np.random.rand(100).astype(np.float32)
        similarities = [0.5, 0.5]
        result = cosine_weighted_average([v1, v2], similarities, np.zeros(100), {})
        # Should be equivalent to unweighted mean (normalized)
        expected_unweighted = (v1 + v2) / 2
        expected_normalized = expected_unweighted / (np.linalg.norm(expected_unweighted) + 1e-8)
        assert np.allclose(result, expected_normalized)

    def test_cosine_weighted_with_zero_similarity(self):
        """Test weighted average with zero similarity."""
        v1 = np.random.rand(100).astype(np.float32)
        v2 = np.random.rand(100).astype(np.float32)
        similarities = [0.0, 0.0]
        # Should handle zero similarities gracefully (return zero vector or handle edge case)
        result = cosine_weighted_average([v1, v2], similarities, np.zeros(100), {})
        # At least should not raise error
        assert result.shape == (100,)
        assert not np.any(np.isnan(result))

    def test_cosine_weighted_with_one_high_similarity(self):
        """Test weighted average dominated by one high similarity."""
        v1 = np.random.rand(100).astype(np.float32)
        v2 = np.random.rand(100).astype(np.float32)
        similarities = [0.99, 0.01]
        result = cosine_weighted_average([v1, v2], similarities, np.zeros(100), {})
        # Result should be closer to v1 (normalized)
        v1_normalized = v1 / (np.linalg.norm(v1) + 1e-8)
        # Cosine similarity between result and v1 should be high
        sim_to_v1 = cosine_distance(result, v1_normalized)
        assert sim_to_v1 < 0.1  # High similarity means low distance