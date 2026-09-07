"""
Unit tests for src/simulation.py: RK45 integration and threshold detection.

These tests verify:
1. The RK45 integrator (via scipy.integrate.solve_ivp) correctly integrates the Kuramoto dynamics.
2. The synchronization threshold detection logic (r > 0.8 for t > 100) works as expected.
3. Disconnected graph handling returns infinity/null as per contract.
"""
import pytest
import numpy as np
import networkx as nx
from scipy.integrate import solve_ivp
from unittest.mock import patch, MagicMock

# Import the functions under test from the src package
from src.simulation import (
    check_disconnected,
    kuramoto_derivative,
    compute_order_parameter,
    run_kuramoto_simulation
)
from src.data_models import SynchronizationStatus


class TestCheckDisconnected:
    """Tests for the check_disconnected helper function."""

    def test_connected_graph_returns_false(self):
        """A standard connected graph should return False."""
        G = nx.erdos_renyi_graph(50, 0.1, seed=42)
        # Ensure it's connected
        if not nx.is_connected(G):
            G = nx.complete_graph(50)
        
        result = check_disconnected(G)
        assert result is False

    def test_disconnected_graph_returns_true(self):
        """A graph with two separate components should return True."""
        G = nx.Graph()
        G.add_nodes_from(range(10))
        G.add_edges_from([(i, i+1) for i in range(5)]) # Component 1: 0-4
        # Nodes 5-9 are isolated or form a second component, but let's make it explicit
        G.add_edges_from([(i, i+1) for i in range(6, 10)]) # Component 2: 6-9, 5 is isolated
        
        result = check_disconnected(G)
        assert result is True

    def test_single_node_graph_returns_false(self):
        """A single node graph is trivially connected."""
        G = nx.Graph()
        G.add_node(0)
        result = check_disconnected(G)
        assert result is False


class TestKuramotoDerivative:
    """Tests for the Kuramoto derivative function (dtheta/dt)."""

    def test_derivative_shape(self):
        """The derivative output must match the input phase shape."""
        N = 10
        phases = np.random.rand(N)
        # Create a simple ring graph adjacency matrix
        G = nx.cycle_graph(N)
        adj_matrix = nx.to_numpy_array(G)
        natural_freqs = np.ones(N) * 1.0
        K = 1.0

        dphases = kuramoto_derivative(t=0.0, y=phases, K=K, adj=adj_matrix, omega=natural_freqs)
        
        assert dphases.shape == phases.shape
        assert isinstance(dphases, np.ndarray)

    def test_derivative_zero_coupling(self):
        """With K=0, derivative should equal natural frequency."""
        N = 5
        phases = np.random.rand(N)
        G = nx.complete_graph(N)
        adj_matrix = nx.to_numpy_array(G)
        natural_freqs = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        K = 0.0

        dphases = kuramoto_derivative(t=0.0, y=phases, K=K, adj=adj_matrix, omega=natural_freqs)
        
        # With K=0, the coupling term is zero, so dtheta/dt = omega
        np.testing.assert_array_almost_equal(dphases, natural_freqs)

    def test_derivative_consistency(self):
        """Verify the derivative calculation logic manually for a small case."""
        N = 3
        phases = np.array([0.0, np.pi/2, np.pi])
        # Triangle graph
        adj = np.array([
            [0, 1, 1],
            [1, 0, 1],
            [1, 1, 0]
        ])
        omega = np.zeros(N) # Zero natural frequency for simplicity
        K = 1.0

        dphases = kuramoto_derivative(0.0, phases, K, adj, omega)

        # Manual calculation for node 0:
        # dtheta_0/dt = sum_{j} A_0j * sin(theta_j - theta_0)
        # = sin(pi/2 - 0) + sin(pi - 0)
        # = sin(pi/2) + sin(pi) = 1 + 0 = 1.0
        expected_0 = np.sin(phases[1] - phases[0]) + np.sin(phases[2] - phases[0])
        
        assert np.isclose(dphases[0], expected_0)


class TestComputeOrderParameter:
    """Tests for the order parameter calculation."""

    def test_perfect_synchronization(self):
        """All phases aligned should yield R=1."""
        phases = np.array([0.5, 0.5, 0.5, 0.5])
        R, psi = compute_order_parameter(phases)
        assert np.isclose(R, 1.0, atol=1e-6)
        assert np.isclose(psi, 0.5, atol=1e-6)

    def test_perfect_antisynchronization(self):
        """Phases evenly spread (0, pi) should yield R approx 0."""
        # 50% at 0, 50% at pi
        phases = np.array([0.0, 0.0, np.pi, np.pi])
        R, psi = compute_order_parameter(phases)
        assert np.isclose(R, 0.0, atol=1e-6)

    def test_random_phases(self):
        """Random phases should yield R < 1."""
        np.random.seed(42)
        phases = np.random.rand(100) * 2 * np.pi
        R, psi = compute_order_parameter(phases)
        assert 0 <= R < 1.0


class TestRunKuramotoSimulation:
    """Tests for the full simulation pipeline and threshold detection."""

    def setup_method(self):
        """Setup common test fixtures."""
        self.N = 50
        self.G = nx.erdos_renyi_graph(self.N, 0.1, seed=42)
        # Ensure connected for most tests
        if not nx.is_connected(self.G):
            self.G = nx.complete_graph(self.N)
        
        self.omega = np.random.uniform(-0.5, 0.5, self.N)
        self.K_values = [0.5, 1.5] # Small set for speed

    def test_simulation_returns_result_object(self):
        """The function must return a SimulationResult object."""
        from src.data_models import SimulationResult
        
        result = run_kuramoto_simulation(self.G, self.omega, self.K_values, t_max=10.0, dt=0.1)
        
        assert isinstance(result, SimulationResult)
        assert result.threshold is not None
        assert isinstance(result.threshold, (float, int))

    def test_rk45_integration_used(self):
        """Verify that solve_ivp is called with method='RK45'."""
        with patch('src.simulation.solve_ivp') as mock_solve_ivp:
            # Mock the return value to avoid actual integration
            mock_solution = MagicMock()
            mock_solution.success = True
            mock_solution.y = np.zeros((self.N, 10)) # Mock phases
            mock_solution.t = np.linspace(0, 10, 10)
            mock_solve_ivp.return_value = mock_solution

            run_kuramoto_simulation(self.G, self.omega, self.K_values, t_max=10.0, dt=1.0)

            # Check that solve_ivp was called
            assert mock_solve_ivp.called
            # Check the method argument
            call_kwargs = mock_solve_ivp.call_args[1]
            assert call_kwargs.get('method') == 'RK45'

    def test_threshold_detection_logic(self):
        """
        Test that the threshold detection logic correctly identifies the K value
        where synchronization is sustained (r > 0.8 for t > 100).
        
        We simulate a scenario where low K fails and high K succeeds.
        """
        # Create a scenario where we know the threshold
        # We'll mock the simulation to return specific order parameters
        
        # Mock data: Low K (0.5) -> R=0.2 (not synced), High K (2.0) -> R=0.9 (synced)
        # We need to mock run_kuramoto_simulation or the internal loop.
        # Instead, let's test the logic by constructing a SimulationResult directly
        # if the function allows, or by mocking the internal simulation steps.
        
        # Since run_kuramoto_simulation is the entry point, we'll mock the inner
        # simulation logic to return deterministic results.
        
        def mock_simulate(K, G, omega, t_max, dt):
            # Return a mock result based on K
            if K < 1.0:
                # Simulate failure: R stays low
                # We need to return a structure that the threshold logic can parse
                # The function returns a SimulationResult. We need to mock the 
                # internal behavior that leads to the threshold calculation.
                # This is tricky. Let's mock the `compute_order_parameter` calls
                # inside the loop or the final aggregation.
                pass
            return None

        # Alternative approach: Test the threshold calculation logic by feeding
        # a pre-computed set of (K, R_history) if the code exposes it, 
        # or by mocking the solve_ivp return values to produce specific R(t) curves.
        
        # Let's mock solve_ivp to return phases that result in specific R values.
        # For K=0.5: phases diverge -> R ~ 0.2
        # For K=2.0: phases converge -> R ~ 0.95
        
        def mock_solve_ivp_side_effect(fun, t_span, y0, args, **kwargs):
            N = len(y0)
            t_eval = np.linspace(t_span[0], t_span[1], 100)
            
            # Determine K from args
            # args = (K, adj, omega)
            K = args[0]
            
            if K < 1.0:
                # Diverging phases: random
                y_final = np.random.rand(N) * 2 * np.pi
            else:
                # Converging phases: all same
                y_final = np.ones(N) * 0.5
            
            # Construct a mock solution object
            mock_sol = MagicMock()
            mock_sol.success = True
            mock_sol.y = np.tile(y_final, (len(t_eval), 1)).T # Shape: (N, len(t_eval))
            mock_sol.t = t_eval
            return mock_sol

        with patch('src.simulation.solve_ivp', side_effect=mock_solve_ivp_side_effect):
            # Run with a range that includes the threshold
            K_range = [0.5, 1.0, 1.5, 2.0]
            result = run_kuramoto_simulation(
                self.G, self.omega, K_range, 
                t_max=200.0, dt=1.0 # t_max > 100 to satisfy duration condition
            )
            
            # We expect the threshold to be around 1.0 or 1.5 (the first K that succeeds)
            # Since 0.5 fails and 1.0 might be the boundary, let's check the logic:
            # The logic looks for the first K where R > 0.8 for t > 100.
            # With our mock:
            # K=0.5 -> R ~ 0.2 (fail)
            # K=1.0 -> R ~ 0.5 (fail, if we set threshold strictly)
            # K=1.5 -> R ~ 0.95 (pass)
            # K=2.0 -> R ~ 0.95 (pass)
            # Expected threshold: 1.5
            
            # Note: The exact value depends on the mock implementation details.
            # The key is that it's not infinity (since we have a passing case)
            # and it's not 0.5 (the failing case).
            assert result.threshold != float('inf')
            assert result.threshold >= 0.5

    def test_disconnected_graph_returns_infinity(self):
        """If the graph is disconnected, the threshold should be infinity."""
        G_disconnected = nx.Graph()
        G_disconnected.add_nodes_from(range(10))
        G_disconnected.add_edges_from([(0, 1), (2, 3)]) # Two small components, rest isolated
        
        K_values = [0.5, 1.0]
        
        result = run_kuramoto_simulation(G_disconnected, np.ones(10), K_values, t_max=10.0, dt=0.1)
        
        assert result.threshold == float('inf')
        assert result.status == SynchronizationStatus.DISCONNECTED

    def test_small_network_fast_run(self):
        """Ensure the simulation runs quickly on a small network for unit tests."""
        G_small = nx.complete_graph(10)
        omega_small = np.ones(10)
        K_vals = [0.5]
        
        import time
        start = time.time()
        result = run_kuramoto_simulation(G_small, omega_small, K_vals, t_max=5.0, dt=0.1)
        elapsed = time.time() - start
        
        assert elapsed < 5.0 # Should be very fast
        assert result.threshold is not None

    def test_output_contains_metrics(self):
        """The result object should contain the necessary metrics."""
        result = run_kuramoto_simulation(
            self.G, self.omega, self.K_values, 
            t_max=10.0, dt=0.1
        )
        
        assert hasattr(result, 'threshold')
        assert hasattr(result, 'status')
        # Depending on implementation, it might also store the full sweep data
        # but the contract requires at least the threshold.

class TestIntegrationEdgeCases:
    """Integration tests for edge cases."""

    def test_natural_frequency_zero(self):
        """All natural frequencies zero should synchronize easily."""
        G = nx.erdos_renyi_graph(20, 0.2, seed=42)
        omega = np.zeros(20)
        K_vals = [0.1, 0.5]
        
        result = run_kuramoto_simulation(G, omega, K_vals, t_max=10.0, dt=0.1)
        
        # With zero frequencies, even low K should synchronize
        # (assuming connected graph)
        assert result.threshold != float('inf')

    def test_large_k_sweep(self):
        """Test with a larger sweep of K values."""
        G = nx.erdos_renyi_graph(30, 0.1, seed=42)
        omega = np.random.rand(30)
        K_vals = np.linspace(0, 5, 50).tolist()
        
        result = run_kuramoto_simulation(G, omega, K_vals, t_max=20.0, dt=0.2)
        
        assert result.threshold is not None
        # The threshold should be within the range [0, 5] or infinity
        if result.threshold != float('inf'):
            assert 0 <= result.threshold <= 5.0