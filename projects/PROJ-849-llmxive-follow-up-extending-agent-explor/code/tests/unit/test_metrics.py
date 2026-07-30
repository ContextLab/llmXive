"""
Unit tests for metrics calculations.
"""
import pytest
import numpy as np
from lib.metrics import cosine_similarity_safe, compute_centroid

class TestCosineSimilaritySafe:
    def test_identical_vectors(self):
        v1 = np.array([1.0, 0.0, 0.0])
        v2 = np.array([1.0, 0.0, 0.0])
        assert cosine_similarity_safe(v1, v2) == 1.0

    def test_orthogonal_vectors(self):
        v1 = np.array([1.0, 0.0, 0.0])
        v2 = np.array([0.0, 1.0, 0.0])
        assert cosine_similarity_safe(v1, v2) == 0.0

    def test_zero_vector(self):
        v1 = np.array([0.0, 0.0, 0.0])
        v2 = np.array([1.0, 0.0, 0.0])
        assert cosine_similarity_safe(v1, v2) == 0.0

class TestComputeCentroid:
    def test_two_vectors(self):
        v1 = np.array([1.0, 0.0])
        v2 = np.array([3.0, 0.0])
        centroid = compute_centroid([v1, v2])
        expected = np.array([2.0, 0.0])
        assert np.allclose(centroid, expected)

    def test_empty_list(self):
        centroid = compute_centroid([])
        assert centroid.shape == (1,)
        assert centroid[0] == 0.0
