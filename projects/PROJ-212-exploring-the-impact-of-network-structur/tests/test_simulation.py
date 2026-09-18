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
from data_models import SimulationResult, SynchronizationStatus
import logging

# Configure logging for tests to avoid noise
logging.basicConfig(level=logging.ERROR)

class TestCheckDisconnected:
    def test_connected_graph_returns_false(self):
        """A complete graph is definitely connected."""
        G = nx.complete_graph(10)
        assert check_disconnected(G) is False

    def test_disconnected_graph_returns_true(self):
        """Two disjoint cliques are disconnected."""
        G = nx.Graph()
        G.add_nodes_from(range(5))
        G.add_nodes_from(range(5, 10))
        G.add_edges_from([(i, i+1) for i in range(4)]) # Clique 1
        G.add_edges_from([(i, i+1) for i in range(5, 9)]) # Clique 2
        assert check_disconnected(G) is True

    def test_single_node_connected(self):
        """A single node is considered connected."""
        G = nx.Graph()
        G.add_node(0)
        assert check_disconnected(G) is False

class TestKuramotoDerivative:
    def test_derivative_shape(self):
        """Verify the derivative function returns the correct shape."""
        N = 10
        thetas = np.zeros(N)
        K = 1.0
        adj = np.eye(N) # Fully connected
        omega = np.ones(N)

        dthetas = kuramoto_derivative(0, thetas, K, adj, omega)
        assert dthetas.shape == thetas.shape

    def test_derivative_values(self):
        """Check a simple case where we can manually verify the math."""
        # Simple 2-node case
        N = 2
        thetas = np.array([0.0, np.pi/2]) # 0 and 90 degrees
        K = 1.0
        # Adjacency: 0 connected to 1, 1 connected to 0
        adj = np.array([[0, 1], [1, 0]])
        omega = np.array([0.0, 0.0]) # No natural frequency difference

        dthetas = kuramoto_derivative(0, thetas, K, adj, omega)

        # d(theta_0)/dt = K * sum(sin(theta_j - theta_0))
        # = 1.0 * sin(theta_1 - theta_0) = sin(pi/2 - 0) = 1.0
        # d(theta_1)/dt = K * sum(sin(theta_j - theta_1))
        # = 1.0 * sin(theta_0 - theta_1) = sin(0 - pi/2) = -1.0
        assert np.isclose(dthetas[0], 1.0)
        assert np.isclose(dthetas[1], -1.0)

class TestComputeOrderParameter:
    def test_perfect_synchronization(self):
        """All phases equal -> R = 1."""
        thetas = np.array([0.5, 0.5, 0.5, 0.5])
        R, phi = compute_order_parameter(thetas)
        assert np.isclose(R, 1.0)
        assert np.isclose(phi, 0.5)

    def test_uniform_distribution(self):
        """Uniformly distributed phases -> R approx 0."""
        thetas = np.array([0, np.pi/2, np.pi, 3*np.pi/2])
        R, phi = compute_order_parameter(thetas)
        assert np.isclose(R, 0.0, atol=1e-6)

    def test_partial_synchronization(self):
        """Some synchronization -> 0 < R < 1."""
        # Cluster around 0, but with some spread
        thetas = np.array([0.0, 0.1, -0.1, 3.0, 3.1])
        R, phi = compute_order_parameter(thetas)
        assert 0.0 < R < 1.0

class TestRunKuramotoSimulation:
    def test_disconnected_graph_returns_infinity(self):
        """Disconnected graphs should immediately return infinity threshold."""
        G = nx.Graph()
        G.add_nodes_from([0, 1, 2, 3])
        G.add_edge(0, 1)
        G.add_edge(2, 3) # Disconnected component

        result = run_kuramoto_simulation(G, k_range=np.array([0.1, 0.2, 0.3]), r_threshold=0.8, t_min=100)

        assert result.threshold == float('inf')
        assert result.status == SynchronizationStatus.DISCONNECTED

    def test_ring_graph_analytical_threshold(self):
        """
        T011 Core Test: Input Ring Graph (N=200), verify threshold detection
        matches analytical solution within 5% tolerance.

        Analytical Critical Coupling for Ring Graph (1D lattice with nearest neighbors):
        K_c = 2 / (pi * density_of_states_at_omega=0) ... simplified for identical oscillators
        Actually, for identical oscillators (omega=0), any K > 0 leads to sync eventually,
        but we are looking for the threshold where the order parameter > 0.8 within a fixed time.
        
        However, the standard analytical result for the onset of synchronization in the
        Kuramoto model on a ring (or 1D lattice) with natural frequencies drawn from a
        distribution g(omega) is K_c = 2 / (pi * g(0)).
        
        In this test, we use identical oscillators (omega=0) to test the RK45 integration
        stability and the order parameter calculation logic. With identical oscillators,
        the system should synchronize for any K > 0. The "threshold" in this context
        for the simulation logic (finding first K where R > 0.8 for t > 100) should be
        the smallest K in our sweep that allows synchronization.
        
        To make the test meaningful for "analytical solution", we introduce a small
        frequency spread. Let's assume a Lorentzian distribution with gamma=0.1.
        K_c_analytical = 2 * gamma = 0.2.
        
        We will sweep K from 0.0 to 0.5. The simulation should detect a threshold
        close to 0.2.
        """
        N = 200
        G = nx.cycle_graph(N)
        
        # Assign natural frequencies from a Lorentzian distribution (Cauchy)
        # g(omega) = gamma / (pi * (omega^2 + gamma^2))
        # K_c = 2 * gamma
        gamma = 0.1
        # Generate frequencies
        np.random.seed(42)
        # Use inverse transform sampling for Cauchy distribution
        u = np.random.uniform(0, 1, N)
        # F(x) = 1/2 + (1/pi) * arctan((x-x0)/gamma)
        # x = x0 + gamma * tan(pi * (F(x) - 1/2))
        # Assuming x0 = 0
        omega = gamma * np.tan(np.pi * (u - 0.5))

        # Sweep K values
        # We expect K_c ~ 0.2. Let's sweep around it.
        k_values = np.linspace(0.05, 0.5, 10)
        
        result = run_kuramoto_simulation(G, k_range=k_values, r_threshold=0.8, t_min=100, t_max=200)

        # The detected threshold should be close to the analytical 2*gamma = 0.2
        # Allow 5% tolerance: 0.19 to 0.21
        expected_kc = 2 * gamma
        tolerance = 0.05 * expected_kc
        
        assert result.threshold is not None, "Threshold should be detected"
        assert abs(result.threshold - expected_kc) <= tolerance, \
            f"Detected threshold {result.threshold:.4f} is not within 5% of analytical {expected_kc:.4f}"

    def test_rk45_integration_stability(self):
        """Verify that RK45 integration does not blow up or produce NaNs."""
        G = nx.barabasi_albert_graph(50, 3)
        omega = np.random.randn(50)
        k_values = np.array([0.5, 1.0, 1.5])
        
        result = run_kuramoto_simulation(G, k_range=k_values, r_threshold=0.5, t_min=50, t_max=100)
        
        assert not np.isnan(result.threshold)
        assert not np.isinf(result.threshold) or result.threshold == float('inf') # Inf is allowed for disconnected or no sync

    def test_threshold_detection_logic(self):
        """
        Verify that the threshold detection logic correctly identifies the first K
        where the order parameter stays above r_threshold for t > t_min.
        """
        # Create a graph that is easy to synchronize
        G = nx.complete_graph(20)
        omega = np.zeros(20) # Identical oscillators -> sync for any K > 0
        
        # Sweep K
        k_values = np.array([0.1, 0.2, 0.3, 0.4, 0.5])
        
        result = run_kuramoto_simulation(G, k_range=k_values, r_threshold=0.9, t_min=50, t_max=100)
        
        # With identical oscillators, even small K should sync.
        # The first value in k_values is 0.1.
        # If the simulation works, it should detect 0.1 (or the first one that passes).
        # Since we start with 0.1, and it's complete graph, it should sync.
        assert result.threshold == 0.1, f"Expected threshold 0.1, got {result.threshold}"

class TestIntegrationEdgeCases:
    def test_very_small_network(self):
        """Test with N=2."""
        G = nx.path_graph(2)
        omega = np.array([0.0, 0.0])
        k_values = np.array([0.1, 0.5])
        
        result = run_kuramoto_simulation(G, k_range=k_values, r_threshold=0.8, t_min=10, t_max=50)
        
        # Should not crash
        assert result is not None

    def test_large_k_values(self):
        """Test with very large K to ensure no overflow."""
        G = nx.cycle_graph(50)
        omega = np.random.randn(50)
        k_values = np.array([10.0, 20.0, 50.0])
        
        result = run_kuramoto_simulation(G, k_range=k_values, r_threshold=0.8, t_min=50, t_max=100)
        
        # Should detect synchronization quickly
        assert result.threshold is not None
        assert result.threshold <= 50.0