"""
Unit tests for metrics.py functions.
Specifically covers Global Connectivity (T018) and Average Branching Factor (T019).
"""
import pytest
import networkx as nx
import json
import os
import csv
import tempfile
from pathlib import Path
from typing import Dict, List, Any, Optional

# Import the function under test from the sibling module
from metrics import load_graph_from_json, calculate_global_connectivity, calculate_avg_branching_factor


class TestCalculateGlobalConnectivity:
    """Tests for T018: Global Connectivity calculation."""

    def test_empty_graph(self):
        """Test that empty graph (0 nodes) returns 0.0."""
        G = nx.DiGraph()
        assert calculate_global_connectivity(G) == 0.0

    def test_single_node(self):
        """Test single node graph (0 edges) returns 0.0."""
        G = nx.DiGraph()
        G.add_node(1)
        assert calculate_global_connectivity(G) == 0.0

    def test_simple_dag(self):
        """
        Test a simple DAG: 3 nodes, 2 edges (1->2, 2->3).
        Max edges for N=3 is 3*(2) = 6.
        Connectivity = 2 / 6 = 0.3333...
        """
        G = nx.DiGraph()
        G.add_edges_from([(1, 2), (2, 3)])
        expected = 2 / (3 * (3 - 1))
        assert abs(calculate_global_connectivity(G) - expected) < 1e-9

    def test_complete_graph(self):
        """
        Test a complete directed graph: 3 nodes, 6 edges (all possible).
        Connectivity = 6 / 6 = 1.0
        """
        G = nx.DiGraph()
        G.add_edges_from([(1, 2), (1, 3), (2, 1), (2, 3), (3, 1), (3, 2)])
        expected = 1.0
        assert abs(calculate_global_connectivity(G) - expected) < 1e-9


class TestCalculateAvgBranchingFactor:
    """Tests for T019: Average Branching Factor calculation."""

    def test_empty_graph(self):
        """Test that empty graph (0 nodes) returns 0.0."""
        G = nx.DiGraph()
        assert calculate_avg_branching_factor(G) == 0.0

    def test_single_node(self):
        """Test single node graph (0 edges) returns 0.0."""
        G = nx.DiGraph()
        G.add_node(1)
        assert calculate_avg_branching_factor(G) == 0.0

    def test_simple_dag(self):
        """
        Test a simple DAG: 3 nodes, 2 edges (1->2, 2->3).
        Out-degrees: Node 1: 1, Node 2: 1, Node 3: 0.
        Sum of out-degrees = 2.
        Avg Branching = 2 / 3 = 0.6666...
        """
        G = nx.DiGraph()
        G.add_edges_from([(1, 2), (2, 3)])
        expected = 2 / 3
        assert abs(calculate_avg_branching_factor(G) - expected) < 1e-9

    def test_star_graph(self):
        """
        Test a star graph: Center node 1 connects to 2, 3, 4.
        Out-degrees: Node 1: 3, Nodes 2,3,4: 0.
        Sum of out-degrees = 3.
        Avg Branching = 3 / 4 = 0.75.
        """
        G = nx.DiGraph()
        G.add_edges_from([(1, 2), (1, 3), (1, 4)])
        expected = 3 / 4
        assert abs(calculate_avg_branching_factor(G) - expected) < 1e-9

    def test_known_small_graph(self):
        """
        Explicit test case from task description:
        Feed a known small graph (3 nodes, 2 edges).
        Verify output matches mathematically derived values exactly.
        Graph: 1->2, 2->3.
        Expected Avg Branching: 2/3.
        """
        G = nx.DiGraph()
        G.add_node(1)
        G.add_node(2)
        G.add_node(3)
        G.add_edge(1, 2)
        G.add_edge(2, 3)

        result = calculate_avg_branching_factor(G)
        expected = 2.0 / 3.0

        assert isinstance(result, float)
        assert abs(result - expected) < 1e-9, f"Expected {expected}, got {result}"


class TestLoadGraphFromJson:
    """Tests for the graph loading utility."""

    def test_load_valid_graph(self):
        """Test loading a valid graph from a temporary JSON file."""
        G = nx.DiGraph()
        G.add_edges_from([(1, 2), (2, 3)])

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_path = f.name
            json.dump(list(G.edges()), f)

        try:
            loaded_G = load_graph_from_json(temp_path)
            assert loaded_G.number_of_nodes() == 3
            assert loaded_G.number_of_edges() == 2
        finally:
            os.unlink(temp_path)

    def test_load_empty_graph(self):
        """Test loading an empty graph (just nodes, no edges)."""
        G = nx.DiGraph()
        G.add_node(1)
        G.add_node(2)

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_path = f.name
            json.dump([], f) # Empty edge list

        try:
            loaded_G = load_graph_from_json(temp_path)
            # Note: load_graph_from_json typically creates graph from edges.
            # If nodes are isolated and not in edges, they might not appear
            # unless the JSON format stores nodes explicitly.
            # Assuming the standard format stores edges:
            assert loaded_G.number_of_edges() == 0
        finally:
            os.unlink(temp_path)