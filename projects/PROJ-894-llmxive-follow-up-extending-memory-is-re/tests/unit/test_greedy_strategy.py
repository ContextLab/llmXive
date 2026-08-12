"""
Unit tests for the Greedy Traversal Strategy.
"""
import pytest
import networkx as nx
from strategies.greedy import GreedyTraversal, run_greedy_strategy
from graph_utils import validate_graph

class TestGreedyTraversal:
    """Tests for GreedyTraversal class."""

    def test_init(self):
        """Test initialization with default and custom parameters."""
        g = GreedyTraversal()
        assert g.top_k == 3
        assert g.max_iterations == 100

        g_custom = GreedyTraversal(top_k=5, max_iterations=50)
        assert g_custom.top_k == 5
        assert g_custom.max_iterations == 50

    def test_run_simple_graph(self):
        """Test traversal on a simple linear graph."""
        G = nx.DiGraph()
        G.add_edge("A", "B", confidence=0.9)
        G.add_edge("B", "C", confidence=0.8)
        G.add_edge("C", "D", confidence=0.7)
        
        strategy = GreedyTraversal(top_k=1)
        result = strategy.run(G, "Find D")
        
        assert result["status"] == "success"
        assert result["nodes_visited"] >= 1
        assert len(result["path"]) > 0
        assert "D" in result["answer"]

    def test_run_disconnected_graph(self):
        """Test handling of a graph where the target is unreachable."""
        G = nx.DiGraph()
        G.add_edge("A", "B", confidence=0.9)
        G.add_edge("C", "D", confidence=0.9) # Disconnected component
        
        strategy = GreedyTraversal(top_k=1)
        # Start at A, trying to find D (unreachable)
        result = strategy.run(G, "Find D")
        
        # Should not crash, status should be incomplete
        assert result["status"] in ["incomplete", "success"] # Depends on fallback logic
        assert result["nodes_visited"] > 0

    def test_run_empty_graph(self):
        """Test handling of an empty graph."""
        G = nx.DiGraph()
        strategy = GreedyTraversal()
        result = strategy.run(G, "Find anything")
        
        assert result["status"] == "degenerate"
        assert result["nodes_visited"] == 0
        assert result["answer"] == ""

    def test_top_k_selection(self):
        """Test that the strategy correctly selects top-k edges."""
        G = nx.DiGraph()
        # Node A connects to B, C, D with different confidences
        G.add_edge("A", "B", confidence=0.5)
        G.add_edge("A", "C", confidence=0.9)
        G.add_edge("A", "D", confidence=0.7)
        
        strategy = GreedyTraversal(top_k=2)
        result = strategy.run(G, "Start at A")
        
        # Should visit C (0.9) and D (0.7), but not B (0.5)
        assert result["nodes_visited"] == 2
        # Check path contains C and D
        path_nodes = [p["v"] for p in result["path"]]
        assert "C" in path_nodes
        assert "D" in path_nodes
        assert "B" not in path_nodes

    def test_degenerate_single_node(self):
        """Test handling of a single-node graph."""
        G = nx.DiGraph()
        G.add_node("X")
        strategy = GreedyTraversal()
        result = strategy.run(G, "Find X")
        
        # Should handle gracefully, likely incomplete or success if X matches
        assert result["status"] in ["success", "incomplete"]
        assert result["nodes_visited"] == 1

def test_run_greedy_strategy_wrapper():
    """Test the convenience wrapper function."""
    G = nx.DiGraph()
    G.add_edge("Start", "End", confidence=0.99)
    
    result = run_greedy_strategy(G, "Find End")
    
    assert result["status"] == "success"
    assert "End" in result["answer"]