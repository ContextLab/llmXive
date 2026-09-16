import pytest
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from env.state_graph import Node, Edge, StateGraph
from env.graph_validator import find_path_bfs, validate_graph_connectivity, validate_graph_properties, ensure_valid_graph


class TestGraphValidator:
    def test_find_path_simple(self):
        """Test BFS on a simple linear graph."""
        graph = StateGraph()
        graph.add_node(Node(id="A", neighbors=["B"]))
        graph.add_node(Node(id="B", neighbors=["C"]))
        graph.add_node(Node(id="C", neighbors=[]))
        graph.start_node_id = "A"
        graph.goal_node_id = "C"

        path = find_path_bfs(graph, "A", "C")
        assert path is not None
        assert path == ["A", "B", "C"]

    def test_find_path_no_path(self):
        """Test BFS on a disconnected graph."""
        graph = StateGraph()
        graph.add_node(Node(id="A", neighbors=["B"]))
        graph.add_node(Node(id="B", neighbors=[]))
        graph.add_node(Node(id="C", neighbors=[])) # C is isolated
        graph.start_node_id = "A"
        graph.goal_node_id = "C"

        path = find_path_bfs(graph, "A", "C")
        assert path is None

    def test_validate_graph_properties_invalid_edge(self):
        """Test validation with an edge to a non-existent node."""
        graph = StateGraph()
        node_a = Node(id="A", neighbors=["B"])
        graph.add_node(node_a)
        graph.start_node_id = "A"
        graph.goal_node_id = "B" # B is referenced but not added

        assert validate_graph_properties(graph) is False

    def test_validate_connectivity_valid(self):
        """Test connectivity validation on a valid graph."""
        graph = StateGraph()
        graph.add_node(Node(id="Start", neighbors=["Mid"]))
        graph.add_node(Node(id="Mid", neighbors=["End"]))
        graph.add_node(Node(id="End", neighbors=[]))
        graph.start_node_id = "Start"
        graph.goal_node_id = "End"

        is_valid, path = validate_graph_connectivity(graph)
        assert is_valid is True
        assert path is not None

    def test_validate_connectivity_invalid(self):
        """Test connectivity validation on a graph with no path."""
        graph = StateGraph()
        graph.add_node(Node(id="Start", neighbors=["Mid"]))
        graph.add_node(Node(id="Mid", neighbors=[]))
        graph.add_node(Node(id="End", neighbors=[]))
        graph.start_node_id = "Start"
        graph.goal_node_id = "End"

        is_valid, path = validate_graph_connectivity(graph)
        assert is_valid is False
        assert path is None

    def test_ensure_valid_graph_success(self):
        """Test ensure_valid_graph returns graph when valid."""
        graph = StateGraph()
        graph.add_node(Node(id="S", neighbors=["G"]))
        graph.add_node(Node(id="G", neighbors=[]))
        graph.start_node_id = "S"
        graph.goal_node_id = "G"

        result = ensure_valid_graph(graph)
        assert result is graph

    def test_ensure_valid_graph_failure(self):
        """Test ensure_valid_graph returns None when no path exists."""
        graph = StateGraph()
        graph.add_node(Node(id="S", neighbors=["X"]))
        graph.add_node(Node(id="X", neighbors=[]))
        graph.add_node(Node(id="G", neighbors=[]))
        graph.start_node_id = "S"
        graph.goal_node_id = "G"

        result = ensure_valid_graph(graph)
        assert result is None