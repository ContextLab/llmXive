"""
Unit tests for motif analysis performance and SC-002 compliance.
"""
import os
import json
import numpy as np
import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path

# Import the module
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))
from motifs import count_motifs, generate_null_model, compute_z_scores, timeout_wrapper
from config import MOTIF_TIMEOUT_SECONDS

@pytest.fixture
def small_adj_matrix():
    """Create a small 5x5 binary adjacency matrix for testing."""
    np.random.seed(42)
    adj = np.random.randint(0, 2, size=(5, 5))
    np.fill_diagonal(adj, 0)  # No self-loops
    return adj

@pytest.fixture
def medium_adj_matrix():
    """Create a medium 20x20 binary adjacency matrix for testing."""
    np.random.seed(42)
    adj = np.random.randint(0, 2, size=(20, 20))
    np.fill_diagonal(adj, 0)
    return adj

def test_count_motifs_small_graph(small_adj_matrix):
    """Test motif counting on a small graph."""
    counts = count_motifs(small_adj_matrix)
    assert isinstance(counts, dict)
    assert len(counts) > 0
    # All counts should be non-negative integers
    for count in counts.values():
        assert isinstance(count, int)
        assert count >= 0

def test_count_motifs_medium_graph(medium_adj_matrix):
    """Test motif counting on a medium graph."""
    counts = count_motifs(medium_adj_matrix)
    assert isinstance(counts, dict)
    assert len(counts) > 0

def test_generate_null_model(small_adj_matrix):
    """Test null model generation preserves degree distribution approximately."""
    null_counts = generate_null_model(small_adj_matrix, iterations=10)
    assert isinstance(null_counts, list)
    assert len(null_counts) == 10
    for nc in null_counts:
        assert isinstance(nc, dict)

def test_compute_z_scores(small_adj_matrix):
    """Test z-score computation."""
    observed = count_motifs(small_adj_matrix)
    null_counts = generate_null_model(small_adj_matrix, iterations=20)
    z_scores = compute_z_scores(observed, null_counts)
    
    assert isinstance(z_scores, dict)
    for motif_id, data in z_scores.items():
        assert 'z_score' in data
        assert 'count' in data
        assert isinstance(data['z_score'], float)
        assert isinstance(data['count'], int)

def test_timeout_wrapper():
    """Test that timeout wrapper enforces time limits."""
    def slow_func():
        import time
        time.sleep(2)
        return {"result": "success"}
    
    # This should timeout
    with pytest.raises(Exception):  # TimeoutError or similar
        timeout_wrapper(slow_func, timeout=0.5)()

def test_performance_on_medium_graph(medium_adj_matrix):
    """Test that motif counting completes within reasonable time."""
    import time
    start = time.time()
    counts = count_motifs(medium_adj_matrix)
    elapsed = time.time() - start
    
    # Should complete in < 10 seconds for a 20-node graph
    assert elapsed < 10.0, f"Motif counting took {elapsed:.2f}s, expected < 10s"

def test_empty_graph():
    """Test handling of empty graphs."""
    empty_adj = np.zeros((3, 3), dtype=int)
    counts = count_motifs(empty_adj)
    assert isinstance(counts, dict)
    assert len(counts) > 0
    # All counts should be 0
    for count in counts.values():
        assert count == 0

def test_complete_graph():
    """Test handling of complete directed graph."""
    complete_adj = np.ones((5, 5), dtype=int)
    np.fill_diagonal(complete_adj, 0)
    counts = count_motifs(complete_adj)
    assert isinstance(counts, dict)
    assert len(counts) > 0
    # Should have many motifs
    total = sum(counts.values())
    assert total > 0
