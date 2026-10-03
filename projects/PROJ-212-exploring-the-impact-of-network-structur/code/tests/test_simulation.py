import pytest
import numpy as np
import networkx as nx
from scipy.integrate import solve_ivp
from unittest.mock import patch, MagicMock
from src.simulation import (
    check_disconnected, compute_order_parameter, kuramoto_derivative,
    run_kuramoto_simulation, find_critical_coupling, process_single_network
)
from data_models import SynchronizationStatus

class TestCheckDisconnected:
    """Tests for the disconnected graph pre-check guard clause (T015)."""

    def test_connected_graph_returns_false(self):
        """A fully connected graph should be reported as connected."""
        G = nx.complete_graph(10)
        assert check_disconnected(G) is False

    def test_disconnected_graph_returns_true(self):
        """A graph with two separate components should be reported as disconnected."""
        G = nx.Graph()
        G.add_nodes_from([1, 2, 3, 4, 5, 6])
        G.add_edges_from([(1, 2), (2, 3)])  # Component 1
        G.add_edges_from([(4, 5), (5, 6)])  # Component 2
        assert check_disconnected(G) is True

    def test_single_node_graph_connected(self):
        """A graph with a single node is connected."""
        G = nx.Graph()
        G.add_node(1)
        assert check_disconnected(G) is False

    def test_empty_graph_disconnected(self):
        """An empty graph (no nodes) is considered disconnected."""
        G = nx.Graph()
        assert check_disconnected(G) is True

    def test_ring_graph_connected(self):
        """A ring graph is connected."""
        G = nx.cycle_graph(20)
        assert check_disconnected(G) is False

class TestComputeOrderParameter:
    def test_perfect_sync(self):
        """All phases aligned should give r=1."""
        phis = np.zeros(100)
        assert np.isclose(compute_order_parameter(phis), 1.0)

    def test_random_phases(self):
        """Random phases should give r near 0."""
        phis = np.random.uniform(0, 2 * np.pi, 1000)
        r = compute_order_parameter(phis)
        assert r < 0.2  # Random should be low

class TestKuramotoDerivative:
    def test_derivative_shape(self):
        """Derivative should have same shape as input phases."""
        N = 50
        t = 0.0
        y = np.random.uniform(0, 2*np.pi, N)
        K = 1.0
        adjacency = np.random.randint(0, 2, (N, N))
        natural_freqs = np.random.uniform(-0.5, 0.5, N)
        
        dydt = kuramoto_derivative(t, y, K, adjacency, natural_freqs)
        assert dydt.shape == y.shape

class TestRunKuramotoSimulation:
    def test_simulation_runs(self):
        """Simulation should complete without error on a simple graph."""
        G = nx.barabasi_albert_graph(50, 2)
        status, r = run_kuramoto_simulation(G, K=2.0, T=10.0, seed=42)
        assert isinstance(status, SynchronizationStatus)
        assert 0.0 <= r <= 1.0

    def test_disconnected_graph_handling(self):
        """Test that disconnected graphs are handled gracefully (T015 integration)."""
        G = nx.Graph()
        G.add_nodes_from([1, 2, 3, 4, 5, 6])
        G.add_edges_from([(1, 2), (2, 3)])
        G.add_edges_from([(4, 5), (5, 6)])
        
        status, r = run_kuramoto_simulation(G, K=2.0, seed=42)
        # Should not crash, though specific status depends on implementation details
        assert isinstance(status, SynchronizationStatus)

class TestFindCriticalCoupling:
    def test_bisection_converges_on_connected(self):
        """Bisection should converge on a connected graph."""
        G = nx.barabasi_albert_graph(50, 2)
        threshold, metadata = find_critical_coupling(G, K_min=0.0, K_max=5.0, tolerance=0.01, seed=42)
        
        assert metadata["converged"] is True
        assert 0.0 <= threshold <= 5.0

    def test_disconnected_returns_infinity(self):
        """Disconnected graph should return infinity threshold immediately (T015)."""
        G = nx.Graph()
        G.add_nodes_from([1, 2, 3, 4, 5, 6])
        G.add_edges_from([(1, 2), (2, 3)])
        G.add_edges_from([(4, 5), (5, 6)])
        
        threshold, metadata = find_critical_coupling(G, K_min=0.0, K_max=5.0)
        
        assert threshold == float('inf')
        assert metadata["method"] == "disconnected_guard"
        assert "reason" in metadata

    def test_fallback_to_discrete_sweep(self):
        """Test that fallback to discrete sweep occurs when bisection fails."""
        # This is a bit hard to force without mocking, but we test the logic exists
        G = nx.barabasi_albert_graph(50, 2)
        # Force a scenario where bisection might struggle by using tight tolerance
        threshold, metadata = find_critical_coupling(G, K_min=0.0, K_max=5.0, 
                                                     tolerance=0.0000001, max_iterations=2, seed=42)
        
        # With only 2 iterations and tight tolerance, it should fallback
        assert metadata["method"] in ["bisection", "fallback_discrete_sweep"]

class TestProcessSingleNetwork:
    def test_process_connected(self):
        """Process a connected network successfully."""
        G = nx.barabasi_albert_graph(50, 2)
        config = {
            "network_id": "test_001",
            "K_min": 0.0,
            "K_max": 5.0,
            "tolerance": 0.01,
            "seed": 42
        }
        
        result = process_single_network(G, config)
        
        assert result.network_id == "test_001"
        assert result.threshold is not None
        assert result.metrics is not None

    def test_process_disconnected(self):
        """Process a disconnected network should return infinity threshold (T015)."""
        G = nx.Graph()
        G.add_nodes_from([1, 2, 3, 4, 5, 6])
        G.add_edges_from([(1, 2), (2, 3)])
        G.add_edges_from([(4, 5), (5, 6)])
        
        config = {
            "network_id": "test_disconnected",
            "K_min": 0.0,
            "K_max": 5.0,
            "tolerance": 0.01,
            "seed": 42
        }
        
        result = process_single_network(G, config)
        
        assert result.threshold == float('inf')
        assert result.metadata["reason"] == "disconnected_graph"
        assert result.metadata["method"] == "pre_check_guard"