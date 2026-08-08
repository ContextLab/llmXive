"""
Unit tests for src.retrieval.strategies.

Verifies:
1. Unweighted arithmetic mean (k-top) averaging math.
2. Cosine-weighted averaging math.
3. Edge case handling (identical scores, single neighbor).
"""
import pytest
import numpy as np
from typing import List, Tuple

# Import the functions to test
from src.retrieval.strategies import (
    unweighted_mean_interpolation,
    cosine_weighted_interpolation,
    get_top_k_neighbors
)


class TestUnweightedMeanInterpolation:
    """Tests for the unweighted arithmetic mean strategy."""

    def test_single_vector_returns_normalized_copy(self):
        """If k=1, the result should be the normalized vector itself."""
        vec = np.array([3.0, 4.0], dtype=np.float32)
        # Normalize manually to expected
        expected = vec / np.linalg.norm(vec)
        
        # Mock neighbor data: (vector, similarity)
        neighbors = [(vec, 0.9)]
        
        result = unweighted_mean_interpolation(neighbors, k=1)
        
        np.testing.assert_array_almost_equal(result, expected, decimal=6)

    def test_two_orthogonal_vectors(self):
        """Average of two orthogonal unit vectors."""
        v1 = np.array([1.0, 0.0], dtype=np.float32)
        v2 = np.array([0.0, 1.0], dtype=np.float32)
        
        neighbors = [(v1, 0.5), (v2, 0.5)]
        
        result = unweighted_mean_interpolation(neighbors, k=2)
        
        # Expected: (v1 + v2) / 2, then normalized
        expected_unnorm = (v1 + v2) / 2.0
        expected = expected_unnorm / np.linalg.norm(expected_unnorm)
        
        np.testing.assert_array_almost_equal(result, expected, decimal=6)

    def test_k_limited_selection(self):
        """Only the top k neighbors should be used."""
        v1 = np.array([1.0, 0.0], dtype=np.float32)
        v2 = np.array([0.0, 1.0], dtype=np.float32)
        v3 = np.array([1.0, 1.0], dtype=np.float32) # Low similarity, should be ignored if k=2
        
        # v3 has lower similarity
        neighbors = [(v1, 0.9), (v2, 0.8), (v3, 0.1)]
        
        result = unweighted_mean_interpolation(neighbors, k=2)
        
        # Should only average v1 and v2
        expected_unnorm = (v1 + v2) / 2.0
        expected = expected_unnorm / np.linalg.norm(expected_unnorm)
        
        np.testing.assert_array_almost_equal(result, expected, decimal=6)

    def test_all_weights_equal(self):
        """Verify that weights are ignored in unweighted mean."""
        v1 = np.array([1.0, 0.0], dtype=np.float32)
        v2 = np.array([0.0, 1.0], dtype=np.float32)
        
        # Different similarities, but should be treated equally
        neighbors = [(v1, 0.99), (v2, 0.01)]
        
        result = unweighted_mean_interpolation(neighbors, k=2)
        
        expected_unnorm = (v1 + v2) / 2.0
        expected = expected_unnorm / np.linalg.norm(expected_unnorm)
        
        np.testing.assert_array_almost_equal(result, expected, decimal=6)


class TestCosineWeightedInterpolation:
    """Tests for the cosine-weighted averaging strategy."""

    def test_single_vector_returns_normalized_copy(self):
        """If k=1, result is the normalized vector."""
        vec = np.array([3.0, 4.0], dtype=np.float32)
        expected = vec / np.linalg.norm(vec)
        
        neighbors = [(vec, 0.9)]
        
        result = cosine_weighted_interpolation(neighbors, k=1)
        
        np.testing.assert_array_almost_equal(result, expected, decimal=6)

    def test_weighted_average_respects_similarity(self):
        """Higher similarity vector should dominate the average."""
        v1 = np.array([1.0, 0.0], dtype=np.float32)
        v2 = np.array([0.0, 1.0], dtype=np.float32)
        
        # v1 has much higher similarity
        neighbors = [(v1, 0.95), (v2, 0.05)]
        
        result = cosine_weighted_interpolation(neighbors, k=2)
        
        # Weights: w1 = 0.95, w2 = 0.05
        # Unnormalized sum = w1*v1 + w2*v2
        expected_unnorm = (0.95 * v1) + (0.05 * v2)
        expected = expected_unnorm / np.linalg.norm(expected_unnorm)
        
        np.testing.assert_array_almost_equal(result, expected, decimal=6)

    def test_identical_similarities_equals_unweighted(self):
        """If similarities are identical, result matches unweighted mean."""
        v1 = np.array([1.0, 0.0], dtype=np.float32)
        v2 = np.array([0.0, 1.0], dtype=np.float32)
        
        neighbors = [(v1, 0.5), (v2, 0.5)]
        
        result = cosine_weighted_interpolation(neighbors, k=2)
        
        # Unweighted mean result
        expected_unnorm = (v1 + v2) / 2.0
        expected = expected_unnorm / np.linalg.norm(expected_unnorm)
        
        np.testing.assert_array_almost_equal(result, expected, decimal=6)

    def test_normalization_applied_after_weighting(self):
        """Ensure the final output is L2 normalized."""
        v1 = np.array([1.0, 0.0], dtype=np.float32)
        v2 = np.array([0.0, 1.0], dtype=np.float32)
        
        neighbors = [(v1, 0.8), (v2, 0.2)]
        
        result = cosine_weighted_interpolation(neighbors, k=2)
        
        # Check L2 norm is 1.0
        norm = np.linalg.norm(result)
        assert np.isclose(norm, 1.0, atol=1e-6), f"Result norm is {norm}, expected 1.0"


class TestGetTopKNeighbors:
    """Tests for the neighbor selection utility."""

    def test_sorts_by_similarity_descending(self):
        """Neighbors should be sorted by similarity descending."""
        v1 = np.array([1.0], dtype=np.float32)
        v2 = np.array([2.0], dtype=np.float32)
        v3 = np.array([3.0], dtype=np.float32)
        
        neighbors = [(v1, 0.5), (v2, 0.9), (v3, 0.2)]
        
        result = get_top_k_neighbors(neighbors, k=2)
        
        # Expected order: v2 (0.9), v1 (0.5)
        assert result[0][0] is v2
        assert result[1][0] is v1

    def test_returns_all_if_k_larger_than_list(self):
        """Should return all available neighbors if k >= len."""
        v1 = np.array([1.0], dtype=np.float32)
        v2 = np.array([2.0], dtype=np.float32)
        
        neighbors = [(v1, 0.5), (v2, 0.9)]
        
        result = get_top_k_neighbors(neighbors, k=10)
        
        assert len(result) == 2

    def test_empty_list(self):
        """Should return empty list for empty input."""
        result = get_top_k_neighbors([], k=1)
        assert len(result) == 0