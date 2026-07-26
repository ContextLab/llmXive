import pytest
import numpy as np
from lib.metrics import cosine_similarity_safe, compute_centroid

class TestCosineSimilaritySafe:
    def test_identical_vectors(self):
        v1 = np.array([1.0, 0.0, 0.0])
        v2 = np.array([1.0, 0.0, 0.0])
        assert abs(cosine_similarity_safe(v1, v2) - 1.0) < 1e-6

    def test_orthogonal_vectors(self):
        v1 = np.array([1.0, 0.0, 0.0])
        v2 = np.array([0.0, 1.0, 0.0])
        assert abs(cosine_similarity_safe(v1, v2)) < 1e-6

    def test_opposite_vectors(self):
        v1 = np.array([1.0, 0.0, 0.0])
        v2 = np.array([-1.0, 0.0, 0.0])
        assert abs(cosine_similarity_safe(v1, v2) - (-1.0)) < 1e-6

    def test_zero_vector(self):
        v1 = np.array([0.0, 0.0, 0.0])
        v2 = np.array([1.0, 0.0, 0.0])
        assert cosine_similarity_safe(v1, v2) == 0.0

class TestComputeCentroid:
    def test_centroid_two_vectors(self):
        v1 = np.array([2.0, 2.0])
        v2 = np.array([4.0, 4.0])
        centroid = compute_centroid([v1, v2])
        expected = np.array([3.0, 3.0])
        assert np.allclose(centroid, expected)

    def test_centroid_empty_list(self):
        assert compute_centroid([]) is None

    def test_centroid_single_vector(self):
        v1 = np.array([5.0, 5.0])
        centroid = compute_centroid([v1])
        assert np.allclose(centroid, v1)
