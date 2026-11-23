"""
Unit tests for the Greedy Traversal Strategy.
"""

import pytest
import networkx as nx
from strategies.greedy import GreedyTraversal, run_greedy_strategy
from graph_utils import inject_noise


class TestGreedyTraversal:
    """Tests for the GreedyTraversal class."""

    def test_simple_path(self):
        """Test traversal on a simple linear graph."""
        G = nx.DiGraph()
        G.add_edge("A", "B", weight=1.0)
        G.add_edge("B", "C", weight=1.0)
        G.add_edge("C", "D", weight=1.0)

        strategy = GreedyTraversal()
        path, stats = strategy.traverse(G, "A", "D")

        assert path == ["A", "B", "C", "D"]
        assert stats["status"] == "SUCCESS"
        assert stats["nodes_visited"] == 4

    def test_greedy_choice_higher_weight(self):
        """Test that greedy strategy picks the higher weight edge."""
        G = nx.DiGraph()
        G.add_edge("A", "B", weight=0.5)
        G.add_edge("A", "C", weight=0.9)
        G.add_edge("C", "D", weight=1.0)
        G.add_edge("B", "D", weight=1.0)

        strategy = GreedyTraversal()
        path, stats = strategy.traverse(G, "A", "D")

        # Should prefer A -> C because 0.9 > 0.5
        assert path[0] == "A"
        assert path[1] == "C"
        assert path[-1] == "D"
        assert stats["status"] == "SUCCESS"

    def test_dead_end(self):
        """Test behavior when a dead end is encountered."""
        G = nx.DiGraph()
        G.add_edge("A", "B", weight=1.0)
        G.add_edge("B", "C", weight=1.0)
        # No edge from C to D, and D is not reachable from C
        G.add_node("D")

        strategy = GreedyTraversal()
        path, stats = strategy.traverse(G, "A", "D")

        assert stats["status"] == "DEAD_END"
        assert "D" not in path

    def test_unreachable_target(self):
        """Test behavior when target is in a disconnected component."""
        G = nx.DiGraph()
        G.add_edge("A", "B", weight=1.0)
        G.add_edge("C", "D", weight=1.0)

        strategy = GreedyTraversal()
        path, stats = strategy.traverse(G, "A", "D")

        assert stats["status"] == "UNREACHABLE"

    def test_start_equals_target(self):
        """Test when start node is the same as target node."""
        G = nx.DiGraph()
        G.add_node("A")

        strategy = GreedyTraversal()
        path, stats = strategy.traverse(G, "A", "A")

        assert path == ["A"]
        assert stats["status"] == "SUCCESS"
        assert stats["nodes_visited"] == 1

    def test_invalid_start_node(self):
        """Test when start node is not in graph."""
        G = nx.DiGraph()
        G.add_edge("A", "B", weight=1.0)

        strategy = GreedyTraversal()
        path, stats = strategy.traverse(G, "X", "B")

        assert path == []
        assert stats["status"] == "NODE_NOT_FOUND"

    def test_max_visits_limit(self):
        """Test that traversal stops when max_visits is reached."""
        G = nx.DiGraph()
        # Create a long chain
        for i in range(50):
            G.add_edge(str(i), str(i+1), weight=1.0)

        strategy = GreedyTraversal(config={"max_visits": 10})
        path, stats = strategy.traverse(G, "0", "50")

        assert stats["nodes_visited"] == 10
        assert stats["status"] != "SUCCESS"  # Should not have reached target

    def test_run_greedy_strategy_function(self):
        """Test the convenience function run_greedy_strategy."""
        G = nx.DiGraph()
        G.add_edge("A", "B", weight=1.0)
        G.add_edge("B", "C", weight=1.0)

        path, stats = run_greedy_strategy(G, "A", "C")

        assert path == ["A", "B", "C"]
        assert stats["status"] == "SUCCESS"