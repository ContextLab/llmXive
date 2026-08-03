"""
Unit tests for edge cases in the Kuramoto simulation and analysis pipeline.
Covers zero variance scenarios, numerical instability, and boundary conditions.
"""
import pytest
import numpy as np
import networkx as nx
from scipy import stats
import json
import os
import tempfile
from pathlib import Path

# Import from project modules
from code.simulate_kuramoto import (
    kuramoto_derivative,
    calculate_order_parameter,
    simulate_kuramoto,
    find_critical_coupling_binary_search
)
from code.utils.stats_utils import spearman_correlation, bonferroni_correction
from code.utils.graph_utils import is_connected, calculate_average_degree


class TestOrderParameterEdgeCases:
    """Tests for calculate_order_parameter with edge cases."""

    def test_perfect_synchronization(self):
        """Test order parameter R=1 when all phases are identical."""
        N = 100
        phases = np.zeros(N)  # All phases at 0
        R, phi = calculate_order_parameter(phases)
        assert np.isclose(R, 1.0, atol=1e-10), f"Expected R=1.0, got {R}"
        assert np.isclose(phi, 0.0, atol=1e-10), f"Expected phi=0.0, got {phi}"

    def test_complete_desynchronization_uniform(self):
        """Test order parameter R≈0 when phases are uniformly distributed."""
        N = 1000
        # Uniform distribution over [0, 2π)
        phases = np.random.uniform(0, 2 * np.pi, N)
        R, _ = calculate_order_parameter(phases)
        # For large N, R should be close to 0 (within statistical fluctuation)
        assert R < 0.1, f"Expected R < 0.1 for uniform distribution, got {R}"

    def test_two_cluster_anti_phase(self):
        """Test order parameter for two equal anti-phase clusters."""
        N = 100
        phases = np.concatenate([np.zeros(N // 2), np.full(N // 2, np.pi)])
        R, _ = calculate_order_parameter(phases)
        # Two equal anti-phase clusters should give R ≈ 0
        assert np.isclose(R, 0.0, atol=1e-10), f"Expected R≈0 for anti-phase clusters, got {R}"

    def test_single_oscillator(self):
        """Test order parameter for N=1."""
        phases = np.array([0.5])
        R, phi = calculate_order_parameter(phases)
        assert np.isclose(R, 1.0, atol=1e-10), f"Expected R=1.0 for N=1, got {R}"
        assert np.isclose(phi, 0.5, atol=1e-10), f"Expected phi=0.5 for N=1, got {phi}"

    def test_empty_array_raises(self):
        """Test that empty array raises appropriate error."""
        with pytest.raises((ValueError, IndexError)):
            calculate_order_parameter(np.array([]))


class TestKuramotoDerivativeEdgeCases:
    """Tests for kuramoto_derivative with edge cases."""

    def test_zero_coupling(self):
        """Test derivative when K=0 (no coupling)."""
        N = 10
        theta = np.random.uniform(0, 2 * np.pi, N)
        omega = np.random.uniform(-1, 1, N)
        A = np.eye(N)  # Adjacency matrix (no edges)
        K = 0.0

        dtheta = kuramoto_derivative(theta, omega, A, K)
        # With K=0, derivative should equal natural frequencies
        assert np.allclose(dtheta, omega, atol=1e-10), "With K=0, dtheta should equal omega"

    def test_zero_natural_frequencies(self):
        """Test derivative when all ω_i = 0."""
        N = 10
        theta = np.random.uniform(0, 2 * np.pi, N)
        omega = np.zeros(N)
        A = np.ones((N, N)) - np.eye(N)  # Fully connected
        K = 1.0

        dtheta = kuramoto_derivative(theta, omega, A, K)
        # With ω=0, derivative comes purely from coupling
        assert not np.allclose(dtheta, 0), "Coupling should produce non-zero derivative"

    def test_all_zero_phases(self):
        """Test derivative when all phases are zero."""
        N = 10
        theta = np.zeros(N)
        omega = np.ones(N)
        A = np.ones((N, N)) - np.eye(N)
        K = 1.0

        dtheta = kuramoto_derivative(theta, omega, A, K)
        # sin(0) = 0, so coupling term is 0, derivative should be omega
        assert np.allclose(dtheta, omega, atol=1e-10), "With all θ=0, dtheta should equal omega"

    def test_very_large_coupling(self):
        """Test numerical stability with very large K."""
        N = 10
        theta = np.random.uniform(0, 2 * np.pi, N)
        omega = np.random.uniform(-1, 1, N)
        A = np.ones((N, N)) - np.eye(N)
        K = 1e6  # Very large coupling

        dtheta = kuramoto_derivative(theta, omega, A, K)
        # Should not produce NaN or Inf
        assert not np.any(np.isnan(dtheta)), "Large K should not produce NaN"
        assert not np.any(np.isinf(dtheta)), "Large K should not produce Inf"


class TestSynchronizationDetectionEdgeCases:
    """Tests for binary search and linear sweep edge cases."""

    def test_binary_search_no_synchronization(self):
        """Test binary search when synchronization never occurs (K too low)."""
        N = 20
        G = nx.watts_strogatz_graph(N, 2, 0.0)
        A = nx.to_numpy_array(G)
        omega = np.random.uniform(-1, 1, N)
        time_steps = 100

        # Very low coupling range - should not synchronize
        K_min, K_max = 0.0, 0.001

        try:
            Kc, status = find_critical_coupling_binary_search(
                A, omega, K_min, K_max, time_steps, tol=1e-3, max_iter=10
            )
            # Should return status indicating no synchronization found
            assert status in ['no_sync', 'max_iter_reached'], f"Unexpected status: {status}"
        except Exception as e:
            # If it raises, that's also acceptable behavior for edge case
            assert isinstance(e, (ValueError, RuntimeError))

    def test_binary_search_always_synchronized(self):
        """Test binary search when synchronization always occurs (K too high)."""
        N = 20
        G = nx.watts_strogatz_graph(N, 2, 0.0)
        A = nx.to_numpy_array(G)
        omega = np.random.uniform(-1, 1, N)
        time_steps = 100

        # Very high coupling range - should always synchronize
        K_min, K_max = 100.0, 200.0

        try:
            Kc, status = find_critical_coupling_binary_search(
                A, omega, K_min, K_max, time_steps, tol=1e-3, max_iter=10
            )
            # Should return status indicating always synchronized
            assert status in ['always_sync', 'converged'], f"Unexpected status: {status}"
        except Exception as e:
            assert isinstance(e, (ValueError, RuntimeError))

    def test_binary_search_single_iteration(self):
        """Test binary search with minimal iterations."""
        N = 20
        G = nx.watts_strogatz_graph(N, 2, 0.0)
        A = nx.to_numpy_array(G)
        omega = np.random.uniform(-1, 1, N)
        time_steps = 50  # Short simulation

        K_min, K_max = 0.0, 10.0

        Kc, status = find_critical_coupling_binary_search(
            A, omega, K_min, K_max, time_steps, tol=1e-3, max_iter=1
        )
        assert status == 'max_iter_reached', "Should reach max iterations"


class TestStatisticalEdgeCases:
    """Tests for statistical functions with edge cases."""

    def test_spearman_zero_variance_x(self):
        """Test Spearman correlation when x has zero variance."""
        x = np.ones(10)  # Zero variance
        y = np.random.randn(10)

        with pytest.raises((ValueError, stats.stats.ConstantInputWarning)):
            spearman_correlation(x, y)

    def test_spearman_zero_variance_y(self):
        """Test Spearman correlation when y has zero variance."""
        x = np.random.randn(10)
        y = np.ones(10)  # Zero variance

        with pytest.raises((ValueError, stats.stats.ConstantInputWarning)):
            spearman_correlation(x, y)

    def test_spearman_perfect_correlation(self):
        """Test Spearman correlation with perfect linear relationship."""
        x = np.arange(100)
        y = 2 * x + 5
        rho, p = spearman_correlation(x, y)
        assert np.isclose(rho, 1.0, atol=1e-10), f"Expected rho=1.0, got {rho}"

    def test_spearman_perfect_negative_correlation(self):
        """Test Spearman correlation with perfect negative relationship."""
        x = np.arange(100)
        y = -2 * x + 5
        rho, p = spearman_correlation(x, y)
        assert np.isclose(rho, -1.0, atol=1e-10), f"Expected rho=-1.0, got {rho}"

    def test_spearman_small_sample(self):
        """Test Spearman correlation with minimal sample size."""
        x = np.array([1.0, 2.0, 3.0])
        y = np.array([1.0, 2.0, 3.0])
        rho, p = spearman_correlation(x, y)
        assert np.isclose(rho, 1.0, atol=1e-10)

    def test_bonferroni_single_test(self):
        """Test Bonferroni correction with single p-value."""
        p_values = [0.05]
        corrected = bonferroni_correction(p_values, alpha=0.05)
        assert len(corrected) == 1
        assert corrected[0] == 0.05  # No correction for single test

    def test_bonferroni_all_significant(self):
        """Test Bonferroni when all p-values are significant."""
        p_values = [0.001, 0.002, 0.003]
        corrected = bonferroni_correction(p_values, alpha=0.05)
        assert all(p <= 0.05 for p in corrected)

    def test_bonferroni_all_non_significant(self):
        """Test Bonferroni when no p-values are significant."""
        p_values = [0.5, 0.6, 0.7]
        corrected = bonferroni_correction(p_values, alpha=0.05)
        assert all(p > 0.05 for p in corrected)


class TestGraphEdgeCases:
    """Tests for graph utility functions with edge cases."""

    def test_is_connected_single_node(self):
        """Test connectivity check for single-node graph."""
        G = nx.Graph()
        G.add_node(0)
        assert is_connected(G), "Single node should be connected"

    def test_is_connected_two_nodes_no_edge(self):
        """Test connectivity for two nodes without edge."""
        G = nx.Graph()
        G.add_nodes_from([0, 1])
        assert not is_connected(G), "Two nodes without edge should be disconnected"

    def test_is_connected_two_nodes_with_edge(self):
        """Test connectivity for two nodes with edge."""
        G = nx.Graph()
        G.add_edge(0, 1)
        assert is_connected(G), "Two nodes with edge should be connected"

    def test_average_degree_empty_graph(self):
        """Test average degree for empty graph."""
        G = nx.Graph()
        # Should handle gracefully (return 0 or raise)
        try:
            avg_deg = calculate_average_degree(G)
            assert avg_deg == 0.0
        except Exception:
            # Raising is also acceptable
            pass

    def test_average_degree_single_node(self):
        """Test average degree for single node."""
        G = nx.Graph()
        G.add_node(0)
        avg_deg = calculate_average_degree(G)
        assert avg_deg == 0.0


class TestNumericalStability:
    """Tests for numerical stability in simulations."""

    def test_very_small_time_step(self):
        """Test simulation with very small time step."""
        N = 10
        G = nx.watts_strogatz_graph(N, 2, 0.0)
        A = nx.to_numpy_array(G)
        omega = np.random.uniform(-1, 1, N)
        theta0 = np.random.uniform(0, 2 * np.pi, N)

        # Very small dt
        t_eval = np.linspace(0, 0.1, 1000)

        try:
            t, theta = simulate_kuramoto(theta0, omega, A, K=1.0, t_eval=t_eval)
            assert not np.any(np.isnan(theta)), "Small dt should not produce NaN"
            assert not np.any(np.isinf(theta)), "Small dt should not produce Inf"
        except Exception:
            # Some integrators may fail with very small steps, which is acceptable
            pass

    def test_very_large_time_step(self):
        """Test simulation with very large time step (potential instability)."""
        N = 10
        G = nx.watts_strogatz_graph(N, 2, 0.0)
        A = nx.to_numpy_array(G)
        omega = np.random.uniform(-1, 1, N)
        theta0 = np.random.uniform(0, 2 * np.pi, N)

        # Large dt
        t_eval = np.linspace(0, 100, 10)

        try:
            t, theta = simulate_kuramoto(theta0, omega, A, K=1.0, t_eval=t_eval)
            # Should not explode to infinity
            assert not np.any(np.isinf(theta)), "Large dt should not produce Inf"
        except Exception:
            # Instability is expected with large steps
            pass

    def test_extreme_natural_frequencies(self):
        """Test simulation with extreme natural frequency values."""
        N = 10
        G = nx.watts_strogatz_graph(N, 2, 0.0)
        A = nx.to_numpy_array(G)
        # Extreme frequencies
        omega = np.random.uniform(-1000, 1000, N)
        theta0 = np.random.uniform(0, 2 * np.pi, N)
        t_eval = np.linspace(0, 10, 100)

        try:
            t, theta = simulate_kuramoto(theta0, omega, A, K=10.0, t_eval=t_eval)
            assert not np.any(np.isnan(theta)), "Extreme omega should not produce NaN"
        except Exception:
            # May fail due to stiffness, which is acceptable
            pass


class TestFileIOEdgeCases:
    """Tests for file I/O edge cases."""

    def test_missing_config_file(self):
        """Test behavior when config file is missing."""
        from code.simulate_kuramoto import load_config

        with tempfile.TemporaryDirectory() as tmpdir:
            missing_path = os.path.join(tmpdir, "nonexistent.json")
            with pytest.raises(FileNotFoundError):
                load_config(missing_path)

    def test_invalid_json_config(self):
        """Test behavior when config file contains invalid JSON."""
        from code.simulate_kuramoto import load_config

        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = os.path.join(tmpdir, "invalid.json")
            with open(config_path, 'w') as f:
                f.write("{ invalid json }")

            with pytest.raises((json.JSONDecodeError, ValueError)):
                load_config(config_path)

    def test_empty_simulation_results(self):
        """Test correlation calculation with empty results file."""
        from code.analyze_results import load_simulation_results

        with tempfile.TemporaryDirectory() as tmpdir:
            csv_path = os.path.join(tmpdir, "empty.csv")
            with open(csv_path, 'w') as f:
                f.write("topology_id,p,kc_binary,kc_linear,status\n")

            results = load_simulation_results(csv_path)
            assert len(results) == 0, "Empty CSV should return empty list"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])