import pytest
import numpy as np
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'code'))

from drift_scoring import compute_cosine_distance, load_centroids

class TestComputeCosineDistance:
    
    def test_identical_vectors(self):
        """Distance between identical unit vectors should be 0."""
        vec = np.array([1.0, 0.0, 0.0])
        centroids = {"cat1": np.array([1.0, 0.0, 0.0])}
        dist, cat = compute_cosine_distance(vec, centroids)
        assert np.isclose(dist, 0.0, atol=1e-5)
        assert cat == "cat1"

    def test_orthogonal_vectors(self):
        """Distance between orthogonal unit vectors should be 1.0."""
        vec = np.array([1.0, 0.0, 0.0])
        centroids = {"cat1": np.array([0.0, 1.0, 0.0])}
        dist, cat = compute_cosine_distance(vec, centroids)
        assert np.isclose(dist, 1.0, atol=1e-5)
        assert cat == "cat1"

    def test_opposite_vectors(self):
        """Distance between opposite unit vectors should be 2.0."""
        vec = np.array([1.0, 0.0, 0.0])
        centroids = {"cat1": np.array([-1.0, 0.0, 0.0])}
        dist, cat = compute_cosine_distance(vec, centroids)
        assert np.isclose(dist, 2.0, atol=1e-5)
        assert cat == "cat1"

    def test_multiple_centroids_selects_minimum(self):
        """Should select the centroid with the minimum distance."""
        vec = np.array([1.0, 0.0, 0.0])
        centroids = {
            "close": np.array([1.0, 0.0, 0.0]),
            "far": np.array([0.0, 1.0, 0.0])
        }
        dist, cat = compute_cosine_distance(vec, centroids)
        assert np.isclose(dist, 0.0, atol=1e-5)
        assert cat == "close"

    def test_empty_centroids_raises(self):
        """Should raise ValueError if centroids are empty."""
        vec = np.array([1.0, 0.0, 0.0])
        with pytest.raises(ValueError):
            compute_cosine_distance(vec, {})

    def test_empty_log_raises(self):
        """Should raise ValueError if log embedding is empty."""
        vec = np.array([])
        centroids = {"cat1": np.array([1.0, 0.0, 0.0])}
        with pytest.raises(ValueError):
            compute_cosine_distance(vec, centroids)

    def test_non_unit_vectors_normalized(self):
        """Should handle non-unit vectors correctly by normalizing."""
        vec = np.array([2.0, 0.0, 0.0])
        centroids = {"cat1": np.array([2.0, 0.0, 0.0])}
        dist, cat = compute_cosine_distance(vec, centroids)
        assert np.isclose(dist, 0.0, atol=1e-5)
        assert cat == "cat1"