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
    def test_connected_graph(self):
        G = nx.barabasi_albert_graph(100, 3)
        assert not check_disconnected_graph(G)

    def test_disconnected_graph(self):
        G1 = nx.barabasi_albert_graph(50, 3)
        G2 = nx.barabasi_albert_graph(50, 3)
        G = nx.disjoint_union(G1, G2)
        assert check_disconnected_graph(G)

    def test_empty_graph(self):
        G = nx.Graph()
        with pytest.raises((ValueError, nx.NetworkXError)):
            # Empty graph behavior: returns True with warning, or raises?
            # Our implementation returns True with a warning for empty graph.
            result = check_disconnected_graph(G)
            assert result is True

    def test_network_graph_wrapper(self):
        G = nx.Graph()
        G.add_edge(1, 2)
        G.add_edge(3, 4)  # Disconnected
        wrapped = NetworkGraph(graph=G, id="test")
        assert check_disconnected_graph(wrapped)

class TestValidateGraph:
    def test_valid_connected_graph(self):
        G = nx.barabasi_albert_graph(100, 3)
        result = validate_graph(G)
        assert result["is_valid"] is True
        assert result["node_count"] == 100
        assert len(result["errors"]) == 0

    def test_graph_with_self_loops(self):
        G = nx.Graph()
        G.add_edge(1, 2)
        G.add_loop(1)
        result = validate_graph(G)
        assert result["is_valid"] is True  # Self-loops are warnings, not errors
        assert any("self-loop" in w for w in result["warnings"])

    def test_empty_graph(self):
        G = nx.Graph()
        result = validate_graph(G)
        assert result["is_valid"] is False
        assert any("empty" in e.lower() for e in result["errors"])

    def test_disconnected_graph_warning(self):
        G = nx.Graph()
        G.add_edge(1, 2)
        G.add_edge(3, 4)
        result = validate_graph(G)
        assert result["is_valid"] is True  # Disconnected is a warning, not a hard error
        assert any("not connected" in w for w in result["warnings"])

class TestValidateNetworkList:
    def test_valid_list(self):
        graphs = [nx.barabasi_albert_graph(50, 3) for _ in range(5)]
        result = validate_network_list(graphs)
        assert result["is_valid"] is True
        assert result["valid_count"] == 5
        assert len(result["invalid_indices"]) == 0

    def test_list_with_invalid(self):
        graphs = [
            nx.barabasi_albert_graph(50, 3),
            nx.Graph(),  # Empty
            nx.barabasi_albert_graph(50, 3)
        ]
        result = validate_network_list(graphs)
        assert result["is_valid"] is False
        assert result["valid_count"] == 2
        assert 1 in result["invalid_indices"]

    def test_non_list_input(self):
        with pytest.raises(TypeError):
            validate_network_list(nx.barabasi_albert_graph(10, 3))

class TestValidateSimulationInputs:
    def test_valid_inputs(self):
        G = nx.barabasi_albert_graph(100, 3)
        result = validate_simulation_inputs(G, coupling_range=(0.0, 5.0), tolerance=0.001)
        assert result["is_valid"] is True
        assert result["ready_for_simulation"] is True

    def test_invalid_coupling_range(self):
        G = nx.barabasi_albert_graph(100, 3)
        result = validate_simulation_inputs(G, coupling_range=(5.0, 0.0), tolerance=0.001)
        assert result["is_valid"] is False
        assert result["ready_for_simulation"] is False
        assert any("coupling range" in e for e in result["errors"])

    def test_invalid_tolerance(self):
        G = nx.barabasi_albert_graph(100, 3)
        result = validate_simulation_inputs(G, coupling_range=(0.0, 5.0), tolerance=-0.001)
        assert result["is_valid"] is False
        assert result["ready_for_simulation"] is False
        assert any("tolerance" in e for e in result["errors"])

    def test_disconnected_graph_warning(self):
        G1 = nx.barabasi_albert_graph(50, 3)
        G2 = nx.barabasi_albert_graph(50, 3)
        G = nx.disjoint_union(G1, G2)
        result = validate_simulation_inputs(G)
        assert result["is_valid"] is True  # Graph is structurally valid
        assert result["ready_for_simulation"] is True
        assert any("disconnected" in w for w in result["warnings"])