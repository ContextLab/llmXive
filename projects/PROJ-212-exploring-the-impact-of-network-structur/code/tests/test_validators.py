"""
Unit tests for src/validators.py

Tests cover:
- Disconnected graph detection
- Graph validation (self-loops, multi-edges, connectivity)
- Network list validation
- Simulation input validation
"""

import pytest
import networkx as nx
import numpy as np
from pathlib import Path
import sys

from src.validators import (
    check_disconnected_graph,
    validate_graph,
    validate_network_list,
    validate_simulation_inputs
)
from data_models import NetworkGraph


class TestCheckDisconnectedGraph:
    """Tests for check_disconnected_graph function."""

    def test_connected_graph(self):
        """Test that a connected graph returns False."""
        G = nx.barbell_graph(10, 5)  # Two cliques connected by a path
        assert check_disconnected_graph(G) is False

    def test_disconnected_graph(self):
        """Test that a disconnected graph returns True."""
        G = nx.disjoint_union(
            nx.complete_graph(5),
            nx.complete_graph(5)
        )
        assert check_disconnected_graph(G) is True

    def test_single_node_graph(self):
        """Test that a single-node graph is considered connected."""
        G = nx.Graph()
        G.add_node(1)
        assert check_disconnected_graph(G) is False

    def test_empty_graph(self):
        """Test that an empty graph is considered disconnected."""
        G = nx.Graph()
        assert check_disconnected_graph(G) is True

    def test_two_nodes_no_edge(self):
        """Test that two nodes with no edge is disconnected."""
        G = nx.Graph()
        G.add_nodes_from([1, 2])
        assert check_disconnected_graph(G) is True

    def test_two_nodes_with_edge(self):
        """Test that two nodes with an edge is connected."""
        G = nx.Graph()
        G.add_nodes_from([1, 2])
        G.add_edge(1, 2)
        assert check_disconnected_graph(G) is False

    def test_networkgraph_wrapper(self):
        """Test that NetworkGraph wrapper is handled correctly."""
        G = nx.Graph()
        G.add_nodes_from([1, 2, 3])
        G.add_edges_from([(1, 2), (2, 3)])
        network_graph = NetworkGraph(graph=G, id="test", source="test")
        assert check_disconnected_graph(network_graph) is False


class TestValidateGraph:
    """Tests for validate_graph function."""

    def test_valid_connected_graph(self):
        """Test validation of a valid connected graph."""
        G = nx.erdos_renyi_graph(20, 0.3, seed=42)
        result = validate_graph(G, name="test_valid")
        assert result["valid"] is True
        assert result["is_connected"] is True
        assert len(result["errors"]) == 0
        assert result["node_count"] == 20

    def test_graph_with_self_loops(self):
        """Test validation of a graph with self-loops."""
        G = nx.Graph()
        G.add_nodes_from([1, 2, 3])
        G.add_edges_from([(1, 2), (2, 3), (1, 1)])  # Self-loop on 1
        result = validate_graph(G, name="test_self_loop")
        assert result["valid"] is True  # Still valid, just a warning
        assert result["has_self_loops"] is True
        assert len(result["warnings"]) > 0
        assert any("self-loop" in w for w in result["warnings"])

    def test_disconnected_graph_validation(self):
        """Test validation of a disconnected graph."""
        G = nx.disjoint_union(nx.complete_graph(5), nx.complete_graph(5))
        result = validate_graph(G, name="test_disconnected")
        assert result["valid"] is True  # Still valid, just a warning
        assert result["is_connected"] is False
        assert len(result["warnings"]) > 0
        assert any("disconnected" in w.lower() for w in result["warnings"])

    def test_empty_graph_validation(self):
        """Test validation of an empty graph."""
        G = nx.Graph()
        result = validate_graph(G, name="test_empty")
        assert result["valid"] is False
        assert len(result["errors"]) > 0
        assert any("empty" in e.lower() for e in result["errors"])

    def test_graph_with_no_edges(self):
        """Test validation of a graph with nodes but no edges."""
        G = nx.Graph()
        G.add_nodes_from([1, 2, 3])
        result = validate_graph(G, name="test_no_edges")
        assert result["valid"] is False
        assert len(result["errors"]) > 0
        assert any("no edges" in e.lower() for e in result["errors"])

    def test_single_node_graph(self):
        """Test validation of a single-node graph."""
        G = nx.Graph()
        G.add_node(1)
        result = validate_graph(G, name="test_single")
        assert result["valid"] is True  # Technically valid
        assert len(result["warnings"]) > 0
        assert any("fewer than 2 nodes" in w for w in result["warnings"])

    def test_networkgraph_wrapper(self):
        """Test validation with NetworkGraph wrapper."""
        G = nx.barbell_graph(10, 5)
        network_graph = NetworkGraph(graph=G, id="test", source="test")
        result = validate_graph(network_graph, name="test_wrapper")
        assert result["valid"] is True
        assert result["is_connected"] is True


class TestValidateNetworkList:
    """Tests for validate_network_list function."""

    def test_valid_list(self):
        """Test validation of a list of valid graphs."""
        graphs = [
            nx.erdos_renyi_graph(20, 0.3, seed=i)
            for i in range(3)
        ]
        result = validate_network_list(graphs)
        assert result["total_count"] == 3
        assert result["valid_count"] == 3
        assert result["invalid_count"] == 0
        assert len(result["results"]) == 3

    def test_mixed_validity(self):
        """Test validation of a list with mixed validity."""
        graphs = [
            nx.erdos_renyi_graph(20, 0.3, seed=0),  # Valid
            nx.Graph(),  # Invalid (empty)
            nx.disjoint_union(nx.complete_graph(5), nx.complete_graph(5)),  # Valid but disconnected
        ]
        result = validate_network_list(graphs)
        assert result["total_count"] == 3
        assert result["valid_count"] == 2
        assert result["invalid_count"] == 1
        assert result["disconnected_count"] == 1

    def test_empty_list(self):
        """Test validation of an empty list."""
        result = validate_network_list([])
        assert result["total_count"] == 0
        assert result["valid_count"] == 0
        assert result["invalid_count"] == 0
        assert len(result["results"]) == 0

    def test_invalid_input_type(self):
        """Test that non-list input raises TypeError."""
        with pytest.raises(TypeError):
            validate_network_list("not a list")


class TestValidateSimulationInputs:
    """Tests for validate_simulation_inputs function."""

    def test_valid_inputs(self):
        """Test validation with valid inputs."""
        G = nx.erdos_renyi_graph(20, 0.3, seed=42)
        result = validate_simulation_inputs(
            G,
            coupling_range=(0.0, 5.0),
            tolerance=0.001,
            max_iterations=1000,
            time_steps=1000,
            dt=0.01
        )
        assert result["valid"] is True
        assert len(result["errors"]) == 0

    def test_invalid_coupling_range(self):
        """Test validation with invalid coupling range."""
        G = nx.erdos_renyi_graph(20, 0.3, seed=42)
        result = validate_simulation_inputs(
            G,
            coupling_range=(5.0, 0.0),  # min > max
            tolerance=0.001
        )
        assert result["valid"] is False
        assert len(result["errors"]) > 0
        assert any("min coupling" in e.lower() for e in result["errors"])

    def test_negative_coupling(self):
        """Test validation with negative coupling."""
        G = nx.erdos_renyi_graph(20, 0.3, seed=42)
        result = validate_simulation_inputs(
            G,
            coupling_range=(-1.0, 5.0)
        )
        assert result["valid"] is False
        assert any("non-negative" in e.lower() for e in result["errors"])

    def test_invalid_tolerance(self):
        """Test validation with invalid tolerance."""
        G = nx.erdos_renyi_graph(20, 0.3, seed=42)
        result = validate_simulation_inputs(
            G,
            tolerance=-0.001
        )
        assert result["valid"] is False
        assert any("tolerance" in e.lower() for e in result["errors"])

    def test_large_tolerance_warning(self):
        """Test warning for large tolerance."""
        G = nx.erdos_renyi_graph(20, 0.3, seed=42)
        result = validate_simulation_inputs(
            G,
            tolerance=0.5
        )
        assert result["valid"] is True
        assert len(result["warnings"]) > 0
        assert any("large" in w.lower() for w in result["warnings"])

    def test_invalid_max_iterations(self):
        """Test validation with invalid max iterations."""
        G = nx.erdos_renyi_graph(20, 0.3, seed=42)
        result = validate_simulation_inputs(
            G,
            max_iterations=-10
        )
        assert result["valid"] is False
        assert any("positive" in e.lower() for e in result["errors"])

    def test_small_max_iterations_warning(self):
        """Test warning for small max iterations."""
        G = nx.erdos_renyi_graph(20, 0.3, seed=42)
        result = validate_simulation_inputs(
            G,
            max_iterations=5
        )
        assert result["valid"] is True
        assert len(result["warnings"]) > 0
        assert any("low" in w.lower() for w in result["warnings"])

    def test_invalid_dt(self):
        """Test validation with invalid dt."""
        G = nx.erdos_renyi_graph(20, 0.3, seed=42)
        result = validate_simulation_inputs(
            G,
            dt=-0.01
        )
        assert result["valid"] is False
        assert any("positive" in e.lower() for e in result["errors"])

    def test_large_dt_warning(self):
        """Test warning for large dt."""
        G = nx.erdos_renyi_graph(20, 0.3, seed=42)
        result = validate_simulation_inputs(
            G,
            dt=0.5
        )
        assert result["valid"] is True
        assert len(result["warnings"]) > 0
        assert any("large" in w.lower() for w in result["warnings"])

    def test_disconnected_graph_warning(self):
        """Test warning for disconnected graph."""
        G = nx.disjoint_union(nx.complete_graph(5), nx.complete_graph(5))
        result = validate_simulation_inputs(G)
        assert result["valid"] is True
        assert len(result["warnings"]) > 0
        assert any("disconnected" in w.lower() for w in result["warnings"])

    def test_empty_graph_error(self):
        """Test error for empty graph."""
        G = nx.Graph()
        result = validate_simulation_inputs(G)
        assert result["valid"] is False
        assert len(result["errors"]) > 0
        assert any("empty" in e.lower() for e in result["errors"])