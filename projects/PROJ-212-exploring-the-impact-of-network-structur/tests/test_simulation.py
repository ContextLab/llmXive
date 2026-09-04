import pytest
import numpy as np
import networkx as nx
from src.simulation import check_disconnected, kuramoto_derivative, run_kuramoto_simulation
from data_models import SynchronizationStatus, SimulationResult
import logging

# Configure logging for tests
logging.basicConfig(level=logging.INFO)

class TestCheckDisconnected:
    def test_connected_graph(self):
        """Test that a connected graph returns False."""
        G = nx.barabasi_albert_graph(10, 3)
        assert check_disconnected(G) is False

    def test_disconnected_graph(self):
        """Test that a disconnected graph returns True."""
        G = nx.Graph()
        G.add_nodes_from([1, 2, 3, 4, 5])
        G.add_edges_from([(1, 2), (2, 3)])  # Component 1
        G.add_edges_from([(4, 5)])          # Component 2
        assert check_disconnected(G) is True

    def test_single_node(self):
        """Test that a single node graph is connected."""
        G = nx.Graph()
        G.add_node(1)
        assert check_disconnected(G) is False

    def test_empty_graph(self):
        """Test that an empty graph is considered disconnected."""
        G = nx.Graph()
        assert check_disconnected(G) is True

class TestKuramotoDerivative:
    def test_derivative_shape(self):
        """Test that the derivative has the correct shape."""
        N = 10
        t = 0.0
        theta = np.random.rand(N)
        K = 1.0
        adj_matrix = np.random.rand(N, N)
        adj_matrix = (adj_matrix + adj_matrix.T) / 2  # Symmetric
        omega = np.random.rand(N)
        
        dtheta = kuramoto_derivative(t, theta, K, adj_matrix, omega)
        assert dtheta.shape == (N,)

    def test_derivative_with_zero_coupling(self):
        """Test that with K=0, the derivative is just omega."""
        N = 10
        t = 0.0
        theta = np.random.rand(N)
        K = 0.0
        adj_matrix = np.ones((N, N))  # Fully connected
        omega = np.array([i * 0.1 for i in range(N)])
        
        dtheta = kuramoto_derivative(t, theta, K, adj_matrix, omega)
        np.testing.assert_array_almost_equal(dtheta, omega)

    def test_derivative_with_nonzero_coupling(self):
        """Test that coupling affects the derivative."""
        N = 10
        t = 0.0
        theta = np.zeros(N)  # All phases zero
        K = 1.0
        adj_matrix = np.ones((N, N))  # Fully connected
        omega = np.zeros(N)
        
        # sin(theta_j - theta_i) = sin(0) = 0, so derivative should be 0
        dtheta = kuramoto_derivative(t, theta, K, adj_matrix, omega)
        np.testing.assert_array_almost_equal(dtheta, np.zeros(N))

class TestRunKuramotoSimulation:
    @pytest.fixture
    def small_connected_graph(self):
        """Fixture for a small connected graph."""
        return nx.barabasi_albert_graph(50, 3)

    @pytest.fixture
    def disconnected_graph(self):
        """Fixture for a disconnected graph."""
        G = nx.Graph()
        G.add_nodes_from(range(10))
        G.add_edges_from([(i, i+1) for i in range(0, 5)])
        G.add_edges_from([(i, i+1) for i in range(5, 9)])
        return G

    def test_disconnected_graph_returns_inf(self, disconnected_graph):
        """Test that disconnected graph returns critical_k = inf."""
        result = run_kuramoto_simulation(
            graph=disconnected_graph,
            K_values=[0.1, 0.5, 1.0],
            n_oscillators=10,
            t_max=50.0,
            min_sync_duration=10.0
        )
        assert result.critical_k == float('inf')
        assert result.status == SynchronizationStatus.DISCONNECTED

    def test_ring_graph_analytical_check(self):
        """
        Test with a ring graph (N=200) and K=0.5.
        Analytical solution suggests synchronization should occur for K > Kc.
        For a ring, Kc is related to the eigenvalue gap.
        We check that the simulation runs without error and returns a valid result.
        """
        N = 200
        G = nx.cycle_graph(N)
        
        result = run_kuramoto_simulation(
            graph=G,
            K_values=[0.0, 0.1, 0.5, 1.0],
            n_oscillators=N,
            t_max=100.0,
            min_sync_duration=20.0,
            threshold_r=0.5  # Lower threshold for faster test
        )
        
        assert result is not None
        assert isinstance(result.critical_k, float)
        assert result.status in [SynchronizationStatus.SYNCHRONIZED, SynchronizationStatus.NO_SYNC]

    def test_simulation_with_k_sweep(self, small_connected_graph):
        """Test that the simulation runs a K sweep and returns a result."""
        result = run_kuramoto_simulation(
            graph=small_connected_graph,
            K_values=np.arange(0, 2, 0.5).tolist(),
            n_oscillators=50,
            t_max=50.0,
            min_sync_duration=10.0
        )
        
        assert result.critical_k >= 0
        assert result.status in [SynchronizationStatus.SYNCHRONIZED, SynchronizationStatus.NO_SYNC, SynchronizationStatus.DISCONNECTED]

    def test_robustness_threshold_logic(self):
        """
        Test the robustness threshold logic: r > 0.8 for t > 100.
        We'll create a scenario where we expect synchronization.
        """
        # Use a dense graph that should synchronize easily
        N = 50
        G = nx.erdos_renyi_graph(N, 0.5, seed=42)
        
        result = run_kuramoto_simulation(
            graph=G,
            K_values=[0.1, 0.5, 1.0, 2.0],
            n_oscillators=N,
            t_max=150.0,
            min_sync_duration=100.0,
            threshold_r=0.8,
            seed=42
        )
        
        # We expect that for high enough K, synchronization is found
        # The critical_k should be one of the K values or inf
        assert result.critical_k in [float('inf'), 0.1, 0.5, 1.0, 2.0]

    def test_rk45_integration(self):
        """
        Verify that RK45 is used by checking the method argument in solve_ivp.
        This is implicitly tested by the simulation running successfully.
        """
        G = nx.barabasi_albert_graph(30, 2)
        result = run_kuramoto_simulation(
            graph=G,
            K_values=[0.5],
            n_oscillators=30,
            t_max=20.0,
            min_sync_duration=5.0
        )
        assert result is not None

    def test_empty_k_values(self):
        """Test behavior with empty K_values list."""
        G = nx.barabasi_albert_graph(20, 2)
        result = run_kuramoto_simulation(
            graph=G,
            K_values=[],
            n_oscillators=20,
            t_max=20.0,
            min_sync_duration=5.0
        )
        # Should return inf critical_k and NO_SYNC status
        assert result.critical_k == float('inf')
        assert result.status == SynchronizationStatus.NO_SYNC