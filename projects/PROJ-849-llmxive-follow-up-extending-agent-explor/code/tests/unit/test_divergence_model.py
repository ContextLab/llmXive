"""
Unit tests for the DivergenceModel logic.

Tests the core functions: encode_text, compute_centroid, calculate_divergence_score.
"""

import pytest
import numpy as np
import sys
import os

# Add code directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'code'))

from lib.metrics import cosine_similarity_safe, compute_centroid
from src.models.divergence_model import (
    DivergenceModel, 
    DivergenceResult, 
    calculate_divergence_score, 
    compute_thinking_embedding,
    compute_tool_centroid_embedding
)
from src.models.divergence_model import DivergenceModelError

class TestDivergenceModelLogic:
    """Tests for the mathematical logic of the divergence model."""

    def test_cosine_similarity_identical_vectors(self):
        """Test that identical vectors have similarity 1.0."""
        vec = np.array([1.0, 2.0, 3.0])
        assert abs(cosine_similarity_safe(vec, vec) - 1.0) < 1e-6

    def test_cosine_similarity_orthogonal_vectors(self):
        """Test that orthogonal vectors have similarity 0.0."""
        vec_a = np.array([1.0, 0.0, 0.0])
        vec_b = np.array([0.0, 1.0, 0.0])
        assert abs(cosine_similarity_safe(vec_a, vec_b) - 0.0) < 1e-6

    def test_cosine_similarity_opposite_vectors(self):
        """Test that opposite vectors have similarity -1.0."""
        vec_a = np.array([1.0, 0.0, 0.0])
        vec_b = np.array([-1.0, 0.0, 0.0])
        assert abs(cosine_similarity_safe(vec_a, vec_b) - (-1.0)) < 1e-6

    def test_cosine_similarity_zero_vector(self):
        """Test that zero vector returns 0.0 similarity."""
        vec_a = np.array([0.0, 0.0, 0.0])
        vec_b = np.array([1.0, 2.0, 3.0])
        assert cosine_similarity_safe(vec_a, vec_b) == 0.0

    def test_compute_centroid_single_vector(self):
        """Test centroid of a single vector is the vector itself."""
        vec = np.array([1.0, 2.0, 3.0])
        centroid = compute_centroid([vec])
        np.testing.assert_array_almost_equal(centroid, vec)

    def test_compute_centroid_multiple_vectors(self):
        """Test centroid calculation for multiple vectors."""
        vecs = [
            np.array([2.0, 2.0, 2.0]),
            np.array([4.0, 4.0, 4.0])
        ]
        centroid = compute_centroid(vecs)
        expected = np.array([3.0, 3.0, 3.0])
        np.testing.assert_array_almost_equal(centroid, expected)

    def test_calculate_divergence_score(self):
        """Test the divergence score calculation."""
        # Perfect match -> similarity 1.0 -> divergence 0.0
        vec_a = np.array([1.0, 0.0])
        vec_b = np.array([1.0, 0.0])
        sim, div = calculate_divergence_score(vec_a, vec_b)
        assert abs(sim - 1.0) < 1e-6
        assert abs(div - 0.0) < 1e-6

        # Orthogonal -> similarity 0.0 -> divergence 1.0
        vec_c = np.array([0.0, 1.0])
        sim, div = calculate_divergence_score(vec_a, vec_c)
        assert abs(sim - 0.0) < 1e-6
        assert abs(div - 1.0) < 1e-6

    def test_process_problem_missing_thinking(self):
        """Test that missing thinking text raises an error."""
        problem = {"problem_id": "123", "data": "some data"}
        with pytest.raises(DivergenceModelError, match="Missing thinking text"):
            compute_thinking_embedding(problem)

    def test_process_problem_empty_tools(self):
        """Test that empty tool list returns zero centroid."""
        centroid = compute_tool_centroid_embedding([])
        assert centroid.shape == (768,)
        assert np.allclose(centroid, 0.0)