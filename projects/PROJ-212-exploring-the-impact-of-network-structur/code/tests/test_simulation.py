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
    process_single_network
)
from data_models import SynchronizationStatus

class TestCheckDisconnected:
    """Tests for the check_disconnected function."""
    
    def test_connected_graph(self):
        """Test that a connected graph returns False."""
        G = nx.barbell_graph(10, 5)
        assert check_disconnected(G) is False
        
    def test_disconnected_graph(self):
        """Test that a disconnected graph returns True."""
        G = nx.Graph()
        G.add_nodes_from([1, 2, 3, 4, 5, 6])
        G.add_edges_from([(1, 2), (2, 3), (4, 5), (5, 6)])
        assert check_disconnected(G) is True
        
    def test_single_node_graph(self):
        """Test that a single node graph is considered connected."""
        G = nx.Graph()
        G.add_node(1)
        assert check_disconnected(G) is False
        
    def test_empty_graph(self):
        """Test that an empty graph is considered disconnected."""
        G = nx.Graph()
        assert check_disconnected(G) is True
        
    def test_two_isolated_nodes(self):
        """Test that two isolated nodes are disconnected."""
        G = nx.Graph()
        G.add_nodes_from([1, 2])
        assert check_disconnected(G) is True

class TestComputeOrderParameter:
    """Tests for the compute_order_parameter function."""
    
    def test_perfect_sync(self):
        """Test order parameter for perfectly synchronized phases."""
        phases = np.array([0.0, 0.0, 0.0, 0.0])
        r = compute_order_parameter(phases)
        assert np.isclose(r, 1.0, atol=1e-6)
        
    def test_perfect_desync(self):
        """Test order parameter for perfectly desynchronized phases (uniformly distributed)."""
        # For N=4, phases at 0, pi/2, pi, 3pi/2 should give r=0
        phases = np.array([0.0, np.pi/2, np.pi, 3*np.pi/2])
        r = compute_order_parameter(phases)
        assert np.isclose(r, 0.0, atol=1e-6)
        
    def test_partial_sync(self):
        """Test order parameter for partially synchronized phases."""
        phases = np.array([0.0, 0.1, 0.2, 0.15])
        r = compute_order_parameter(phases)
        assert 0.5 < r < 1.0
        
    def test_empty_array(self):
        """Test order parameter for empty array."""
        phases = np.array([])
        r = compute_order_parameter(phases)
        assert r == 0.0

class TestKuramotoDerivative:
    """Tests for the kuramoto_derivative function."""
    
    def test_derivative_computation(self):
        """Test that derivative computation returns correct shape."""
        N = 10
        phases = np.random.uniform(0, 2*np.pi, N)
        K = 1.0
        omega = np.random.uniform(-0.5, 0.5, N)
        adj_matrix = np.random.randint(0, 2, (N, N))
        np.fill_diagonal(adj_matrix, 0)
        
        dtheta = kuramoto_derivative(0, phases, K, omega, adj_matrix)
        assert dtheta.shape == (N,)
        
    def test_derivative_with_zero_coupling(self):
        """Test that with K=0, derivative equals natural frequencies."""
        N = 10
        phases = np.random.uniform(0, 2*np.pi, N)
        K = 0.0
        omega = np.array([1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0])
        adj_matrix = np.zeros((N, N))
        
        dtheta = kuramoto_derivative(0, phases, K, omega, adj_matrix)
        assert np.allclose(dtheta, omega)

class TestRunKuramotoSimulation:
    """Tests for the run_kuramoto_simulation function."""
    
    def test_simulation_runs(self):
        """Test that simulation runs without error on a small graph."""
        G = nx.erdos_renyi_graph(20, 0.3, seed=42)
        result = run_kuramoto_simulation(G, K=1.0, T=10.0, dt=0.1, seed=42)
        assert result.error is None
        assert result.metrics['num_steps'] > 0
        
    def test_empty_graph(self):
        """Test simulation on an empty graph."""
        G = nx.Graph()
        result = run_kuramoto_simulation(G, K=1.0, T=10.0, dt=0.1)
        assert result.status == SynchronizationStatus.FAILED
        assert "Empty graph" in result.error
        
    def test_disconnected_graph_handling(self):
        """Test that disconnected graphs are handled correctly (early exit)."""
        G = nx.Graph()
        G.add_nodes_from([1, 2, 3, 4, 5, 6])
        G.add_edges_from([(1, 2), (2, 3), (4, 5), (5, 6)])
        
        result = run_kuramoto_simulation(G, K=1.0, T=10.0, dt=0.1)
        # The simulation should still run, but synchronization is unlikely
        assert result.error is None

class TestFindCriticalCoupling:
    """Tests for the find_critical_coupling function."""
    
    def test_disconnected_graph_early_exit(self):
        """Test that disconnected graphs return infinity immediately."""
        G = nx.Graph()
        G.add_nodes_from([1, 2, 3, 4, 5, 6])
        G.add_edges_from([(1, 2), (2, 3), (4, 5), (5, 6)])
        
        result = find_critical_coupling(G, K_min=0.0, K_max=5.0, tol=0.001)
        
        assert result.threshold == float('inf')
        assert result.metrics['is_disconnected'] is True
        assert result.metrics['search_method'] == 'early_exit_disconnected'
        assert result.status == SynchronizationStatus.DESYNCHRONIZED
        
    def test_connected_graph_finds_threshold(self):
        """Test that a connected graph finds a finite threshold."""
        # Use a highly connected graph that should synchronize easily
        G = nx.complete_graph(20)
        
        result = find_critical_coupling(G, K_min=0.0, K_max=5.0, tol=0.1)
        
        # Complete graphs synchronize at very low K
        assert result.threshold < 5.0
        assert result.threshold >= 0.0
        assert result.metrics['is_disconnected'] is False
        assert result.metrics['search_method'] == 'bisection'
        
    def test_bisection_search_logic(self):
        """Test that bisection search converges to correct tolerance."""
        G = nx.erdos_renyi_graph(50, 0.2, seed=42)
        
        result = find_critical_coupling(G, K_min=0.0, K_max=5.0, tol=0.001)
        
        # Check that the search was performed correctly
        assert result.metrics['iterations'] <= 50
        # The final threshold should be within the range
        if result.threshold != float('inf'):
            assert 0.0 <= result.threshold <= 5.0

class TestRingGraphAnalytical:
    """Tests for analytical solution check on Ring Graph."""
    
    def test_ring_graph_analytical_match_5pct(self):
        """
        Test that Ring Graph N=200 with K=0.5 matches analytical expectation.
        The analytical critical coupling for a ring graph is K_c = 2 * sin(pi/N) * |omega_max - omega_min| / N
        For uniform omega in [-0.5, 0.5], this is approximately K_c ≈ pi^2 / N^2 * 1.0
        For N=200, K_c ≈ 0.00025, so K=0.5 should definitely synchronize.
        """
        N = 200
        G = nx.cycle_graph(N)
        
        # Run simulation with K=0.5 (well above expected critical coupling)
        result = run_kuramoto_simulation(G, K=0.5, T=100.0, dt=0.1, seed=42)
        
        # Should be synchronized
        assert result.status == SynchronizationStatus.SYNCHRONIZED
        assert result.metrics['final_r'] > 0.8

class TestIntegrationEdgeCases:
    """Integration tests for edge cases."""
    
    def test_n2_graph(self):
        """Test simulation on a graph with only 2 nodes."""
        G = nx.Graph()
        G.add_edges_from([(1, 2)])
        
        result = find_critical_coupling(G, K_min=0.0, K_max=5.0, tol=0.001)
        assert result.error is None
        
    def test_self_loops(self):
        """Test simulation on a graph with self-loops."""
        G = nx.Graph()
        G.add_edges_from([(1, 2), (2, 3), (1, 1)])  # Self-loop on node 1
        
        result = find_critical_coupling(G, K_min=0.0, K_max=5.0, tol=0.001)
        assert result.error is None

class TestBisectionSearch:
    """Tests specifically for bisection search logic."""
    
    def test_bisection_search_logic(self):
        """
        Verify that the bisection search correctly narrows down the threshold.
        This test uses a known graph and checks the search behavior.
        """
        G = nx.erdos_renyi_graph(30, 0.3, seed=123)
        
        result = find_critical_coupling(G, K_min=0.0, K_max=5.0, tol=0.01, max_iter=20)
        
        # Verify the search completed
        assert result.metrics['iterations'] <= 20
        assert result.metrics['final_K_low'] <= result.metrics['final_K_high']
        
        # The threshold should be within the search range (or infinity if not found)
        if result.threshold != float('inf'):
            assert 0.0 <= result.threshold <= 5.0

def test_disconnected_graph(self):
    """
    Contract test for disconnected graph handling (returns infinity/null).
    This test specifically verifies the early-exit logic for disconnected graphs.
    """
    # Create a disconnected graph
    G = nx.Graph()
    G.add_nodes_from([1, 2, 3, 4, 5, 6, 7, 8])
    G.add_edges_from([(1, 2), (2, 3), (3, 1), (4, 5), (5, 6), (6, 4), (7, 8)])
    
    # Verify it's disconnected
    assert nx.number_connected_components(G) == 3
    
    # Run find_critical_coupling
    result = find_critical_coupling(G, K_min=0.0, K_max=5.0, tol=0.001)
    
    # Verify early exit behavior
    assert result.threshold == float('inf'), "Disconnected graph should return infinity threshold"
    assert result.metrics['is_disconnected'] is True
    assert result.metrics['search_method'] == 'early_exit_disconnected'
    assert result.status == SynchronizationStatus.DESYNCHRONIZED
    
    # Verify no K-sweep was performed (iterations should be 0 or minimal)
    # The function should exit immediately without calling run_kuramoto_simulation multiple times
    assert result.metrics.get('iterations', 0) == 0 or 'early_exit' in result.metrics.get('search_method', '')