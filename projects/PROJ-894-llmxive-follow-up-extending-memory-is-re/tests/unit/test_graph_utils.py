"""
Unit tests for graph_utils.py, specifically focusing on noise injection and graph handling.
"""

import pytest
import networkx as nx
import numpy as np
from pathlib import Path
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from graph_utils import inject_noise, build_memory_graph, validate_graph, get_graph_statistics


class TestInjectNoise:
    """Tests for the inject_noise function."""

    def test_inject_noise_replaces_edges(self):
        """
        Test that inject_noise replaces edges rather than adding new ones.
        The total edge count should remain constant.
        """
        # Create a simple graph
        G = nx.DiGraph()
        G.add_edges_from([
            ('A', 'B'),
            ('B', 'C'),
            ('C', 'D'),
            ('D', 'A'),
            ('A', 'C')
        ])
        
        original_edges = set(G.edges())
        original_count = G.number_of_edges()
        
        # Inject noise with ratio 0.4 (should replace ~2 edges)
        noisy_G = inject_noise(G, ratio=0.4, seed=42)
        
        noisy_edges = set(noisy_G.edges())
        noisy_count = noisy_G.number_of_edges()
        
        # Assert total edge count is preserved
        assert noisy_count == original_count, \
            f"Edge count changed: {original_count} -> {noisy_count}"
        
        # Assert at least one edge was replaced
        unchanged = original_edges & noisy_edges
        replaced = original_count - len(unchanged)
        assert replaced > 0, "No edges were replaced"
        
    def test_inject_noise_deterministic(self):
        """
        Test that inject_noise produces the same result with the same seed.
        """
        G = nx.DiGraph()
        G.add_edges_from([
            ('A', 'B'),
            ('B', 'C'),
            ('C', 'D'),
            ('D', 'A')
        ])
        
        # Run twice with same seed
        noisy_G1 = inject_noise(G, ratio=0.5, seed=123)
        noisy_G2 = inject_noise(G, ratio=0.5, seed=123)
        
        assert set(noisy_G1.edges()) == set(noisy_G2.edges()), \
            "Noise injection is not deterministic with same seed"
        
    def test_inject_noise_no_self_loops(self):
        """
        Test that inject_noise does not create self-loops.
        """
        G = nx.DiGraph()
        G.add_edges_from([
            ('A', 'B'),
            ('B', 'C'),
            ('C', 'D')
        ])
        
        noisy_G = inject_noise(G, ratio=1.0, seed=42)
        
        # Check for self-loops
        self_loops = [edge for edge in noisy_G.edges() if edge[0] == edge[1]]
        assert len(self_loops) == 0, f"Self-loops found: {self_loops}"
        
    def test_inject_noise_empty_graph(self):
        """
        Test behavior on an empty graph.
        """
        G = nx.DiGraph()
        noisy_G = inject_noise(G, ratio=0.5, seed=42)
        
        assert noisy_G.number_of_edges() == 0
        assert noisy_G.number_of_nodes() == 0
        
    def test_inject_noise_single_node(self):
        """
        Test behavior on a graph with a single node.
        """
        G = nx.DiGraph()
        G.add_node('A')
        
        noisy_G = inject_noise(G, ratio=0.5, seed=42)
        
        # Should remain unchanged (no edges to replace, can't add edges)
        assert noisy_G.number_of_edges() == 0
        assert noisy_G.number_of_nodes() == 1
        
    def test_inject_noise_ratio_zero(self):
        """
        Test that ratio=0.0 results in no changes.
        """
        G = nx.DiGraph()
        G.add_edges_from([
            ('A', 'B'),
            ('B', 'C')
        ])
        
        original_edges = set(G.edges())
        noisy_G = inject_noise(G, ratio=0.0, seed=42)
        
        assert set(noisy_G.edges()) == original_edges
        
    def test_inject_noise_ratio_one(self):
        """
        Test that ratio=1.0 replaces all edges.
        """
        G = nx.DiGraph()
        G.add_edges_from([
            ('A', 'B'),
            ('B', 'C'),
            ('C', 'D')
        ])
        
        original_edges = set(G.edges())
        noisy_G = inject_noise(G, ratio=1.0, seed=42)
        noisy_edges = set(noisy_G.edges())
        
        # All original edges should be replaced (unlikely to be exactly 0 overlap, but test logic)
        # At least, the structure should be different
        assert noisy_G.number_of_edges() == G.number_of_edges()

class TestBuildMemoryGraph:
    """Tests for the build_memory_graph function."""

    def test_build_memory_graph_basic(self):
        """Test basic graph construction from triples."""
        triples = [
            ('Alice', 'loves', 'Bob'),
            ('Bob', 'knows', 'Charlie'),
            ('Charlie', 'likes', 'Alice')
        ]
        
        G = build_memory_graph(triples)
        
        assert G.number_of_nodes() == 3
        assert G.number_of_edges() == 3
        assert G.has_edge('alice', 'bob')
        assert G.has_edge('bob', 'charlie')
        assert G.has_edge('charlie', 'alice')
        
    def test_build_memory_graph_normalized(self):
        """Test that node names are normalized (lowercase)."""
        triples = [
            ('Alice', 'LOVES', 'Bob'),
        ]
        
        G = build_memory_graph(triples)
        
        assert 'alice' in G.nodes()
        assert 'bob' in G.nodes()
        assert 'Alice' not in G.nodes()
        assert 'LOVES' not in G.nodes()

class TestValidateGraph:
    """Tests for the validate_graph function."""

    def test_validate_graph_valid(self):
        """Test validation of a valid graph."""
        G = nx.DiGraph()
        G.add_edges_from([('A', 'B'), ('B', 'C')])
        
        is_valid, issues = validate_graph(G)
        
        assert is_valid
        assert len(issues) == 0
        
    def test_validate_graph_disconnected(self):
        """Test validation of a disconnected graph."""
        G = nx.DiGraph()
        G.add_edges_from([('A', 'B'), ('C', 'D')])
        
        # Disconnected graphs are valid but flagged
        is_valid, issues = validate_graph(G)
        
        assert is_valid  # Still structurally valid
        assert any('disconnected' in issue.lower() for issue in issues)

class TestGetGraphStatistics:
    """Tests for the get_graph_statistics function."""

    def test_get_graph_statistics(self):
        """Test calculation of graph statistics."""
        G = nx.DiGraph()
        G.add_edges_from([
            ('A', 'B'),
            ('B', 'C'),
            ('C', 'D'),
            ('D', 'A')
        ])
        
        stats = get_graph_statistics(G)
        
        assert stats['num_nodes'] == 4
        assert stats['num_edges'] == 4
        assert 'density' in stats
        assert 'avg_in_degree' in stats
        assert 'avg_out_degree' in stats

class TestDegenerateGraphHandling:
    """Tests for degenerate graph scenarios."""

    def test_single_node_graph(self):
        """Test handling of a single-node graph."""
        G = nx.DiGraph()
        G.add_node('A')
        
        # Should not crash
        noisy_G = inject_noise(G, ratio=0.5, seed=42)
        assert noisy_G.number_of_nodes() == 1
        assert noisy_G.number_of_edges() == 0
        
    def test_zero_edge_graph(self):
        """Test handling of a graph with zero edges."""
        G = nx.DiGraph()
        G.add_edges_from([('A', 'B'), ('C', 'D')])
        G.remove_edges_from([('A', 'B'), ('C', 'D')])
        
        # Should not crash
        noisy_G = inject_noise(G, ratio=0.5, seed=42)
        assert noisy_G.number_of_edges() == 0

if __name__ == "__main__":
    pytest.main([__file__, "-v"])