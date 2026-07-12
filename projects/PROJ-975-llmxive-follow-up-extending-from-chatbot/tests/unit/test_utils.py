"""
Unit tests for utils module - embedding and similarity functions.
"""
import os
import sys
import pytest
import numpy as np

# Add code directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))

from utils import cosine_similarity, variance, std_dev, mean_pairwise_similarity

def test_cosine_similarity_identical():
    """Test cosine similarity of identical vectors is 1.0."""
    vec = np.array([1.0, 2.0, 3.0])
    assert abs(cosine_similarity(vec, vec) - 1.0) < 1e-6

def test_cosine_similarity_opposite():
    """Test cosine similarity of opposite vectors is -1.0."""
    vec1 = np.array([1.0, 2.0, 3.0])
    vec2 = np.array([-1.0, -2.0, -3.0])
    assert abs(cosine_similarity(vec1, vec2) + 1.0) < 1e-6

def test_cosine_similarity_orthogonal():
    """Test cosine similarity of orthogonal vectors is 0.0."""
    vec1 = np.array([1.0, 0.0, 0.0])
    vec2 = np.array([0.0, 1.0, 0.0])
    assert abs(cosine_similarity(vec1, vec2)) < 1e-6

def test_variance_basic():
    """Test variance calculation."""
    values = [1.0, 2.0, 3.0, 4.0, 5.0]
    result = variance(values)
    expected = 2.5  # Population variance with ddof=1
    assert abs(result - expected) < 1e-6

def test_variance_constant():
    """Test variance of constant values is 0."""
    values = [5.0, 5.0, 5.0, 5.0]
    assert variance(values) == 0.0

def test_std_dev_basic():
    """Test standard deviation calculation."""
    values = [1.0, 2.0, 3.0, 4.0, 5.0]
    result = std_dev(values)
    expected = np.sqrt(2.5)
    assert abs(result - expected) < 1e-6

def test_mean_pairwise_similarity_basic():
    """Test mean pairwise similarity calculation."""
    # Create orthogonal vectors
    vecs = [
        np.array([1.0, 0.0, 0.0]),
        np.array([0.0, 1.0, 0.0]),
        np.array([0.0, 0.0, 1.0])
    ]
    result = mean_pairwise_similarity(vecs)
    # All pairs are orthogonal, so mean should be ~0
    assert abs(result) < 1e-6

def test_mean_pairwise_similarity_single():
    """Test mean pairwise similarity with single vector returns 0."""
    vecs = [np.array([1.0, 2.0, 3.0])]
    assert mean_pairwise_similarity(vecs) == 0.0