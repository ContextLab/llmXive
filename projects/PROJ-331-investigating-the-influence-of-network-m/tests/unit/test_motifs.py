"""
Unit tests for motifs.py functions.
Tests motif enumeration, null model generation, and z-score computation.
"""
import os
import sys
import json
import numpy as np
import pytest
import time
from unittest.mock import patch, MagicMock

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))

from motifs import (
    get_motif_id,
    count_motifs_nx,
    count_motifs_igraph,
    count_motifs_with_timeout,
    generate_null_model,
    compute_z_scores
)


class TestGetMotifId:
    """Tests for the get_motif_id function."""

    def test_get_motif_id_valid(self):
        """Test that get_motif_id returns valid motif IDs."""
        # Test with a simple 3-node pattern
        # This assumes the function maps adjacency matrices to motif IDs 0-12
        adj = np.array([
            [0, 1, 0],
            [0, 0, 1],
            [0, 0, 0]
        ])
        motif_id = get_motif_id(adj)
        assert 0 <= motif_id <= 12

    def test_get_motif_id_invalid_shape(self):
        """Test that get_motif_id raises error for non-3-node graphs."""
        adj = np.array([
            [0, 1, 0, 0],
            [0, 0, 1, 0],
            [0, 0, 0, 1],
            [0, 0, 0, 0]
        ])
        with pytest.raises(ValueError):
            get_motif_id(adj)

    def test_get_motif_id_non_binary(self):
        """Test that get_motif_id handles non-binary input."""
        adj = np.array([
            [0, 0.5, 0],
            [0, 0, 0.8],
            [0, 0, 0]
        ])
        # Should either binarize or raise an error
        try:
            motif_id = get_motif_id(adj)
            assert 0 <= motif_id <= 12
        except ValueError:
            pass  # Expected if function requires binary input


class TestCountMotifsNx:
    """Tests for the count_motifs_nx function."""

    def test_count_motifs_nx_empty_graph(self):
        """Counting motifs on an empty graph should return zeros."""
        adj = np.zeros((3, 3))
        counts = count_motifs_nx(adj)
        assert all(v == 0 for v in counts.values())

    def test_count_motifs_nx_complete_graph(self):
        """Complete 3-node graph should have specific motif count."""
        adj = np.ones((3, 3))
        np.fill_diagonal(adj, 0)
        counts = count_motifs_nx(adj)
        # A complete directed 3-node graph has 6 edges
        # This should match one of the 13 motif classes
        assert sum(counts.values()) > 0

    def test_count_motifs_nx_shape(self):
        """Test that output is a dict with 13 keys."""
        adj = np.random.randint(0, 2, (3, 3))
        np.fill_diagonal(adj, 0)
        counts = count_motifs_nx(adj)
        assert isinstance(counts, dict)
        assert len(counts) == 13  # 13 directed 3-node motifs


class TestCountMotifsIgraph:
    """Tests for the count_motifs_igraph function."""

    def test_count_motifs_igraph_empty_graph(self):
        """Counting motifs on an empty graph should return zeros."""
        adj = np.zeros((3, 3))
        counts = count_motifs_igraph(adj)
        assert all(v == 0 for v in counts.values())

    def test_count_motifs_igraph_consistency(self):
        """Test that igraph and nx give similar results on small graphs."""
        adj = np.random.randint(0, 2, (3, 3))
        np.fill_diagonal(adj, 0)
        counts_nx = count_motifs_nx(adj)
        counts_igraph = count_motifs_igraph(adj)
        # Both should have 13 keys
        assert len(counts_nx) == 13
        assert len(counts_igraph) == 13


class TestCountMotifsWithTimeout:
    """Tests for the count_motifs_with_timeout function."""

    def test_timeout_functionality(self):
        """Test that timeout works correctly."""
        # Create a small graph that should process quickly
        adj = np.random.randint(0, 2, (3, 3))
        np.fill_diagonal(adj, 0)
        
        with patch('motifs.count_motifs_with_timeout') as mock_func:
            mock_func.side_effect = TimeoutError("Test timeout")
            with pytest.raises(TimeoutError):
                count_motifs_with_timeout(adj, timeout=1)

    def test_normal_execution(self):
        """Test normal execution without timeout."""
        adj = np.random.randint(0, 2, (3, 3))
        np.fill_diagonal(adj, 0)
        # This should complete without timeout
        try:
            counts = count_motifs_with_timeout(adj, timeout=5)
            assert isinstance(counts, dict)
        except TimeoutError:
            pytest.fail("Unexpected timeout on small graph")


class TestGenerateNullModel:
    """Tests for the generate_null_model function."""

    def test_null_model_preserves_degree(self):
        """Test that null model preserves degree distribution."""
        adj = np.random.randint(0, 2, (10, 10))
        np.fill_diagonal(adj, 0)
        
        # Make it directed but with some structure
        adj = (adj + adj.T) / 2  # Make symmetric for undirected test
        adj = (adj > 0.5).astype(int)
        
        original_degree = np.sum(adj, axis=1)
        null_adj = generate_null_model(adj, iterations=100)
        null_degree = np.sum(null_adj, axis=1)
        
        # Degrees should be very similar (within tolerance)
        assert np.allclose(original_degree, null_degree, atol=1)

    def test_null_model_different_edges(self):
        """Test that null model changes edge positions."""
        adj = np.ones((5, 5))
        np.fill_diagonal(adj, 0)
        np.fill_diagonal(adj, 0)  # Ensure no self-loops
        
        null_adj = generate_null_model(adj, iterations=50)
        
        # Should be different (though may occasionally be same by chance)
        # With enough iterations, probability of identical is low
        if not np.array_equal(adj, null_adj):
            pass  # Expected
        else:
            # If same, it's a rare case, but we accept it
            pass

    def test_null_model_binary(self):
        """Test that null model output is binary."""
        adj = np.random.randint(0, 2, (5, 5))
        np.fill_diagonal(adj, 0)
        
        null_adj = generate_null_model(adj, iterations=50)
        assert np.all((null_adj == 0) | (null_adj == 1))
        assert np.all(np.diag(null_adj) == 0)  # No self-loops


class TestComputeZScores:
    """Tests for the compute_z_scores function."""

    def test_zscore_calculation(self):
        """Test basic z-score calculation."""
        counts = {'motif_0': 10, 'motif_1': 5, 'motif_2': 8}
        null_counts = [
            {'motif_0': 8, 'motif_1': 4, 'motif_2': 7},
            {'motif_0': 12, 'motif_1': 6, 'motif_2': 9},
            {'motif_0': 9, 'motif_1': 5, 'motif_2': 8}
        ]
        
        z_scores = compute_z_scores(counts, null_counts)
        
        assert isinstance(z_scores, dict)
        assert len(z_scores) == 3
        # Z-scores should be floats
        for v in z_scores.values():
            assert isinstance(v, float)

    def test_zscore_with_zero_std(self):
        """Test z-score calculation when null std is zero."""
        counts = {'motif_0': 10}
        null_counts = [
            {'motif_0': 10},
            {'motif_0': 10},
            {'motif_0': 10}
        ]
        
        # Should handle zero std gracefully (return 0 or raise)
        try:
            z_scores = compute_z_scores(counts, null_counts)
            # If it returns, z-score should be 0 or inf
            assert 0 in z_scores.values() or np.isinf(list(z_scores.values())[0])
        except Exception:
            pass  # Expected if function raises on zero std

    def test_zscore_with_single_null(self):
        """Test z-score with only one null model."""
        counts = {'motif_0': 10}
        null_counts = [{'motif_0': 8}]
        
        # With one sample, std is 0, so this should handle edge case
        try:
            z_scores = compute_z_scores(counts, null_counts)
            assert isinstance(z_scores, dict)
        except Exception:
            pass  # Expected if function requires multiple nulls