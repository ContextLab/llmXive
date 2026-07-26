"""
Unit tests for metric computation functions.
"""
import pytest
import numpy as np
from lib.metrics import cosine_similarity_safe, compute_centroid

def test_cosine_similarity_identical_vectors():
    """Test cosine similarity for identical vectors."""
    vec1 = np.array([1.0, 2.0, 3.0])
    vec2 = np.array([1.0, 2.0, 3.0])
    
    similarity = cosine_similarity_safe(vec1, vec2)
    assert np.isclose(similarity, 1.0, atol=1e-6)

def test_cosine_similarity_orthogonal_vectors():
    """Test cosine similarity for orthogonal vectors."""
    vec1 = np.array([1.0, 0.0, 0.0])
    vec2 = np.array([0.0, 1.0, 0.0])
    
    similarity = cosine_similarity_safe(vec1, vec2)
    assert np.isclose(similarity, 0.0, atol=1e-6)

def test_cosine_similarity_zero_vector():
    """Test cosine similarity with zero vector."""
    vec1 = np.array([0.0, 0.0, 0.0])
    vec2 = np.array([1.0, 2.0, 3.0])
    
    similarity = cosine_similarity_safe(vec1, vec2)
    assert similarity == 0.0

def test_compute_centroid_single_vector():
    """Test centroid computation with single vector."""
    vectors = [np.array([1.0, 2.0, 3.0])]
    centroid = compute_centroid(vectors)
    
    assert np.allclose(centroid, [1.0, 2.0, 3.0])

def test_compute_centroid_multiple_vectors():
    """Test centroid computation with multiple vectors."""
    vectors = [
        np.array([1.0, 0.0, 0.0]),
        np.array([0.0, 1.0, 0.0]),
        np.array([0.0, 0.0, 1.0])
    ]
    centroid = compute_centroid(vectors)
    
    expected = np.array([1/3, 1/3, 1/3])
    assert np.allclose(centroid, expected)

def test_compute_centroid_empty_list():
    """Test centroid computation with empty list."""
    centroid = compute_centroid([])
    assert centroid is None
