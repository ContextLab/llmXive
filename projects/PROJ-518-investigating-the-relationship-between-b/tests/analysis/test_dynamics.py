"""
Tests for dynamics analysis functions.
"""
import numpy as np
import pytest
from analysis.dynamics import detect_communities, calculate_flexibility

def test_detect_communities_returns_list():
    """Test that detect_communities returns a list of integers."""
    # Create a simple 5x5 correlation matrix
    np.random.seed(42)
    matrix = np.random.rand(5, 5)
    matrix = (matrix + matrix.T) / 2  # Symmetrize
    np.fill_diagonal(matrix, 1.0)
    
    communities = detect_communities(matrix)
    assert isinstance(communities, list)
    assert len(communities) == 5
    assert all(isinstance(c, int) for c in communities)

def test_detect_communities_gamma_parameter():
    """Test that gamma parameter is accepted (even if mock implementation)."""
    matrix = np.eye(4)
    communities_1 = detect_communities(matrix, gamma=1.0)
    communities_2 = detect_communities(matrix, gamma=0.5)
    # With a diagonal matrix, behavior might be deterministic regardless of gamma
    # in the fallback, but the function must accept the argument.
    assert len(communities_1) == 4
    assert len(communities_2) == 4

def test_calculate_flexibility_empty():
    """Test flexibility with empty input."""
    assert calculate_flexibility([]) == 0.0

def test_calculate_flexibility_single_window():
    """Test flexibility with a single window."""
    labels = [[0, 1, 2]]
    assert calculate_flexibility(labels) == 0.0

def test_calculate_flexibility_no_changes():
    """Test flexibility when no changes occur."""
    labels = [
        [0, 1, 2],
        [0, 1, 2],
        [0, 1, 2]
    ]
    assert calculate_flexibility(labels) == 0.0

def test_calculate_flexibility_max_changes():
    """Test flexibility when every node changes every window."""
    labels = [
        [0, 0, 0],
        [1, 1, 1],
        [0, 0, 0]
    ]
    # 2 windows of change, max possible is 2. Ratio = 1.0
    assert calculate_flexibility(labels) == 1.0