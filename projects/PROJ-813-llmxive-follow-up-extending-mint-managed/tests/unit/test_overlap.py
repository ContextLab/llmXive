"""
Unit tests for compute_overlap.py (T015).

Tests:
1. Normalization logic: verify mapping [-1, 1] -> [0, 1].
2. Symmetry: similarity matrix must be symmetric.
3. Diagonal: self-similarity must be 1.0 (normalized).
"""

import numpy as np
import pytest
from scipy.spatial.distance import cdist

from code.data.compute_overlap import (
    compute_cosine_similarity_matrix,
    normalize_similarity_matrix,
)


def test_normalize_range():
    """Test that normalization maps [-1, 1] to [0, 1]."""
    # Test boundary values
    test_cases = [
        (-1.0, 0.0),
        (0.0, 0.5),
        (1.0, 1.0),
        (-0.5, 0.25),
        (0.5, 0.75),
    ]

    for sim, expected_norm in test_cases:
        result = normalize_similarity_matrix(np.array([[sim]]))
        assert np.isclose(result[0, 0], expected_norm), f"Failed for {sim} -> {result[0,0]}"


def test_normalize_matrix():
    """Test normalization on a small matrix."""
    sim_matrix = np.array([
        [1.0, 0.5, -1.0],
        [0.5, 1.0, 0.0],
        [-1.0, 0.0, 1.0]
    ])

    normalized = normalize_similarity_matrix(sim_matrix)

    expected = np.array([
        [1.0, 0.75, 0.0],
        [0.75, 1.0, 0.5],
        [0.0, 0.5, 1.0]
    ])

    assert np.allclose(normalized, expected)


def test_cosine_similarity_symmetry():
    """Test that cosine similarity matrix is symmetric."""
    # Create random vectors
    np.random.seed(42)
    params = np.random.rand(5, 10)

    sim_matrix = compute_cosine_similarity_matrix(params)

    # Check symmetry
    assert np.allclose(sim_matrix, sim_matrix.T), "Cosine similarity matrix is not symmetric"


def test_cosine_similarity_diagonal():
    """Test that diagonal elements (self-similarity) are 1.0."""
    np.random.seed(42)
    params = np.random.rand(5, 10)

    sim_matrix = compute_cosine_similarity_matrix(params)

    # Diagonal should be 1.0
    assert np.allclose(np.diag(sim_matrix), 1.0), "Self-similarity should be 1.0"


def test_normalize_preserves_symmetry():
    """Test that normalization preserves symmetry."""
    np.random.seed(42)
    params = np.random.rand(5, 10)

    sim_matrix = compute_cosine_similarity_matrix(params)
    normalized = normalize_similarity_matrix(sim_matrix)

    assert np.allclose(normalized, normalized.T), "Normalized matrix is not symmetric"