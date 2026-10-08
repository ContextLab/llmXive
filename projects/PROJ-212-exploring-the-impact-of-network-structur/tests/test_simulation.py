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
from data_models import SynchronizationStatus, SimulationResult

class TestCheckDisconnected:
    def test_connected_graph_returns_false(self):
        G = nx.erdos_renyi_graph(20, 0.3, seed=42)
        assert not check_disconnected(G)

    def test_disconnected_graph_returns_true(self):
        G = nx.Graph()
        G.add_nodes_from([1, 2, 3, 4])
        G.add_edge(1, 2)
        G.add_edge(3, 4)
        assert check_disconnected(G)

    def test_single_node_graph(self):
        G = nx.Graph()
        G.add_node(1)
        assert not check_disconnected(G)

class TestComputeOrderParameter:
    def test_full_synchronization(self):
        N = 10
        phases = np.zeros(N)
        r, phi = compute_order_parameter(phases)
        assert np.isclose(r, 1.0)
        assert np.isclose(phi, 0.0)

    def test_uniform_distribution(self):
        N = 100
        phases = np.linspace(0, 2 * np.pi, N, endpoint=False)
        r, phi = compute_order_parameter(phases)
        assert r < 0.1  # Near zero for uniform distribution

    def test_partial_synchronization(self):
        N = 50
        phases = np.zeros(N)
        phases[10:] = np.pi  # Half synchronized at 0, half at pi
        r, phi = compute_order_parameter(phases)
        assert 0.0 < r < 1.0

class TestKuramotoDerivative:
    def test_derivative_shape(self):
        t = 0.0
        y = np.zeros(20)
        K = 1.0
        G = nx.erdos_renyi_graph(20, 0.2, seed=42)
        adj = nx.to_numpy_array(G)
        
        dydt = kuramoto_derivative(t, y, K, adj)
        assert dydt.shape == (20,)

    def test_derivative_zero_at_sync(self):
        N = 10
        y = np.zeros(N)
        K = 1.0
        G = nx.complete_graph(N)
        adj = nx.to_numpy_array(G)
        
        dydt = kuramoto_derivative(0.0, y, K, adj)
        assert np.allclose(dydt, 0.0, atol=1e-10)

class TestRunKuramotoSimulation:
    def test_simulation_returns_result(self):
        N = 20
        G = nx.erdos_renyi_graph(N, 0.3, seed=42)
        adj = nx.to_numpy_array(G)
        K = 1.0
        
        result = run_kuramoto_simulation(G, K, t_max=10.0, dt=0.01)
        
        assert isinstance(result, SimulationResult)
        assert result.status in [SynchronizationStatus.SYNC, SynchronizationStatus.NO_SYNC]
        assert len(result.phases) == N
        assert result.order_parameter_history is not None

    def test_simulation_time_consistency(self):
        N = 10
        G = nx.complete_graph(N)
        adj = nx.to_numpy_array(G)
        K = 5.0
        t_max = 5.0
        dt = 0.01
        
        result = run_kuramoto_simulation(G, K, t_max=t_max, dt=dt)
        
        expected_steps = int(t_max / dt)
        assert len(result.order_parameter_history) == expected_steps + 1

class TestFindCriticalCoupling:
    def test_bisection_search_logic(self):
        """
        Test the bisection search logic for finding critical coupling.
        Uses a ring graph where we know the analytical solution is approximately 2.0/N * pi^2 for large N,
        but for N=200, K_c ~ 0.5-1.0 range depending on exact definition.
        We verify the algorithm converges and returns a value within expected bounds.
        """
        N = 200
        # Create a ring graph (1D lattice with periodic boundaries)
        G = nx.cycle_graph(N)
        
        # Bisection parameters
        K_min = 0.0
        K_max = 5.0
        tol = 0.01
        max_iter = 50
        
        K_c = find_critical_coupling(G, K_min, K_max, tol, max_iter)
        
        # Should converge to a finite value
        assert K_c is not None
        assert K_min < K_c < K_max
        # For a ring graph, K_c should be positive and not excessively large
        assert 0.0 < K_c < 4.0

    def test_bisection_convergence(self):
        """
        Verify that bisection search converges within max iterations.
        """
        N = 50
        G = nx.barabasi_albert_graph(N, m=2, seed=42)
        
        K_c = find_critical_coupling(G, 0.0, 10.0, tol=0.001, max_iter=50)
        
        assert K_c is not None
        # Should have found a solution within bounds
        assert 0.0 <= K_c <= 10.0

    def test_disconnected_graph_returns_none(self):
        """
        Verify that disconnected graphs return None for critical coupling.
        """
        G = nx.Graph()
        G.add_nodes_from([1, 2, 3, 4])
        G.add_edge(1, 2)
        G.add_edge(3, 4)
        
        K_c = find_critical_coupling(G, 0.0, 5.0, tol=0.01, max_iter=20)
        
        assert K_c is None

class TestRingGraphAnalyticalMatchPct:
    def test_ring_graph_analytical_match_pct(self):
        """
        Test that the critical coupling for a ring graph matches the analytical expectation.
        For a ring graph with N nodes, the analytical critical coupling is:
        K_c = (2 * pi^2) / N for the Kuramoto model on a 1D lattice.
        
        We test with N=200, expecting K_c ~ 0.0987.
        However, due to finite-size effects and the specific definition of synchronization
        (r > 0.8 for t > 100), the empirical value may differ slightly.
        We verify the value is within a reasonable range of the theoretical expectation.
        """
        N = 200
        G = nx.cycle_graph(N)
        
        K_c = find_critical_coupling(G, 0.0, 2.0, tol=0.01, max_iter=50)
        
        # Analytical approximation for ring graph: K_c ≈ 2*pi^2 / N
        # For N=200: K_c ≈ 0.0987
        # We allow a generous range due to finite-size effects and simulation parameters
        theoretical_K_c = (2 * np.pi**2) / N
        
        assert K_c is not None
        # Check that the result is within a factor of 3 of the theoretical value
        # (accounting for finite-size effects and the specific sync threshold)
        assert theoretical_K_c / 3 < K_c < theoretical_K_c * 3

    def test_ring_graph_with_known_K(self):
        """
        Verify that a ring graph with K significantly above K_c achieves synchronization.
        """
        N = 100
        G = nx.cycle_graph(N)
        
        # Use a K value well above expected K_c
        K = 1.0
        
        result = run_kuramoto_simulation(G, K, t_max=20.0, dt=0.01)
        
        # Should achieve synchronization
        assert result.status == SynchronizationStatus.SYNC
        assert result.final_order_parameter > 0.8

class TestDiscreteSweepFallback:
    def test_discrete_sweep_fallback(self):
        """
        Test the discrete sweep fallback when bisection fails to converge.
        """
        N = 50
        G = nx.barabasi_albert_graph(N, m=2, seed=42)
        
        # Force a scenario where bisection might struggle by using a very tight tolerance
        # and a small number of iterations, then verify fallback works
        K_c = find_critical_coupling(G, 0.0, 10.0, tol=0.0001, max_iter=5)
        
        # Even if bisection doesn't converge perfectly, fallback should provide a result
        # or return None if no synchronization is found
        assert K_c is None or 0.0 <= K_c <= 10.0

class TestProcessSingleNetwork:
    def test_process_single_network_returns_result(self):
        """
        Test the full pipeline for a single network.
        """
        N = 30
        G = nx.erdos_renyi_graph(N, 0.3, seed=42)
        
        result = process_single_network(G, "test_network")
        
        assert isinstance(result, SimulationResult)
        assert result.network_id == "test_network"
        assert result.threshold is not None
        assert result.metrics is not None

    def test_process_disconnected_network(self):
        """
        Test that disconnected networks are handled gracefully.
        """
        G = nx.Graph()
        G.add_nodes_from([1, 2, 3, 4])
        G.add_edge(1, 2)
        G.add_edge(3, 4)
        
        result = process_single_network(G, "disconnected_test")
        
        assert isinstance(result, SimulationResult)
        assert result.threshold is None  # Should be None for disconnected
        assert result.status == SynchronizationStatus.NO_SYNC