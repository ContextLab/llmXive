"""
Unit tests for src/validators.py
"""

import pytest
import networkx as nx
import numpy as np
from pathlib import Path
import sys

# Add src to path if needed
src_path = Path(__file__).parent.parent / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

from validators import (
    check_disconnected_graph,
    validate_graph,
    validate_network_list,
    validate_simulation_inputs
)
from data_models import NetworkGraph


class TestCheckDisconnectedGraph:
    """Tests for check_disconnected_graph function."""
    
    def test_connected_graph(self):
        """Test that a connected graph returns False for disconnected."""
        graph = nx.barabasi_albert_graph(100, 3)
        is_disconnected, num_components = check_disconnected_graph(graph)
        assert is_disconnected is False
        assert num_components == 1
        
    def test_disconnected_graph(self):
        """Test that a disconnected graph returns True."""
        graph = nx.Graph()
        graph.add_nodes_from(range(10))
        graph.add_edges_from([(0, 1), (1, 2)])  # Only 3 nodes connected
        graph.add_edges_from([(5, 6), (6, 7)])  # Another component
        # Nodes 3, 4, 8, 9 are isolated
        
        is_disconnected, num_components = check_disconnected_graph(graph)
        assert is_disconnected is True
        assert num_components > 1
        
    def test_single_node_graph(self):
        """Test graph with single node."""
        graph = nx.Graph()
        graph.add_node(0)
        
        is_disconnected, num_components = check_disconnected_graph(graph)
        assert is_disconnected is False
        assert num_components == 1
        
    def test_none_graph_raises_error(self):
        """Test that None graph raises ValueError."""
        with pytest.raises(ValueError, match="Graph cannot be None"):
            check_disconnected_graph(None)
            
    def test_empty_graph_raises_error(self):
        """Test that empty graph raises ValueError."""
        graph = nx.Graph()
        with pytest.raises(ValueError, match="Graph cannot be empty"):
            check_disconnected_graph(graph)

class TestValidateGraph:
    """Tests for validate_graph function."""
    
    def test_valid_graph(self):
        """Test validation of a valid graph."""
        graph = nx.barabasi_albert_graph(100, 3)
        is_valid, errors = validate_graph(graph)
        assert is_valid is True
        assert len(errors) == 0
        
    def test_small_graph_fails_min_nodes(self):
        """Test that graph with too few nodes fails."""
        graph = nx.Graph()
        graph.add_node(0)
        
        is_valid, errors = validate_graph(graph, min_nodes=2)
        assert is_valid is False
        assert any("nodes" in err for err in errors)
        
    def test_large_graph_fails_max_nodes(self):
        """Test that graph with too many nodes fails."""
        graph = nx.erdos_renyi_graph(10001, 0.01)
        
        is_valid, errors = validate_graph(graph, max_nodes=10000)
        assert is_valid is False
        assert any("maximum" in err.lower() for err in errors)
        
    def test_self_loop_rejected(self):
        """Test that self-loops are detected when not allowed."""
        graph = nx.Graph()
        graph.add_edge(0, 1)
        graph.add_edge(1, 1)  # Self-loop
        
        is_valid, errors = validate_graph(graph, allow_self_loops=False)
        assert is_valid is False
        assert any("self-loop" in err.lower() for err in errors)
        
    def test_self_loop_allowed(self):
        """Test that self-loops are allowed when permitted."""
        graph = nx.Graph()
        graph.add_edge(0, 1)
        graph.add_edge(1, 1)  # Self-loop
        
        is_valid, errors = validate_graph(graph, allow_self_loops=True)
        assert is_valid is True
        
    def test_isolated_nodes_detected(self):
        """Test that isolated nodes are detected."""
        graph = nx.Graph()
        graph.add_nodes_from(range(10))
        graph.add_edges_from([(0, 1), (1, 2), (2, 3)])
        # Nodes 4-9 are isolated
        
        is_valid, errors = validate_graph(graph)
        assert is_valid is False
        assert any("isolated" in err.lower() for err in errors)
        
    def test_networkgraph_wrapper(self):
        """Test validation with NetworkGraph dataclass."""
        nx_graph = nx.barabasi_albert_graph(50, 3)
        network_graph = NetworkGraph(id="test", graph=nx_graph, metrics={})
        
        is_valid, errors = validate_graph(network_graph)
        assert is_valid is True
        
    def test_none_graph_fails(self):
        """Test that None graph fails validation."""
        is_valid, errors = validate_graph(None)
        assert is_valid is False
        assert any("None" in err for err in errors)
        
    def test_invalid_type_fails(self):
        """Test that invalid graph type fails."""
        is_valid, errors = validate_graph("not a graph")
        assert is_valid is False
        assert any("Invalid graph type" in err for err in errors)

class TestValidateNetworkList:
    """Tests for validate_network_list function."""
    
    def test_valid_list(self):
        """Test validation of a list of valid graphs."""
        graphs = [nx.barabasi_albert_graph(50, 3) for _ in range(5)]
        
        is_valid, errors = validate_network_list(graphs)
        assert is_valid is True
        assert len(errors) == 0
        
    def test_empty_list_fails(self):
        """Test that empty list fails validation."""
        is_valid, errors = validate_network_list([])
        assert is_valid is False
        assert any("empty" in err.lower() for err in errors)
        
    def test_mixed_valid_invalid(self):
        """Test list with both valid and invalid graphs."""
        valid_graph = nx.barabasi_albert_graph(50, 3)
        invalid_graph = nx.Graph()
        invalid_graph.add_node(0)  # Too small
        
        graphs = [valid_graph, invalid_graph, valid_graph]
        
        is_valid, errors = validate_network_list(graphs)
        assert is_valid is False
        assert len(errors) > 0
        
    def test_dict_networks(self):
        """Test validation of list of dictionaries."""
        nx_graph = nx.barabasi_albert_graph(50, 3)
        networks = [
            {"id": "test1", "graph": nx_graph},
            {"id": "test2", "graph": nx_graph}
        ]
        
        is_valid, errors = validate_network_list(networks)
        assert is_valid is True
        
    def test_dict_without_graph_key(self):
        """Test dict without 'graph' key fails."""
        networks = [
            {"id": "test1", "data": "something"}
        ]
        
        is_valid, errors = validate_network_list(networks)
        assert is_valid is False
        assert any("without 'graph' key" in err for err in errors)

class TestValidateSimulationInputs:
    """Tests for validate_simulation_inputs function."""
    
    def test_valid_inputs(self):
        """Test validation of valid simulation inputs."""
        graph = nx.barabasi_albert_graph(100, 3)
        freqs = np.random.randn(100)
        
        is_valid, errors = validate_simulation_inputs(
            graph=graph,
            natural_frequencies=freqs,
            coupling_strength=1.0,
            time_span=(0.0, 100.0),
            num_oscillators=100
        )
        assert is_valid is True
        assert len(errors) == 0
        
    def test_mismatched_oscillator_count(self):
        """Test that mismatched oscillator count fails."""
        graph = nx.barabasi_albert_graph(100, 3)
        freqs = np.random.randn(50)  # Wrong size
        
        is_valid, errors = validate_simulation_inputs(
            graph=graph,
            natural_frequencies=freqs,
            num_oscillators=100
        )
        assert is_valid is False
        assert any("does not match" in err for err in errors)
        
    def test_negative_coupling_strength(self):
        """Test that negative coupling strength fails."""
        graph = nx.barabasi_albert_graph(100, 3)
        
        is_valid, errors = validate_simulation_inputs(
            graph=graph,
            coupling_strength=-1.0
        )
        assert is_valid is False
        assert any("negative" in err.lower() for err in errors)
        
    def test_invalid_time_span(self):
        """Test that invalid time span fails."""
        graph = nx.barabasi_albert_graph(100, 3)
        
        is_valid, errors = validate_simulation_inputs(
            graph=graph,
            time_span=(100.0, 0.0)  # End before start
        )
        assert is_valid is False
        assert any("start must be less than end" in err for err in errors)
        
    def test_nan_frequencies(self):
        """Test that NaN frequencies fail."""
        graph = nx.barabasi_albert_graph(100, 3)
        freqs = np.random.randn(100)
        freqs[0] = np.nan
        
        is_valid, errors = validate_simulation_inputs(
            graph=graph,
            natural_frequencies=freqs
        )
        assert is_valid is False
        assert any("NaN" in err for err in errors)
        
    def test_inf_frequencies(self):
        """Test that Inf frequencies fail."""
        graph = nx.barabasi_albert_graph(100, 3)
        freqs = np.random.randn(100)
        freqs[0] = np.inf
        
        is_valid, errors = validate_simulation_inputs(
            graph=graph,
            natural_frequencies=freqs
        )
        assert is_valid is False
        assert any("Inf" in err for err in errors)
        
    def test_none_graph_fails(self):
        """Test that None graph fails."""
        is_valid, errors = validate_simulation_inputs(graph=None)
        assert is_valid is False
        assert any("Graph is None" in err for err in errors)
        
    def test_empty_graph_fails(self):
        """Test that empty graph fails."""
        graph = nx.Graph()
        
        is_valid, errors = validate_simulation_inputs(graph=graph)
        assert is_valid is False
        assert any("no nodes" in err.lower() for err in errors)
        
    def test_default_values_work(self):
        """Test that missing optional parameters use defaults."""
        graph = nx.barabasi_albert_graph(100, 3)
        
        # Should not raise errors, just use defaults
        is_valid, errors = validate_simulation_inputs(graph=graph)
        assert is_valid is True