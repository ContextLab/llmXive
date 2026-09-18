"""
Unit tests for data validators in src/validators.py.

Tests cover:
- Disconnected graph detection
- Graph validation with various edge cases
- Network list validation
- Simulation input validation
"""
import pytest
import networkx as nx
import numpy as np
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

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
        """Test that a connected graph is correctly identified."""
        G = nx.complete_graph(10)
        is_disconnected, sizes = check_disconnected_graph(G)
        assert not is_disconnected
        assert sizes == [10]
        
    def test_disconnected_graph(self):
        """Test that a disconnected graph is correctly identified."""
        G = nx.Graph()
        G.add_nodes_from(range(10))
        G.add_edges_from([(0, 1), (1, 2), (2, 0)])  # Component 1
        G.add_edges_from([(3, 4), (4, 5)])          # Component 2
        G.add_edges_from([(6, 7), (7, 8), (8, 9), (9, 6)])  # Component 3
        
        is_disconnected, sizes = check_disconnected_graph(G)
        assert is_disconnected
        assert sorted(sizes) == [3, 3, 4]
        
    def test_single_node(self):
        """Test that a single node graph is considered connected."""
        G = nx.Graph()
        G.add_node(0)
        is_disconnected, sizes = check_disconnected_graph(G)
        assert not is_disconnected
        assert sizes == [1]
        
    def test_empty_graph(self):
        """Test that an empty graph returns appropriate result."""
        G = nx.Graph()
        is_disconnected, sizes = check_disconnected_graph(G)
        assert is_disconnected
        assert sizes == []
        
    def test_invalid_input(self):
        """Test that non-graph input raises ValueError."""
        with pytest.raises(ValueError):
            check_disconnected_graph("not a graph")
            
    def test_ba_graph(self):
        """Test Barabási-Albert graph (typically connected)."""
        G = nx.barabasi_albert_graph(100, 3)
        is_disconnected, sizes = check_disconnected_graph(G)
        # BA graphs are usually connected, but can be disconnected for small m
        assert isinstance(is_disconnected, bool)
        assert isinstance(sizes, list)


class TestValidateGraph:
    """Tests for validate_graph function."""
    
    def test_valid_complete_graph(self):
        """Test validation of a valid complete graph."""
        G = nx.complete_graph(10)
        result = validate_graph(G)
        assert result['valid']
        assert len(result['errors']) == 0
        assert result['stats']['num_nodes'] == 10
        assert result['stats']['num_edges'] == 45
        
    def test_graph_too_small(self):
        """Test validation fails for graph too small."""
        G = nx.Graph()
        G.add_node(0)
        result = validate_graph(G, min_nodes=2)
        assert not result['valid']
        assert any("minimum" in e.lower() for e in result['errors'])
        
    def test_graph_too_large(self):
        """Test validation fails for graph too large."""
        G = nx.complete_graph(100)
        result = validate_graph(G, max_nodes=50)
        assert not result['valid']
        assert any("maximum" in e.lower() for e in result['errors'])
        
    def test_self_loops_not_allowed(self):
        """Test validation catches self-loops when not allowed."""
        G = nx.Graph()
        G.add_edges_from([(0, 1), (1, 2), (2, 0), (0, 0)])
        result = validate_graph(G, allow_self_loops=False)
        assert not result['valid']
        assert any("self-loop" in e.lower() for e in result['errors'])
        
    def test_self_loops_allowed(self):
        """Test validation passes with self-loops when allowed."""
        G = nx.Graph()
        G.add_edges_from([(0, 1), (1, 2), (2, 0), (0, 0)])
        result = validate_graph(G, allow_self_loops=True)
        assert result['valid']
        
    def test_isolated_nodes_warning(self):
        """Test that isolated nodes generate warnings."""
        G = nx.Graph()
        G.add_edges_from([(0, 1), (1, 2)])
        G.add_node(3)  # Isolated
        result = validate_graph(G)
        assert any("isolated" in w.lower() for w in result['warnings'])
        
    def test_disconnected_graph_warning(self):
        """Test that disconnected graphs generate warnings."""
        G = nx.Graph()
        G.add_edges_from([(0, 1), (2, 3)])  # Two components
        result = validate_graph(G)
        assert any("disconnected" in w.lower() for w in result['warnings'])
        
    def test_degree_statistics(self):
        """Test that degree statistics are computed."""
        G = nx.star_graph(5)  # One center, 5 leaves
        result = validate_graph(G)
        assert 'mean_degree' in result['stats']
        assert 'max_degree' in result['stats']
        assert 'min_degree' in result['stats']
        assert result['stats']['max_degree'] == 5
        assert result['stats']['min_degree'] == 1
        
    def test_invalid_input_type(self):
        """Test that non-graph input raises ValueError."""
        with pytest.raises(ValueError):
            validate_graph("not a graph")


class TestValidateNetworkList:
    """Tests for validate_network_list function."""
    
    def test_valid_list(self):
        """Test validation of a valid network list."""
        networks = [nx.complete_graph(5), nx.path_graph(5)]
        result = validate_network_list(networks)
        assert result['valid']
        assert result['stats']['valid_networks'] == 2
        assert result['stats']['num_networks'] == 2
        
    def test_empty_list(self):
        """Test validation fails for empty list."""
        result = validate_network_list([])
        assert not result['valid']
        assert any("minimum" in e.lower() for e in result['errors'])
        
    def test_list_too_small(self):
        """Test validation fails for list with too few networks."""
        networks = [nx.complete_graph(5)]
        result = validate_network_list(networks, min_networks=3)
        assert not result['valid']
        
    def test_list_too_large(self):
        """Test validation fails for list with too many networks."""
        networks = [nx.complete_graph(i) for i in range(1, 6)]
        result = validate_network_list(networks, max_networks=3)
        assert not result['valid']
        
    def test_mixed_validity(self):
        """Test validation with mixed valid/invalid networks."""
        networks = [
            nx.complete_graph(5),  # Valid
            nx.Graph(),             # Invalid (single node with min_nodes=2)
            nx.path_graph(5)
        ]
        result = validate_network_list(networks, min_nodes=2)
        assert not result['valid']  # Because one is invalid
        assert result['stats']['valid_networks'] == 2
        assert result['stats']['invalid_networks'] == 1
        
    def test_disconnected_networks_counted(self):
        """Test that disconnected networks are counted."""
        G1 = nx.complete_graph(5)
        G2 = nx.Graph()
        G2.add_edges_from([(0, 1), (2, 3)])  # Disconnected
        networks = [G1, G2]
        result = validate_network_list(networks)
        assert result['stats']['disconnected_networks'] == 1
        
    def test_networkgraph_objects(self):
        """Test validation with NetworkGraph dataclass objects."""
        G = nx.complete_graph(5)
        net = NetworkGraph(id="test_1", graph=G, metrics={})
        result = validate_network_list([net])
        assert result['valid']
        assert result['stats']['num_networks'] == 1


class TestValidateSimulationInputs:
    """Tests for validate_simulation_inputs function."""
    
    def test_valid_inputs(self):
        """Test validation of valid simulation inputs."""
        G = nx.complete_graph(10)
        K_values = [0.0, 0.5, 1.0, 1.5, 2.0]
        result = validate_simulation_inputs(
            G, K_values, t_max=100.0, dt=0.01
        )
        assert result['valid']
        assert len(result['errors']) == 0
        
    def test_empty_k_values(self):
        """Test validation fails for empty K_values."""
        G = nx.complete_graph(10)
        result = validate_simulation_inputs(
            G, [], t_max=100.0, dt=0.01
        )
        assert not result['valid']
        assert any("empty" in e.lower() for e in result['errors'])
        
    def test_negative_k_values(self):
        """Test validation fails for negative K_values."""
        G = nx.complete_graph(10)
        result = validate_simulation_inputs(
            G, [-0.5, 0.0, 0.5], t_max=100.0, dt=0.01
        )
        assert not result['valid']
        assert any("negative" in e.lower() for e in result['errors'])
        
    def test_invalid_t_max(self):
        """Test validation fails for non-positive t_max."""
        G = nx.complete_graph(10)
        result = validate_simulation_inputs(
            G, [0.5], t_max=-1.0, dt=0.01
        )
        assert not result['valid']
        
    def test_invalid_dt(self):
        """Test validation fails for non-positive dt."""
        G = nx.complete_graph(10)
        result = validate_simulation_inputs(
            G, [0.5], t_max=100.0, dt=-0.01
        )
        assert not result['valid']
        
    def test_dt_exceeds_t_max(self):
        """Test validation fails when dt > t_max."""
        G = nx.complete_graph(10)
        result = validate_simulation_inputs(
            G, [0.5], t_max=1.0, dt=2.0
        )
        assert not result['valid']
        
    def test_few_time_steps_warning(self):
        """Test warning for too few time steps."""
        G = nx.complete_graph(10)
        result = validate_simulation_inputs(
            G, [0.5], t_max=1.0, dt=0.1  # Only 10 steps
        )
        assert any("time steps" in w.lower() for w in result['warnings'])
        
    def test_mismatched_initial_conditions(self):
        """Test validation fails for mismatched initial conditions."""
        G = nx.complete_graph(10)
        initial = np.random.rand(5)  # Wrong size
        result = validate_simulation_inputs(
            G, [0.5], t_max=100.0, dt=0.01, initial_conditions=initial
        )
        assert not result['valid']
        assert any("length" in e.lower() for e in result['errors'])
        
    def test_non_finite_initial_conditions(self):
        """Test validation fails for non-finite initial conditions."""
        G = nx.complete_graph(10)
        initial = np.array([0.0, 1.0, np.nan, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0])
        result = validate_simulation_inputs(
            G, [0.5], t_max=100.0, dt=0.01, initial_conditions=initial
        )
        assert not result['valid']
        assert any("non-finite" in e.lower() for e in result['errors'])
        
    def test_disconnected_graph_suggestion(self):
        """Test that disconnected graphs get suggestions."""
        G = nx.Graph()
        G.add_edges_from([(0, 1), (2, 3)])  # Disconnected
        result = validate_simulation_inputs(
            G, [0.5], t_max=100.0, dt=0.01
        )
        assert any("disconnected" in w.lower() for w in result['warnings'])
        assert any("largest connected component" in s.lower() for s in result['suggestions'])
        
    def test_k_value_range_suggestions(self):
        """Test suggestions for unusual K value ranges."""
        G = nx.complete_graph(10)
        
        # Low K_max
        result = validate_simulation_inputs(
            G, [0.0, 0.1, 0.2], t_max=100.0, dt=0.01
        )
        assert any("maximum K value is low" in s.lower() for s in result['suggestions'])
        
        # High K_min
        result = validate_simulation_inputs(
            G, [3.0, 4.0, 5.0], t_max=100.0, dt=0.01
        )
        assert any("minimum K value is high" in s.lower() for s in result['suggestions'])
        
    def test_simulation_info_present(self):
        """Test that simulation info is included in result."""
        G = nx.complete_graph(10)
        result = validate_simulation_inputs(
            G, [0.0, 0.5, 1.0], t_max=100.0, dt=0.01
        )
        assert 'simulation_info' in result
        assert result['simulation_info']['n_nodes'] == 10
        assert result['simulation_info']['n_k_values'] == 3
        assert result['simulation_info']['t_max'] == 100.0
        assert result['simulation_info']['dt'] == 0.01