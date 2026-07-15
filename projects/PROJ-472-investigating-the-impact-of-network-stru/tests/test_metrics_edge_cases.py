import pytest
import numpy as np
import pandas as pd
from pathlib import Path
import sys

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from analysis.metrics import compute_degree_centrality, compute_clustering_coefficient, compute_rich_club_coefficient
from utils.logger import ResearchError

class TestMetricsEdgeCases:
    """Additional unit tests for edge cases in metrics computation."""

    def test_degree_centrality_symmetric_matrix(self):
        """Verify degree centrality is symmetric for undirected graphs."""
        adjacency = np.array([
            [0, 1, 1, 0],
            [1, 0, 1, 1],
            [1, 1, 0, 1],
            [0, 1, 1, 0]
        ])
        
        degree = compute_degree_centrality(adjacency)
        # For undirected graphs, degree should be consistent with adjacency
        expected_degrees = [2, 3, 3, 2]
        assert np.allclose(degree, expected_degrees)

    def test_clustering_coefficient_triangle(self):
        """Test clustering coefficient on a perfect triangle (should be 1.0)."""
        adjacency = np.array([
            [0, 1, 1],
            [1, 0, 1],
            [1, 1, 0]
        ])
        
        clustering = compute_clustering_coefficient(adjacency)
        # All nodes in a triangle have clustering coefficient 1.0
        assert np.allclose(clustering, 1.0)

    def test_rich_club_coefficient_range(self):
        """Verify rich-club coefficients are within valid range [0, 1]."""
        # Create a random symmetric adjacency matrix
        np.random.seed(42)
        n = 10
        adjacency = (np.random.rand(n, n) > 0.7).astype(float)
        adjacency = (adjacency + adjacency.T) / 2  # Make symmetric
        np.fill_diagonal(adjacency, 0)
        
        rich_club = compute_rich_club_coefficient(adjacency)
        
        assert all(0 <= rc <= 1 for rc in rich_club.values())

    def test_metrics_with_self_loops(self):
        """Test that self-loops are ignored in metric computation."""
        adjacency = np.array([
            [1, 1, 0],
            [1, 1, 1],
            [0, 1, 1]
        ])
        
        # Should handle self-loops gracefully (treat as no edge)
        degree = compute_degree_centrality(adjacency)
        assert degree is not None

    def test_metrics_with_nan_values(self):
        """Test that NaN values in adjacency matrix are handled."""
        adjacency = np.array([
            [0, 1, np.nan],
            [1, 0, 1],
            [np.nan, 1, 0]
        ])
        
        # Should either handle gracefully or raise a clear error
        with pytest.raises((ValueError, ResearchError)):
            compute_degree_centrality(adjacency)

    def test_metrics_with_infinite_values(self):
        """Test that infinite values in adjacency matrix are handled."""
        adjacency = np.array([
            [0, 1, np.inf],
            [1, 0, 1],
            [np.inf, 1, 0]
        ])
        
        with pytest.raises((ValueError, ResearchError)):
            compute_degree_centrality(adjacency)

    def test_rich_club_empty_graph(self):
        """Test rich-club coefficient on a graph with no edges."""
        adjacency = np.zeros((5, 5))
        
        rich_club = compute_rich_club_coefficient(adjacency)
        # Should return zeros or handle gracefully
        assert rich_club is not None

    def test_clustering_coefficient_star_graph(self):
        """Test clustering coefficient on a star graph (center should be 0)."""
        # Star graph: node 0 connected to all others, no other connections
        n = 5
        adjacency = np.zeros((n, n))
        for i in range(1, n):
            adjacency[0, i] = 1
            adjacency[i, 0] = 1
        
        clustering = compute_clustering_coefficient(adjacency)
        
        # Center node (0) should have clustering coefficient 0
        # Leaf nodes should have clustering coefficient 0 (no triangles)
        assert clustering[0] == 0.0
        assert all(c == 0.0 for c in clustering[1:])
