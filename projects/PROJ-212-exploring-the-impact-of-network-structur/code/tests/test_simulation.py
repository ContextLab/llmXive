import pytest
import numpy as np
import networkx as nx
from scipy.integrate import solve_ivp
from unittest.mock import patch, MagicMock
from src.simulation import (
    check_disconnected,
    kuramoto_derivative,
    compute_order_parameter,
    run_kuramoto_simulation
)
from data_models import SynchronizationStatus

class TestCheckDisconnected:
    def test_connected_graph_returns_false(self):
        G = nx.complete_graph(10)
        assert check_disconnected(G) is False

    def test_disconnected_graph_returns_true(self):
        G = nx.Graph()
        G.add_nodes_from([1, 2, 3, 4])
        G.add_edges_from([(1, 2), (3, 4)])
        assert check_disconnected(G) is True

    def test_single_node_returns_false(self):
        G = nx.Graph()
        G.add_node(1)
        assert check_disconnected(G) is False

    def test_empty_graph_returns_true(self):
        G = nx.Graph()
        assert check_disconnected(G) is True

class TestKuramotoDerivative:
    def test_derivative_shape(self):
        N = 10
        y = np.random.rand(N)
        adj = np.random.rand(N, N)
        adj = (adj + adj.T) / 2  # Symmetric
        K = 1.0
        t = 0.0
        
        dtheta = kuramoto_derivative(t, y, adj, K)
        assert dtheta.shape == (N,)

    def test_zero_coupling(self):
        N = 5
        y = np.random.rand(N)
        adj = np.random.rand(N, N)
        K = 0.0
        t = 0.0
        
        dtheta = kuramoto_derivative(t, y, adj, K)
        # With K=0, derivative should be 0 (assuming omega=0)
        assert np.allclose(dtheta, 0.0)

class TestComputeOrderParameter:
    def test_perfect_sync(self):
        phases = np.ones(10) * 0.5
        R = compute_order_parameter(phases)
        assert np.isclose(R, 1.0)

    def test_random_phases(self):
        np.random.seed(42)
        phases = np.random.uniform(0, 2 * np.pi, 100)
        R = compute_order_parameter(phases)
        # For random phases, R should be close to 0
        assert R < 0.2

    def test_empty_array(self):
        R = compute_order_parameter(np.array([]))
        assert R == 0.0

class TestRunKuramotoSimulation:
    @pytest.fixture
    def ring_graph(self):
        # Ring graph N=200 as per task description
        return nx.cycle_graph(200)

    def test_disconnected_graph_returns_inf(self, ring_graph):
        # Make it disconnected
        G = ring_graph.copy()
        G.remove_edge(0, 1)
        G.remove_edge(100, 101)
        
        result = run_kuramoto_simulation(G, k_values=[0.5])
        assert result.critical_k == float('inf')
        assert result.status == SynchronizationStatus.DISCONNECTED
        assert result.metrics["is_disconnected"] is True

    def test_ring_graph_threshold_detection(self, ring_graph):
        # Analytical solution for ring graph: K_c = 2 / (pi * density of states at 0)
        # For identical oscillators, synchronization depends on coupling.
        # We test that the function runs and returns a finite value for a connected graph
        # with reasonable parameters.
        k_values = [0.1, 0.5, 1.0, 2.0]
        result = run_kuramoto_simulation(
            ring_graph,
            k_values=k_values,
            t_max=50.0,
            dt=0.1,
            r_threshold=0.8,
            t_stable_min=10.0,
            seed=42
        )
        
        # Should not be infinity for a connected graph
        assert result.critical_k != float('inf')
        assert result.status in [SynchronizationStatus.SYNCHRONIZED, SynchronizationStatus.NOT_SYNCHRONIZED]
        assert "critical_k" in result.metrics

    def test_small_network(self):
        G = nx.barabasi_albert_graph(20, 2)
        k_values = [0.1, 0.5, 1.0]
        result = run_kuramoto_simulation(G, k_values=k_values, t_max=20.0, dt=0.1, seed=42)
        
        assert result.critical_k != float('inf') or result.status == SynchronizationStatus.NOT_SYNCHRONIZED
        assert result.metrics["num_nodes"] == 20

class TestIntegrationEdgeCases:
    def test_single_node_simulation(self):
        G = nx.Graph()
        G.add_node(1)
        result = run_kuramoto_simulation(G, k_values=[1.0])
        # Single node is connected, but Kuramoto dynamics trivial
        # Should return a result, critical_k might be 0 or inf depending on logic
        assert isinstance(result.critical_k, float)

    def test_large_k_values(self):
        G = nx.complete_graph(50)
        k_values = [10.0, 20.0, 50.0]
        result = run_kuramoto_simulation(G, k_values=k_values, t_max=10.0, dt=0.1, seed=42)
        assert result.critical_k != float('inf')
        assert result.metrics["critical_k"] <= max(k_values)