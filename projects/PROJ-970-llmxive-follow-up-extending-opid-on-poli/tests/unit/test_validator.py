"""
Unit tests for the graph validator module.

Tests verify that validate_graph correctly identifies valid paths
and raises RuntimeError for unreachable goals.
"""
import pytest
import numpy as np
from environment.state_graph import StateGraph, Node, Edge
from environment.validator import validate_graph


class TestValidateGraph:
    """Tests for the validate_graph function."""

    def setup_method(self):
        """Set up test fixtures."""
        np.random.seed(42)

    def test_valid_linear_chain(self):
        """Test that a simple linear chain passes validation."""
        # Create nodes 0 -> 1 -> 2
        nodes = [Node(id=i) for i in range(3)]
        edges = [
            Edge(source=nodes[0], target=nodes[1]),
            Edge(source=nodes[1], target=nodes[2])
        ]
        graph = StateGraph(
            nodes=nodes,
            edges=edges,
            start=nodes[0],
            goal=nodes[2],
            tier=1
        )
        
        # Should return True without raising
        result = validate_graph(graph)
        assert result is True

    def test_valid_branching_graph(self):
        """Test a graph with branching paths."""
        # Create a diamond shape: 0 -> 1, 0 -> 2 -> 3
        nodes = [Node(id=i) for i in range(4)]
        edges = [
            Edge(source=nodes[0], target=nodes[1]),
            Edge(source=nodes[0], target=nodes[2]),
            Edge(source=nodes[1], target=nodes[3]),
            Edge(source=nodes[2], target=nodes[3])
        ]
        graph = StateGraph(
            nodes=nodes,
            edges=edges,
            start=nodes[0],
            goal=nodes[3],
            tier=2
        )
        
        result = validate_graph(graph)
        assert result is True

    def test_unreachable_goal_raises_error(self):
        """Test that a graph with no path to goal raises RuntimeError."""
        # Create two disconnected components
        nodes = [Node(id=i) for i in range(4)]
        edges = [
            Edge(source=nodes[0], target=nodes[1]),
            # nodes[2] and nodes[3] are isolated or disconnected from 0->1
            Edge(source=nodes[2], target=nodes[3])
        ]
        graph = StateGraph(
            nodes=nodes,
            edges=edges,
            start=nodes[0],
            goal=nodes[3],
            tier=1
        )
        
        with pytest.raises(RuntimeError, match="No path exists"):
            validate_graph(graph)

    def test_self_loops_dont_break_validation(self):
        """Test that self-loops do not prevent path detection."""
        nodes = [Node(id=i) for i in range(3)]
        edges = [
            Edge(source=nodes[0], target=nodes[0]), # Self loop
            Edge(source=nodes[0], target=nodes[1]),
            Edge(source=nodes[1], target=nodes[2])
        ]
        graph = StateGraph(
            nodes=nodes,
            edges=edges,
            start=nodes[0],
            goal=nodes[2],
            tier=1
        )
        
        result = validate_graph(graph)
        assert result is True

    def test_none_graph_raises_error(self):
        """Test that passing None raises RuntimeError."""
        with pytest.raises(RuntimeError, match="Cannot validate a None graph"):
            validate_graph(None)

    def test_missing_start_node_raises_error(self):
        """Test that a graph with None start raises RuntimeError."""
        nodes = [Node(id=0)]
        graph = StateGraph(
            nodes=nodes,
            edges=[],
            start=None,
            goal=nodes[0],
            tier=1
        )
        with pytest.raises(RuntimeError, match="missing start"):
            validate_graph(graph)