"""
Unit tests for src.retrieval.strategies module.

Verifies the mathematical correctness of unweighted and weighted averaging
strategies for LoRA adapter synthesis.
"""
import os
import sys
import tempfile
import numpy as np
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.retrieval.strategies import (
    unweighted_mean,
    cosine_weighted_average,
    reconstruct_matrices,
    synthesize_adapter
)
from src.utils.config import get_project_root


class TestUnweightedMean:
    """Tests for the unweighted arithmetic mean strategy."""

    def test_single_vector_returns_same(self):
        """Unweighted mean of a single vector should return the vector itself."""
        vec = np.array([1.0, 2.0, 3.0, 4.0], dtype=np.float32)
        result = unweighted_mean([vec])
        np.testing.assert_array_almost_equal(result, vec)

    def test_two_vectors_average(self):
        """Unweighted mean of two vectors should be element-wise average."""
        v1 = np.array([1.0, 2.0, 3.0], dtype=np.float32)
        v2 = np.array([5.0, 6.0, 7.0], dtype=np.float32)
        expected = np.array([3.0, 4.0, 5.0], dtype=np.float32)
        result = unweighted_mean([v1, v2])
        np.testing.assert_array_almost_equal(result, expected)

    def test_three_vectors_average(self):
        """Unweighted mean of three vectors."""
        v1 = np.array([1.0, 1.0], dtype=np.float32)
        v2 = np.array([3.0, 3.0], dtype=np.float32)
        v3 = np.array([5.0, 5.0], dtype=np.float32)
        expected = np.array([3.0, 3.0], dtype=np.float32)
        result = unweighted_mean([v1, v2, v3])
        np.testing.assert_array_almost_equal(result, expected)

    def test_empty_list_raises(self):
        """Unweighted mean of an empty list should raise ValueError."""
        with pytest.raises(ValueError, match="Cannot compute mean of empty list"):
            unweighted_mean([])

    def test_dimension_mismatch_raises(self):
        """Unweighted mean of vectors with mismatched dimensions should raise ValueError."""
        v1 = np.array([1.0, 2.0], dtype=np.float32)
        v2 = np.array([1.0, 2.0, 3.0], dtype=np.float32)
        with pytest.raises(ValueError, match="All vectors must have the same dimension"):
            unweighted_mean([v1, v2])


class TestCosineWeightedAverage:
    """Tests for the cosine-weighted averaging strategy."""

    def test_perfect_similarity_weights(self):
        """If similarity is 1.0, weight should be normalized to 1.0."""
        vec = np.array([1.0, 0.0], dtype=np.float32)
        # Simulate a query vector identical to vec
        query = vec.copy()
        # Manually calculate expected weight: cosine similarity = 1.0
        # weight = sim / sum(sim) = 1.0 / 1.0 = 1.0
        result = cosine_weighted_average([vec], [1.0])
        np.testing.assert_array_almost_equal(result, vec)

    def test_zero_similarity_excluded(self):
        """Vectors with 0 similarity should contribute 0 weight."""
        v1 = np.array([1.0, 0.0], dtype=np.float32)
        v2 = np.array([0.0, 1.0], dtype=np.float32)
        # v1 has sim 1.0, v2 has sim 0.0 (orthogonal)
        result = cosine_weighted_average([v1, v2], [1.0, 0.0])
        # Should equal v1
        np.testing.assert_array_almost_equal(result, v1)

    def test_weighted_average_calculation(self):
        """Test actual weighted average calculation."""
        v1 = np.array([1.0, 0.0], dtype=np.float32)
        v2 = np.array([0.0, 1.0], dtype=np.float32)
        # Similarities: v1=0.8, v2=0.2
        # Weights: v1=0.8, v2=0.2
        # Result = 0.8 * v1 + 0.2 * v2 = [0.8, 0.2]
        result = cosine_weighted_average([v1, v2], [0.8, 0.2])
        expected = np.array([0.8, 0.2], dtype=np.float32)
        np.testing.assert_array_almost_equal(result, expected)

    def test_empty_similarities_raises(self):
        """Empty lists should raise ValueError."""
        with pytest.raises(ValueError, match="Vectors and similarities lists must be non-empty"):
            cosine_weighted_average([], [])

    def test_mismatched_lengths_raises(self):
        """Vectors and similarities lists of different lengths should raise ValueError."""
        v1 = np.array([1.0], dtype=np.float32)
        with pytest.raises(ValueError, match="Vectors and similarities lists must have the same length"):
            cosine_weighted_average([v1], [0.5, 0.5])

    def test_negative_similarities_handled(self):
        """Negative similarities should be treated as valid weights (though uncommon in cosine)."""
        v1 = np.array([1.0], dtype=np.float32)
        v2 = np.array([-1.0], dtype=np.float32)
        # Similarities: -0.5, 0.5 -> sum=0 -> this might cause division by zero or specific behavior
        # Let's test a case where sum is positive
        result = cosine_weighted_average([v1, v2], [-0.2, 0.8])
        # Weights: -0.2, 0.8 -> sum=0.6
        # Norm weights: -0.333, 1.333
        # Result = -0.333 * [1] + 1.333 * [-1] = [-1.666]
        # Note: Negative weights can lead to extrapolation. The function should handle math correctly.
        expected_weight_v1 = -0.2 / 0.6
        expected_weight_v2 = 0.8 / 0.6
        expected = expected_weight_v1 * v1 + expected_weight_v2 * v2
        np.testing.assert_array_almost_equal(result, expected)


class TestReconstructMatrices:
    """Tests for reconstructing A and B matrices from flattened vectors."""

    def test_roundtrip_flatten_reconstruct(self):
        """Flattening and reconstructing should return original matrices."""
        A_shape = (4, 8)
        B_shape = (8, 4)
        A = np.random.randn(*A_shape).astype(np.float32)
        B = np.random.randn(*B_shape).astype(np.float32)

        # Flatten and reconstruct
        flat_A = A.flatten()
        flat_B = B.flatten()
        # Note: reconstruct_matrices expects a single flattened vector containing both
        # based on typical LoRA flattening. Let's verify the implementation signature.
        # Assuming the function takes (flat_vector, A_shape, B_shape)
        
        # Simulate the combined flat vector
        combined_flat = np.concatenate([flat_A, flat_B])
        A_recon, B_recon = reconstruct_matrices(combined_flat, A_shape, B_shape)

        np.testing.assert_array_almost_equal(A, A_recon)
        np.testing.assert_array_almost_equal(B, B_recon)

    def test_shape_mismatch_raises(self):
        """Reconstructing with incorrect shapes should raise an error or return wrong size."""
        flat_vec = np.array([1.0, 2.0, 3.0, 4.0], dtype=np.float32)
        # Try to reconstruct into a shape that doesn't match the vector length
        with pytest.raises(ValueError, match="Vector length does not match"):
            reconstruct_matrices(flat_vec, (2, 2), (2, 2)) # 2*2 + 2*2 = 8, but vec has 4


class TestSynthesizeAdapter:
    """Integration tests for the full synthesis pipeline."""

    def test_synthesize_from_single_vector(self):
        """Synthesizing from a single vector should return that vector's matrices."""
        A_shape = (4, 8)
        B_shape = (8, 4)
        A = np.random.randn(*A_shape).astype(np.float32)
        B = np.random.randn(*B_shape).astype(np.float32)
        
        flat_A = A.flatten()
        flat_B = B.flatten()
        combined = np.concatenate([flat_A, flat_B])

        # Strategy: single nearest neighbor (effectively just the vector itself)
        A_out, B_out = synthesize_adapter([combined], [1.0], A_shape, B_shape, strategy="single")
        
        np.testing.assert_array_almost_equal(A, A_out)
        np.testing.assert_array_almost_equal(B, B_out)

    def test_synthesize_mean_strategy(self):
        """Synthesizing with mean strategy should produce average matrices."""
        A_shape = (2, 2)
        B_shape = (2, 2)
        
        A1 = np.array([[1.0, 0.0], [0.0, 1.0]], dtype=np.float32)
        B1 = np.array([[1.0, 0.0], [0.0, 1.0]], dtype=np.float32)
        
        A2 = np.array([[0.0, 1.0], [1.0, 0.0]], dtype=np.float32)
        B2 = np.array([[0.0, 1.0], [1.0, 0.0]], dtype=np.float32)

        flat_A1, flat_B1 = A1.flatten(), B1.flatten()
        flat_A2, flat_B2 = A2.flatten(), B2.flatten()
        
        v1 = np.concatenate([flat_A1, flat_B1])
        v2 = np.concatenate([flat_A2, flat_B2])

        # Mean strategy
        A_out, B_out = synthesize_adapter([v1, v2], [1.0, 1.0], A_shape, B_shape, strategy="mean")

        expected_A = (A1 + A2) / 2
        expected_B = (B1 + B2) / 2

        np.testing.assert_array_almost_equal(A_out, expected_A)
        np.testing.assert_array_almost_equal(B_out, expected_B)

    def test_synthesize_weighted_strategy(self):
        """Synthesizing with weighted strategy should produce weighted average matrices."""
        A_shape = (2, 2)
        B_shape = (2, 2)
        
        A1 = np.array([[2.0, 0.0], [0.0, 2.0]], dtype=np.float32)
        B1 = np.array([[2.0, 0.0], [0.0, 2.0]], dtype=np.float32)
        
        A2 = np.array([[0.0, 0.0], [0.0, 0.0]], dtype=np.float32)
        B2 = np.array([[0.0, 0.0], [0.0, 0.0]], dtype=np.float32)

        flat_A1, flat_B1 = A1.flatten(), B1.flatten()
        flat_A2, flat_B2 = A2.flatten(), B2.flatten()
        
        v1 = np.concatenate([flat_A1, flat_B1])
        v2 = np.concatenate([flat_A2, flat_B2])

        # Weights: 1.0 for v1, 0.0 for v2 -> result should be v1
        A_out, B_out = synthesize_adapter([v1, v2], [1.0, 0.0], A_shape, B_shape, strategy="weighted")

        np.testing.assert_array_almost_equal(A_out, A1)
        np.testing.assert_array_almost_equal(B_out, B1)

    def test_invalid_strategy_raises(self):
        """Passing an invalid strategy name should raise ValueError."""
        A_shape = (2, 2)
        B_shape = (2, 2)
        v1 = np.zeros(8, dtype=np.float32)
        
        with pytest.raises(ValueError, match="Unknown strategy"):
            synthesize_adapter([v1], [1.0], A_shape, B_shape, strategy="invalid_strategy")