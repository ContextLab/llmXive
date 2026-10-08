import pytest
import numpy as np
import networkx as nx
from scipy.integrate import solve_ivp
from unittest.mock import patch, MagicMock
from src.simulation import (
    check_disconnected,
    compute_order_parameter,
    kuramoto_derivative,
    run_kuramoto_simulation,
    find_critical_coupling,
    discrete_sweep_fallback,
    process_single_network
)
from data_models import SimulationResult, SynchronizationStatus

class TestCheckDisconnected:
    def test_disconnected_graph_returns_true(self):
        """Test that a graph with two disconnected components is detected."""
        G = nx.Graph()
        G.add_edges_from([(1, 2), (3, 4)])  # Two separate edges, no path between them
        assert check_disconnected(G) is True

    def test_connected_graph_returns_false(self):
        """Test that a connected graph is not flagged as disconnected."""
        G = nx.Graph()
        G.add_edges_from([(1, 2), (2, 3), (3, 4)])
        assert check_disconnected(G) is False

    def test_single_node_graph(self):
        """Test that a single node graph is considered connected."""
        G = nx.Graph()
        G.add_node(1)
        assert check_disconnected(G) is False

    def test_empty_graph(self):
        """Test that an empty graph is handled (treated as disconnected or edge case)."""
        G = nx.Graph()
        # NetworkX nx.is_connected raises on empty graph, so we expect our wrapper to handle it
        # Typically an empty graph is not considered connected for synchronization
        assert check_disconnected(G) is True

class TestComputeOrderParameter:
    def test_full_sync(self):
        """Test order parameter calculation for fully synchronized phases."""
        phases = np.array([0.0, 0.0, 0.0, 0.0])
        r = compute_order_parameter(phases)
        assert np.isclose(r, 1.0)

    def test_incoherent(self):
        """Test order parameter for incoherent phases (random)."""
        np.random.seed(42)
        phases = np.random.uniform(0, 2 * np.pi, 100)
        r = compute_order_parameter(phases)
        # For random phases, r should be close to 0 (small due to finite N)
        assert r < 0.2

class TestKuramotoDerivative:
    def test_derivative_shape(self):
        """Test that the derivative function returns correct shape."""
        t = 0.0
        y = np.zeros(10)
        K = 1.0
        omega = np.ones(10)
        dwdt = kuramoto_derivative(t, y, K, omega)
        assert len(dwdt) == 10

class TestRunKuramotoSimulation:
    def test_simulation_runs(self):
        """Test that the simulation runs without error."""
        G = nx.erdos_renyi_graph(20, 0.2, seed=42)
        K = 1.0
        result = run_kuramoto_simulation(G, K, t_max=10.0, dt=0.01)
        assert isinstance(result, SimulationResult)
        assert result.status == SynchronizationStatus.RUNNING  # Or SUCCESS depending on implementation
        assert len(result.phases_history) > 0

    def test_disconnected_graph_handling(self):
        """Test that running simulation on a disconnected graph returns infinity/null without running."""
        G = nx.Graph()
        G.add_edges_from([(1, 2), (3, 4)])  # Disconnected
        K = 1.0
        # The wrapper process_single_network should handle this, 
        # but if called directly, we expect the check to happen or result to be invalid.
        # Based on T015 requirement, the entry point should return infinity.
        # We test the logic flow in process_single_network below.

class TestFindCriticalCoupling:
    def test_bisection_search_logic(self):
        """Test the bisection search logic for finding critical K."""
        # Use a connected graph where synchronization is expected at some K
        G = nx.erdos_renyi_graph(50, 0.1, seed=42)
        # We expect a finite K to be found
        K_crit = find_critical_coupling(G)
        assert K_crit is not None
        assert K_crit >= 0

    def test_disconnected_graph_returns_inf(self):
        """Test that disconnected graphs return infinity for critical coupling."""
        G = nx.Graph()
        G.add_edges_from([(1, 2), (3, 4)])
        K_crit = find_critical_coupling(G)
        assert K_crit == float('inf')

class TestProcessSingleNetwork:
    def test_process_disconnected_graph(self):
        """Test that process_single_network returns infinity for disconnected graphs."""
        G = nx.Graph()
        G.add_edges_from([(1, 2), (3, 4)])
        result = process_single_network(G, network_id="test_disconnected")
        assert result.threshold == float('inf')
        assert result.status == SynchronizationStatus.DISCONNECTED

    def test_process_connected_graph(self):
        """Test that process_single_network runs simulation for connected graphs."""
        G = nx.erdos_renyi_graph(20, 0.2, seed=42)
        result = process_single_network(G, network_id="test_connected")
        assert result.threshold is not None
        assert result.threshold != float('inf')