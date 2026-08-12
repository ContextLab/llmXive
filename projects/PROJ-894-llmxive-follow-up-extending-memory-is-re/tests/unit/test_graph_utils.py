import pytest
import networkx as nx
import numpy as np
from code.graph_utils import inject_noise, validate_graph, get_graph_statistics

class TestInjectNoise:
    def test_inject_noise_replaces_edges(self):
        """
        Test that inject_noise correctly replaces a proportion of edges.
        This is the primary test for T011b.
        """
        # Create a deterministic graph
        G = nx.DiGraph()
        G.add_edges_from([
            (1, 2), (2, 3), (3, 4), (4, 5),
            (1, 3), (2, 4), (3, 5), (1, 5)
        ])
        
        original_edges = set(G.edges())
        original_count = len(original_edges)
        
        # Inject 50% noise with a fixed seed
        ratio = 0.5
        seed = 42
        noisy_G = inject_noise(G, ratio, seed)
        
        noisy_edges = set(noisy_G.edges())
        
        # Verify total edge count remains roughly the same (removed vs added)
        # Note: If we remove edges that block all potential new edges, count might drop,
        # but in a connected graph like this, it should be stable.
        assert noisy_G.number_of_edges() <= original_count + 1 # Allow small variance if graph is dense
        
        # Verify that not all original edges are preserved
        # With 50% replacement, we expect some changes
        removed_count = original_count - len(original_edges & noisy_edges)
        assert removed_count > 0, "Expected some edges to be removed."
        
        # Verify that some new edges were added that were not in the original
        added_count = len(noisy_edges - original_edges)
        assert added_count > 0, "Expected some new edges to be added."
        
        # Verify reproducibility: running with same seed should produce same result
        noisy_G_2 = inject_noise(G, ratio, seed)
        assert set(noisy_G.edges()) == set(noisy_G_2.edges()), "Noise injection is not reproducible with same seed."

    def test_inject_noise_zero_ratio(self):
        """Test that 0 ratio results in identical graph."""
        G = nx.DiGraph()
        G.add_edges_from([(1, 2), (2, 3)])
        
        noisy_G = inject_noise(G, 0.0, 42)
        
        assert set(G.edges()) == set(noisy_G.edges())
        assert G.number_of_edges() == noisy_G.number_of_edges()

    def test_inject_noise_empty_graph(self):
        """Test behavior on an empty graph."""
        G = nx.DiGraph()
        noisy_G = inject_noise(G, 0.5, 42)
        
        assert noisy_G.number_of_edges() == 0
        assert noisy_G.number_of_nodes() == 0

    def test_inject_noise_single_edge(self):
        """Test behavior on a graph with a single edge."""
        G = nx.DiGraph()
        G.add_edge(1, 2)
        
        # With 1 edge and 50% ratio, 0 edges should be removed (floor(0.5) = 0)
        # But if ratio is 1.0, 1 edge should be removed
        noisy_G = inject_noise(G, 1.0, 42)
        
        # If we remove the only edge, we have 0 edges.
        # Can we add one back? Yes, if there are nodes.
        # But if we remove (1,2), we have nodes 1 and 2. Potential new edge: (2,1) or self loops (excluded).
        # So we might add (2,1).
        assert noisy_G.number_of_nodes() == 2

    def test_inject_noise_invalid_ratio(self):
        """Test that invalid ratio raises ValueError."""
        G = nx.DiGraph()
        G.add_edge(1, 2)
        
        with pytest.raises(ValueError):
            inject_noise(G, 1.5, 42)
        
        with pytest.raises(ValueError):
            inject_noise(G, -0.1, 42)

    def test_inject_noise_no_self_loops_added(self):
        """Test that noise injection never adds self-loops."""
        G = nx.DiGraph()
        G.add_edges_from([(1, 2), (2, 3), (3, 1)])
        
        # Force high ratio to maximize edge churn
        noisy_G = inject_noise(G, 1.0, 42)
        
        for u, v in noisy_G.edges():
            assert u != v, f"Self-loop detected: ({u}, {v})"

    def test_inject_noise_deterministic_seed(self):
        """Test that different seeds produce different results (usually)."""
        G = nx.DiGraph()
        G.add_edges_from([(1, 2), (2, 3), (3, 4), (4, 5), (5, 1)])
        
        noisy_G_1 = inject_noise(G, 0.5, 123)
        noisy_G_2 = inject_noise(G, 0.5, 456)
        
        # It is statistically extremely unlikely they are identical, but not impossible for very small graphs.
        # However, for a 5-node cycle, they should differ.
        edges_1 = set(noisy_G_1.edges())
        edges_2 = set(noisy_G_2.edges())
        
        # We assert they are different to confirm seed usage
        assert edges_1 != edges_2, "Different seeds should produce different noise patterns."

class TestValidateGraph:
    def test_validate_valid_graph(self):
        G = nx.DiGraph()
        G.add_edges_from([(1, 2), (2, 3)])
        result = validate_graph(G)
        assert result["is_valid"] is True
        assert len(result["issues"]) == 0

    def test_validate_undirected_graph(self):
        G = nx.Graph() # Undirected
        G.add_edge(1, 2)
        result = validate_graph(G)
        assert result["is_valid"] is False
        assert "Graph is not directed." in result["issues"]

class TestGetGraphStatistics:
    def test_get_graph_statistics_basic(self):
        G = nx.DiGraph()
        G.add_edges_from([(1, 2), (2, 3), (3, 1)])
        stats = get_graph_statistics(G)
        
        assert stats["num_nodes"] == 3
        assert stats["num_edges"] == 3
        assert stats["density"] == pytest.approx(0.5) # 3 / (3*2)
        
        assert stats["avg_in_degree"] == 1.0
        assert stats["avg_out_degree"] == 1.0
        assert stats["num_components"] == 1
        assert stats["largest_component_size"] == 3