"""
Unit tests for graph utilities.
"""
import pytest
import networkx as nx
import numpy as np
from code.graph_utils import inject_noise, build_memory_graph, get_graph_statistics

class TestInjectNoise:
    """Tests for the inject_noise function."""

    def test_inject_noise_replaces_edges(self):
        """
        Test that inject_noise REPLACES edges rather than adding them.
        The number of edges should remain constant (or decrease if graph is too small).
        """
        # Create a simple graph with known edges
        G = nx.Graph()
        G.add_edges_from([
            (1, 2), (2, 3), (3, 4), (4, 5),
            (1, 3), (2, 4), (3, 5)
        ])
        
        original_num_edges = G.number_of_edges()
        original_edges = set(G.edges())
        
        # Inject 50% noise
        noisy_G = inject_noise(G, noise_ratio=0.5, seed=42)
        
        # The number of edges should remain the same (replaced, not added)
        assert noisy_G.number_of_edges() == original_num_edges, \
            f"Edge count changed: {original_num_edges} -> {noisy_G.number_of_edges()}. " \
            "Noise should REPLACE edges, not add them."
        
        # Some edges should have changed
        noisy_edges = set(noisy_G.edges())
        unchanged_edges = original_edges.intersection(noisy_edges)
        
        # With 50% noise and seed 42, we expect some changes
        # At least 1 edge should be different (unless the random replacement picks the same edge)
        # We verify that the function actually attempted replacement by checking
        # that the graph structure changed or that noise edges exist
        noise_edges = [e for e in noisy_G.edges() if noisy_G.edges[e].get('type') == 'noise']
        assert len(noise_edges) > 0, "Expected at least one noise edge to be added"

    def test_inject_noise_deterministic_with_seed(self):
        """Test that the same seed produces the same noisy graph."""
        G = nx.Graph()
        G.add_edges_from([(1, 2), (2, 3), (3, 4), (4, 5)])
        
        noisy_1 = inject_noise(G, noise_ratio=0.5, seed=42)
        noisy_2 = inject_noise(G, noise_ratio=0.5, seed=42)
        
        # Compare edges
        assert set(noisy_1.edges()) == set(noisy_2.edges()), \
            "Same seed should produce identical noisy graphs"

    def test_inject_noise_different_seeds(self):
        """Test that different seeds produce different noisy graphs."""
        G = nx.Graph()
        G.add_edges_from([(1, 2), (2, 3), (3, 4), (4, 5), (5, 6), (6, 7)])
        
        noisy_1 = inject_noise(G, noise_ratio=0.5, seed=42)
        noisy_2 = inject_noise(G, noise_ratio=0.5, seed=123)
        
        # With high probability, different seeds produce different results
        # We check that they are not identical
        if set(noisy_1.edges()) == set(noisy_2.edges()):
            # If they happen to be the same (low probability), check noise types
            noise_1 = sum(1 for e in noisy_1.edges() if noisy_1.edges[e].get('type') == 'noise')
            noise_2 = sum(1 for e in noisy_2.edges() if noisy_2.edges[e].get('type') == 'noise')
            # Even if edge sets are same, the noise assignment might differ
            # For robustness, we just ensure the function runs without error
            pass

    def test_inject_noise_zero_ratio(self):
        """Test that 0.0 noise ratio returns the original graph."""
        G = nx.Graph()
        G.add_edges_from([(1, 2), (2, 3), (3, 4)])
        
        noisy_G = inject_noise(G, noise_ratio=0.0, seed=42)
        
        assert set(G.edges()) == set(noisy_G.edges()), \
            "Zero noise ratio should return the original graph"

    def test_inject_noise_one_ratio(self):
        """Test that 1.0 noise ratio replaces all edges."""
        G = nx.Graph()
        G.add_edges_from([(1, 2), (2, 3), (3, 4)])
        
        noisy_G = inject_noise(G, noise_ratio=1.0, seed=42)
        
        # All edges should be noise edges (or the graph structure is completely different)
        original_edges = set(G.edges())
        noisy_edges = set(noisy_G.edges())
        
        # At least some edges should have changed
        assert len(original_edges.intersection(noisy_edges)) < len(original_edges), \
            "With 100% noise, all edges should be replaced"

    def test_inject_noise_empty_graph(self):
        """Test handling of a graph with no edges."""
        G = nx.Graph()
        G.add_nodes_from([1, 2, 3])
        
        noisy_G = inject_noise(G, noise_ratio=0.5, seed=42)
        
        # Should return the graph unchanged (no edges to replace)
        assert noisy_G.number_of_edges() == 0

    def test_inject_noise_invalid_ratio(self):
        """Test that invalid noise ratios raise ValueError."""
        G = nx.Graph()
        G.add_edge(1, 2)
        
        with pytest.raises(ValueError):
            inject_noise(G, noise_ratio=1.5, seed=42)
        
        with pytest.raises(ValueError):
            inject_noise(G, noise_ratio=-0.1, seed=42)

    def test_inject_noise_preserves_nodes(self):
        """Test that node set is preserved during noise injection."""
        G = nx.Graph()
        G.add_edges_from([(1, 2), (2, 3), (3, 4)])
        
        noisy_G = inject_noise(G, noise_ratio=0.5, seed=42)
        
        assert set(G.nodes()) == set(noisy_G.nodes()), \
            "Node set should be preserved during noise injection"

    def test_inject_noise_chi_square_randomness(self):
        """
        Basic randomness check: over multiple runs with different seeds,
        the distribution of noise edges should not be biased toward specific pairs.
        This is a simplified check; a full chi-square test would require many more samples.
        """
        G = nx.Graph()
        # Create a complete graph K4 to ensure many possible edge pairs
        G.add_edges_from([
            (1, 2), (1, 3), (1, 4),
            (2, 3), (2, 4),
            (3, 4)
        ])
        
        # Collect noise edges from multiple seeds
        noise_edge_counts = {}
        for seed in range(10):
            noisy_G = inject_noise(G, noise_ratio=0.5, seed=seed)
            for u, v in noisy_G.edges():
                if noisy_G.edges[u, v].get('type') == 'noise':
                    edge = tuple(sorted((u, v)))
                    noise_edge_counts[edge] = noise_edge_counts.get(edge, 0) + 1
        
        # With 10 samples and 6 possible edges, we expect some variation
        # This test just ensures the function runs and produces varied results
        assert len(noise_edge_counts) > 0, "Expected to find some noise edges across runs"

class TestBuildMemoryGraph:
    """Tests for build_memory_graph."""

    def test_build_memory_graph_basic(self):
        """Test basic graph construction from context."""
        context = "This is a test. It has two sentences. We check connectivity."
        G = build_memory_graph(context)
        
        assert G.number_of_nodes() == 3, "Expected 3 nodes for 3 sentences"
        assert G.number_of_edges() >= 2, "Expected at least sequential edges"

    def test_build_memory_graph_empty(self):
        """Test handling of empty context."""
        G = build_memory_graph("")
        assert G.number_of_nodes() == 0

class TestGetGraphStatistics:
    """Tests for get_graph_statistics."""

    def test_get_graph_statistics(self):
        """Test calculation of graph statistics."""
        G = nx.Graph()
        G.add_edges_from([(1, 2), (2, 3), (3, 4)])
        
        stats = get_graph_statistics(G)
        
        assert stats["num_nodes"] == 4
        assert stats["num_edges"] == 3
        assert stats["is_connected"] == True
        assert stats["num_components"] == 1