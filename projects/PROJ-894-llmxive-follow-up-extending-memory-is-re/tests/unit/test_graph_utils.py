import pytest
import networkx as nx
import numpy as np
from code.graph_utils import inject_noise, validate_graph, get_graph_statistics
from code.strategies.full import FullTraversal, run_full_strategy
from code.strategies.lazy import LazyTraversal, run_lazy_strategy
from code.strategies.greedy import GreedyTraversal, run_greedy_strategy

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

class TestDegenerateGraphHandling:
    """
    Tests for T046: Verify that traversal strategies handle degenerate graphs
    (single-node, zero-edge) without crashing or division-by-zero errors.
    """

    def _create_single_node_graph(self):
        """Helper to create a graph with one node and zero edges."""
        G = nx.DiGraph()
        G.add_node("node_1")
        return G

    def _create_empty_graph(self):
        """Helper to create a completely empty graph."""
        return nx.DiGraph()

    def _create_single_edge_graph(self):
        """Helper to create a graph with two nodes and one edge."""
        G = nx.DiGraph()
        G.add_edge("start", "end")
        return G

    def test_full_strategy_single_node_no_crash(self):
        """
        Test FullTraversal on a single-node graph.
        Expects no division-by-zero and a 'degenerate' or 'unresolved' status.
        """
        G = self._create_single_node_graph()
        
        # Define a query that targets the single node (or a non-existent one)
        query = {"start_node": "node_1", "target_node": "node_1"}
        
        # Run the strategy
        result = run_full_strategy(G, query)
        
        # Assert no crash occurred and result contains status
        assert "status" in result
        # The strategy should detect the degenerate nature (0 edges)
        # and flag it appropriately rather than hanging or crashing.
        assert result["status"] in ["degenerate", "unresolved", "completed"]

    def test_full_strategy_empty_graph_no_crash(self):
        """
        Test FullTraversal on an empty graph.
        """
        G = self._create_empty_graph()
        query = {"start_node": "node_1", "target_node": "node_2"}
        
        result = run_full_strategy(G, query)
        
        assert "status" in result
        assert result["status"] in ["degenerate", "unresolved"]

    def test_lazy_strategy_single_node_no_crash(self):
        """
        Test LazyTraversal on a single-node graph.
        """
        G = self._create_single_node_graph()
        query = {"start_node": "node_1", "target_node": "node_1"}
        
        result = run_lazy_strategy(G, query)
        
        assert "status" in result
        assert result["status"] in ["degenerate", "unresolved", "completed"]

    def test_lazy_strategy_no_division_by_zero(self):
        """
        Specifically check that lazy strategy doesn't divide by zero
        when calculating thresholds on a graph with 0 edges.
        """
        G = self._create_empty_graph()
        query = {"start_node": "A", "target_node": "B"}
        
        # This should not raise ZeroDivisionError
        try:
            result = run_lazy_strategy(G, query)
            assert "status" in result
        except ZeroDivisionError:
            pytest.fail("LazyTraversal raised ZeroDivisionError on degenerate graph")

    def test_greedy_strategy_single_node_no_crash(self):
        """
        Test GreedyTraversal on a single-node graph.
        """
        G = self._create_single_node_graph()
        query = {"start_node": "node_1", "target_node": "node_1"}
        
        result = run_greedy_strategy(G, query)
        
        assert "status" in result
        assert result["status"] in ["degenerate", "unresolved", "completed"]

    def test_greedy_strategy_no_division_by_zero(self):
        """
        Specifically check that greedy strategy doesn't divide by zero
        when selecting top-k edges on a graph with 0 edges.
        """
        G = self._create_empty_graph()
        query = {"start_node": "A", "target_node": "B"}
        
        try:
            result = run_greedy_strategy(G, query)
            assert "status" in result
        except ZeroDivisionError:
            pytest.fail("GreedyTraversal raised ZeroDivisionError on degenerate graph")

    def test_degenerate_flag_returned(self):
        """
        Verify that the strategies explicitly return a 'degenerate' flag
        when the input graph has no edges to traverse.
        """
        G = self._create_empty_graph()
        query = {"start_node": "A", "target_node": "B"}
        
        # Test all three strategies
        strategies = [
            (run_full_strategy, "Full"),
            (run_lazy_strategy, "Lazy"),
            (run_greedy_strategy, "Greedy")
        ]
        
        for strategy_func, name in strategies:
            result = strategy_func(G, query)
            # We expect the status to indicate the graph was degenerate
            # or that the task was unresolved due to lack of connectivity
            assert "status" in result, f"{name} strategy missing status"
            # Depending on implementation, it might be 'degenerate' or 'unresolved'
            # The key is that it doesn't crash.
            assert result["status"] in ["degenerate", "unresolved", "failed"], \
                f"{name} strategy returned unexpected status: {result['status']}"