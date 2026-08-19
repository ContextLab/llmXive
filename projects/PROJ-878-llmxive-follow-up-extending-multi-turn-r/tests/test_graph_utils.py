"""
Unit tests for code/utils/graph_utils.py.

This module provides comprehensive unit tests for the DAG validation
and topological metric calculation functions.
"""

import pytest
import networkx as nx
import numpy as np
from utils.graph_utils import (
    is_dag,
    validate_dag,
    nesting_depth,
    longest_path,
    branching_factor,
    compute_graph_metrics,
    graph_from_dict,
    graph_to_dict,
)


class TestIsDag:
    """Tests for the is_dag function."""

    def test_empty_graph_is_dag(self):
        """An empty DiGraph is a DAG."""
        G = nx.DiGraph()
        assert is_dag(G) is True

    def test_single_node_is_dag(self):
        """A single node DiGraph is a DAG."""
        G = nx.DiGraph()
        G.add_node("A")
        assert is_dag(G) is True

    def test_simple_dag_is_dag(self):
        """A simple directed acyclic graph is a DAG."""
        G = nx.DiGraph()
        G.add_edges_from([("A", "B"), ("B", "C")])
        assert is_dag(G) is True

    def test_cycle_is_not_dag(self):
        """A graph with a cycle is not a DAG."""
        G = nx.DiGraph()
        G.add_edges_from([("A", "B"), ("B", "C"), ("C", "A")])
        assert is_dag(G) is False

    def test_self_loop_is_not_dag(self):
        """A graph with a self-loop is not a DAG."""
        G = nx.DiGraph()
        G.add_edge("A", "A")
        assert is_dag(G) is False

    def test_undirected_graph_not_dag(self):
        """An undirected graph is not considered a DAG."""
        G = nx.Graph()
        G.add_edges_from([("A", "B"), ("B", "C")])
        assert is_dag(G) is False


class TestValidateDag:
    """Tests for the validate_dag function."""

    def test_valid_dag_returns_true_none(self):
        """A valid DAG returns (True, None)."""
        G = nx.DiGraph()
        G.add_edges_from([("A", "B"), ("B", "C")])
        is_valid, error_msg = validate_dag(G)
        assert is_valid is True
        assert error_msg is None

    def test_empty_graph_valid(self):
        """An empty graph is valid."""
        G = nx.DiGraph()
        is_valid, error_msg = validate_dag(G)
        assert is_valid is True
        assert error_msg is None

    def test_cycle_returns_false_error(self):
        """A graph with a cycle returns (False, error_message)."""
        G = nx.DiGraph()
        G.add_edges_from([("A", "B"), ("B", "C"), ("C", "A")])
        is_valid, error_msg = validate_dag(G)
        assert is_valid is False
        assert error_msg is not None
        assert "cycle" in error_msg.lower()

    def test_undirected_graph_returns_error(self):
        """An undirected graph returns an error."""
        G = nx.Graph()
        G.add_edge("A", "B")
        is_valid, error_msg = validate_dag(G)
        assert is_valid is False
        assert error_msg is not None
        assert "directed" in error_msg.lower()


class TestNestingDepth:
    """Tests for the nesting_depth function."""

    def test_empty_graph_depth_zero(self):
        """An empty graph has nesting depth 0."""
        G = nx.DiGraph()
        assert nesting_depth(G) == 0

    def test_single_node_depth_zero(self):
        """A single node graph has nesting depth 0."""
        G = nx.DiGraph()
        G.add_node("A")
        assert nesting_depth(G) == 0

    def test_linear_chain_depth(self):
        """A linear chain A->B->C->D has depth 3 (3 edges)."""
        G = nx.DiGraph()
        G.add_edges_from([("A", "B"), ("B", "C"), ("C", "D")])
        assert nesting_depth(G) == 3

    def test_diamond_depth(self):
        """A diamond graph A->B, A->C, B->D, C->D has depth 2."""
        G = nx.DiGraph()
        G.add_edges_from([("A", "B"), ("A", "C"), ("B", "D"), ("C", "D")])
        assert nesting_depth(G) == 2

    def test_non_dag_raises_error(self):
        """Calling nesting_depth on a non-DAG raises ValueError."""
        G = nx.DiGraph()
        G.add_edges_from([("A", "B"), ("B", "A")])
        with pytest.raises(ValueError, match="DAG"):
            nesting_depth(G)


class TestLongestPath:
    """Tests for the longest_path function."""

    def test_empty_graph_empty_path(self):
        """An empty graph returns an empty list."""
        G = nx.DiGraph()
        assert longest_path(G) == []

    def test_single_node_path(self):
        """A single node graph returns a path with one node."""
        G = nx.DiGraph()
        G.add_node("A")
        path = longest_path(G)
        assert len(path) == 1
        assert path[0] == "A"

    def test_linear_chain_path(self):
        """A linear chain returns the full chain."""
        G = nx.DiGraph()
        G.add_edges_from([("A", "B"), ("B", "C"), ("C", "D")])
        path = longest_path(G)
        assert path == ["A", "B", "C", "D"]

    def test_diamond_longest_path(self):
        """A diamond graph has longest path of length 2 (3 nodes)."""
        G = nx.DiGraph()
        G.add_edges_from([("A", "B"), ("A", "C"), ("B", "D"), ("C", "D")])
        path = longest_path(G)
        assert len(path) == 3
        assert path[0] == "A"
        assert path[-1] == "D"
        # Check it's a valid path
        for i in range(len(path) - 1):
            assert G.has_edge(path[i], path[i + 1])

    def test_non_dag_raises_error(self):
        """Calling longest_path on a non-DAG raises ValueError."""
        G = nx.DiGraph()
        G.add_edges_from([("A", "B"), ("B", "A")])
        with pytest.raises(ValueError, match="DAG"):
            longest_path(G)


class TestBranchingFactor:
    """Tests for the branching_factor function."""

    def test_empty_graph_branching_zero(self):
        """An empty graph has branching factor 0.0."""
        G = nx.DiGraph()
        assert branching_factor(G) == 0.0

    def test_single_node_branching_zero(self):
        """A single node with no edges has branching factor 0.0."""
        G = nx.DiGraph()
        G.add_node("A")
        assert branching_factor(G) == 0.0

    def test_linear_chain_branching(self):
        """A linear chain A->B->C has mean in-degree 2/3."""
        G = nx.DiGraph()
        G.add_edges_from([("A", "B"), ("B", "C")])
        # A: in=0, B: in=1, C: in=1 => mean = 2/3
        expected = 2.0 / 3.0
        assert np.isclose(branching_factor(G), expected)

    def test_star_graph_branching(self):
        """A star graph (center has in-degree N-1) has mean in-degree (N-1)/N."""
        G = nx.DiGraph()
        # Center "C", leaves "L1", "L2", "L3" all point to C
        G.add_edges_from([("L1", "C"), ("L2", "C"), ("L3", "C")])
        # L1:0, L2:0, L3:0, C:3 => mean = 3/4
        expected = 3.0 / 4.0
        assert np.isclose(branching_factor(G), expected)


class TestComputeGraphMetrics:
    """Tests for the compute_graph_metrics function."""

    def test_empty_graph_metrics(self):
        """Metrics for an empty graph."""
        G = nx.DiGraph()
        metrics = compute_graph_metrics(G)
        assert metrics["is_dag"] is True
        assert metrics["num_nodes"] == 0
        assert metrics["num_edges"] == 0
        assert metrics["nesting_depth"] == 0
        assert metrics["longest_path"] == []
        assert metrics["branching_factor"] == 0.0
        assert metrics["avg_out_degree"] == 0.0
        assert metrics["density"] == 0.0

    def test_simple_dag_metrics(self):
        """Metrics for a simple DAG."""
        G = nx.DiGraph()
        G.add_edges_from([("A", "B"), ("B", "C")])
        metrics = compute_graph_metrics(G)
        assert metrics["is_dag"] is True
        assert metrics["num_nodes"] == 3
        assert metrics["num_edges"] == 2
        assert metrics["nesting_depth"] == 2
        assert metrics["longest_path"] == ["A", "B", "C"]
        assert np.isclose(metrics["branching_factor"], 2.0 / 3.0)
        # avg_out_degree: A:1, B:1, C:0 => 2/3
        assert np.isclose(metrics["avg_out_degree"], 2.0 / 3.0)

    def test_non_dag_raises_error(self):
        """compute_graph_metrics raises ValueError for non-DAG."""
        G = nx.DiGraph()
        G.add_edges_from([("A", "B"), ("B", "A")])
        with pytest.raises(ValueError, match="DAG"):
            compute_graph_metrics(G)


class TestGraphFromDict:
    """Tests for the graph_from_dict function."""

    def test_empty_dict(self):
        """Empty dict creates empty graph."""
        G = graph_from_dict({})
        assert G.number_of_nodes() == 0
        assert G.number_of_edges() == 0

    def test_nodes_only(self):
        """Dict with only nodes."""
        G = graph_from_dict({"nodes": ["A", "B", "C"]})
        assert G.number_of_nodes() == 3
        assert G.number_of_edges() == 0
        assert set(G.nodes()) == {"A", "B", "C"}

    def test_edges_only(self):
        """Dict with only edges (nodes inferred)."""
        G = graph_from_dict({"edges": [("A", "B"), ("B", "C")]})
        assert G.number_of_nodes() == 3
        assert G.number_of_edges() == 2
        assert set(G.nodes()) == {"A", "B", "C"}

    def test_full_dict(self):
        """Dict with both nodes and edges."""
        G = graph_from_dict({
            "nodes": ["A", "B", "C", "D"],
            "edges": [("A", "B"), ("B", "C"), ("C", "D")]
        })
        assert G.number_of_nodes() == 4
        assert G.number_of_edges() == 3
        assert set(G.nodes()) == {"A", "B", "C", "D"}


class TestGraphToDict:
    """Tests for the graph_to_dict function."""

    def test_empty_graph_to_dict(self):
        """Empty graph converts to empty dict."""
        G = nx.DiGraph()
        d = graph_to_dict(G)
        assert d["nodes"] == []
        assert d["edges"] == []

    def test_graph_roundtrip(self):
        """Graph -> dict -> Graph should preserve structure."""
        G = nx.DiGraph()
        G.add_edges_from([("A", "B"), ("B", "C"), ("C", "D")])
        d = graph_to_dict(G)
        G2 = graph_from_dict(d)
        assert G2.number_of_nodes() == G.number_of_nodes()
        assert G2.number_of_edges() == G.number_of_edges()
        assert set(G2.nodes()) == set(G.nodes())
        assert set(G2.edges()) == set(G.edges())

    def test_graph_with_isolated_nodes(self):
        """Graph with isolated nodes preserves them."""
        G = nx.DiGraph()
        G.add_edges_from([("A", "B")])
        G.add_node("C")  # isolated
        d = graph_to_dict(G)
        G2 = graph_from_dict(d)
        assert "C" in G2.nodes()
        assert G2.number_of_nodes() == 3