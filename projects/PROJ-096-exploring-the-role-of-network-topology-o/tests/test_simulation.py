"""
Integration tests for simulation module, focusing on binary search convergence.

This test suite verifies that the binary search algorithm for finding the critical
coupling strength (Kc) converges correctly and produces stable results across
different network topologies.
"""

import os
import sys
import json
import tempfile
import shutil
import numpy as np
import networkx as nx
import pytest
from pathlib import Path

# Add code directory to path for imports
code_path = Path(__file__).parent.parent / 'code'
sys.path.insert(0, str(code_path))

from simulate_kuramoto import (
    kuramoto_derivative,
    calculate_order_parameter,
    run_simulation,
    binary_search_kc,
    detect_synchronization
)


class TestBinarySearchConvergence:
    """Integration tests for binary search convergence in Kc detection."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Set up test fixtures."""
        self.test_dir = tempfile.mkdtemp()
        self.data_dir = Path(self.test_dir) / 'data' / 'processed'
        self.data_dir.mkdir(parents=True, exist_ok=True)

        # Create a minimal config.json
        config = {
            'time_steps': 1000,
            'n_topologies': 10,
            'runtime_estimate': 0.5,
            'contingency_flag': False,
            'SC_003_VIOLATION': False
        }
        with open(self.data_dir / 'config.json', 'w') as f:
            json.dump(config, f)

        yield

        # Cleanup
        shutil.rmtree(self.test_dir)

    def _create_test_graph(self, n_nodes=50, p_rewire=0.1):
        """Create a Watts-Strogatz graph for testing."""
        G = nx.watts_strogatz_graph(n_nodes, 4, p_rewire, seed=42)
        # Ensure connectivity
        if not nx.is_connected(G):
            G = nx.barabasi_albert_graph(n_nodes, 2, seed=42)
        return G

    def test_binary_search_convergence_on_regular_lattice(self):
        """Test binary search converges on a regular ring lattice (p=0.0)."""
        G = self._create_test_graph(n_nodes=50, p_rewire=0.0)

        # Binary search parameters
        k_min, k_max = 0.0, 5.0
        tol = 0.01
        max_iter = 20

        k_min_found, k_max_found, converged = binary_search_kc(
            G, k_min, k_max, tol, max_iter,
            time_steps=500, dt=0.01, seed=42
        )

        # Verify convergence
        assert converged, "Binary search should converge on regular lattice"
        assert k_min_found < k_max_found, "K_min should be less than K_max"
        assert (k_max_found - k_min_found) <= tol, "Convergence tolerance not met"

        # Regular lattices typically have higher Kc
        assert k_min_found > 0.1, "Kc should be non-trivial for regular lattice"

    def test_binary_search_convergence_on_small_world(self):
        """Test binary search converges on a small-world network (p=0.1)."""
        G = self._create_test_graph(n_nodes=50, p_rewire=0.1)

        k_min, k_max = 0.0, 5.0
        tol = 0.01
        max_iter = 20

        k_min_found, k_max_found, converged = binary_search_kc(
            G, k_min, k_max, tol, max_iter,
            time_steps=500, dt=0.01, seed=42
        )

        assert converged, "Binary search should converge on small-world network"
        assert k_min_found < k_max_found
        assert (k_max_found - k_min_found) <= tol

    def test_binary_search_convergence_on_random_graph(self):
        """Test binary search converges on a random graph (p=1.0)."""
        G = self._create_test_graph(n_nodes=50, p_rewire=1.0)

        k_min, k_max = 0.0, 5.0
        tol = 0.01
        max_iter = 20

        k_min_found, k_max_found, converged = binary_search_kc(
            G, k_min, k_max, tol, max_iter,
            time_steps=500, dt=0.01, seed=42
        )

        assert converged, "Binary search should converge on random graph"
        assert k_min_found < k_max_found
        assert (k_max_found - k_min_found) <= tol

    def test_binary_search_max_iterations(self):
        """Test that binary search respects max_iterations limit."""
        G = self._create_test_graph(n_nodes=50, p_rewire=0.1)

        # Use a very tight tolerance that may not be achievable
        k_min, k_max = 0.0, 5.0
        tol = 1e-10
        max_iter = 5  # Very low max iterations

        k_min_found, k_max_found, converged = binary_search_kc(
            G, k_min, k_max, tol, max_iter,
            time_steps=200, dt=0.01, seed=42
        )

        # Should not converge with such tight tolerance and low iterations
        assert not converged, "Should not converge with tight tolerance and low iterations"

    def test_binary_search_reproducibility(self):
        """Test that binary search produces reproducible results with same seed."""
        G = self._create_test_graph(n_nodes=50, p_rewire=0.1)

        k_min, k_max = 0.0, 5.0
        tol = 0.01
        max_iter = 20

        # Run twice with same seed
        k1_min, k1_max, _ = binary_search_kc(
            G, k_min, k_max, tol, max_iter,
            time_steps=500, dt=0.01, seed=42
        )

        k2_min, k2_max, _ = binary_search_kc(
            G, k_min, k_max, tol, max_iter,
            time_steps=500, dt=0.01, seed=42
        )

        # Results should be identical
        assert np.isclose(k1_min, k2_min), "Results should be reproducible with same seed"
        assert np.isclose(k1_max, k2_max), "Results should be reproducible with same seed"

    def test_binary_search_different_seeds(self):
        """Test that binary search produces similar but not identical results with different seeds."""
        G = self._create_test_graph(n_nodes=50, p_rewire=0.1)

        k_min, k_max = 0.0, 5.0
        tol = 0.01
        max_iter = 20

        # Run with different seeds
        k1_min, k1_max, _ = binary_search_kc(
            G, k_min, k_max, tol, max_iter,
            time_steps=500, dt=0.01, seed=42
        )

        k2_min, k2_max, _ = binary_search_kc(
            G, k_min, k_max, tol, max_iter,
            time_steps=500, dt=0.01, seed=123
        )

        # Results should be similar (within tolerance) but not necessarily identical
        # due to stochastic nature of initial conditions
        assert abs(k1_min - k2_min) < 0.5, "Results should be similar across seeds"
        assert abs(k1_max - k2_max) < 0.5, "Results should be similar across seeds"

    def test_binary_search_handles_non_convergence(self):
        """Test that binary search handles cases where convergence is not achieved."""
        G = self._create_test_graph(n_nodes=50, p_rewire=0.1)

        # Use parameters that make convergence unlikely
        k_min, k_max = 0.0, 0.1  # Very narrow range
        tol = 0.001
        max_iter = 3  # Very few iterations

        k_min_found, k_max_found, converged = binary_search_kc(
            G, k_min, k_max, tol, max_iter,
            time_steps=200, dt=0.01, seed=42
        )

        # Should not converge
        assert not converged, "Should not converge with narrow range and few iterations"
        assert k_min_found <= k_max_found, "Range should remain valid"

    def test_binary_search_output_format(self):
        """Test that binary search returns correct output format."""
        G = self._create_test_graph(n_nodes=50, p_rewire=0.1)

        k_min, k_max = 0.0, 5.0
        tol = 0.01
        max_iter = 20

        result = binary_search_kc(
            G, k_min, k_max, tol, max_iter,
            time_steps=500, dt=0.01, seed=42
        )

        # Should return a tuple of 3 elements
        assert isinstance(result, tuple), "Should return a tuple"
        assert len(result) == 3, "Should return 3 elements"

        k_min_val, k_max_val, converged = result

        assert isinstance(k_min_val, (int, float)), "k_min should be numeric"
        assert isinstance(k_max_val, (int, float)), "k_max should be numeric"
        assert isinstance(converged, bool), "converged should be boolean"

    def test_binary_search_with_high_coupling(self):
        """Test binary search correctly identifies synchronization at high coupling."""
        G = self._create_test_graph(n_nodes=50, p_rewire=0.1)

        # At very high coupling, should synchronize
        k_min, k_max = 3.0, 5.0
        tol = 0.01
        max_iter = 20

        k_min_found, k_max_found, converged = binary_search_kc(
            G, k_min, k_max, tol, max_iter,
            time_steps=500, dt=0.01, seed=42
        )

        assert converged, "Should converge even at high coupling range"
        # The found Kc should be within the tested range
        assert k_min_found >= 3.0, "Kc should be at least the lower bound"

    def test_binary_search_with_low_coupling(self):
        """Test binary search correctly identifies no synchronization at low coupling."""
        G = self._create_test_graph(n_nodes=50, p_rewire=0.1)

        # At very low coupling, should not synchronize
        k_min, k_max = 0.0, 0.5
        tol = 0.01
        max_iter = 20

        k_min_found, k_max_found, converged = binary_search_kc(
            G, k_min, k_max, tol, max_iter,
            time_steps=500, dt=0.01, seed=42
        )

        assert converged, "Should converge even at low coupling range"
        # The found Kc should be within the tested range
        assert k_max_found <= 0.5, "Kc should be at most the upper bound"

    def test_binary_search_consistency_across_topologies(self):
        """Test that binary search produces consistent results across similar topologies."""
        # Create multiple similar graphs
        graphs = [
            self._create_test_graph(n_nodes=50, p_rewire=0.1) for _ in range(3)
        ]

        k_min, k_max = 0.0, 5.0
        tol = 0.01
        max_iter = 20

        kc_values = []
        for G in graphs:
            k_min_found, k_max_found, converged = binary_search_kc(
                G, k_min, k_max, tol, max_iter,
                time_steps=500, dt=0.01, seed=42
            )
            if converged:
                kc_values.append((k_min_found + k_max_found) / 2)

        assert len(kc_values) == 3, "All graphs should converge"

        # Check that Kc values are reasonably similar (within 20% of mean)
        mean_kc = np.mean(kc_values)
        for kc in kc_values:
            assert abs(kc - mean_kc) / mean_kc < 0.2, \
                f"Kc values should be consistent across similar topologies: {kc_values}"

    def test_binary_search_edge_case_single_iteration(self):
        """Test binary search with minimal iterations."""
        G = self._create_test_graph(n_nodes=50, p_rewire=0.1)

        k_min, k_max = 0.0, 5.0
        tol = 1.0  # Very loose tolerance
        max_iter = 1  # Single iteration

        k_min_found, k_max_found, converged = binary_search_kc(
            G, k_min, k_max, tol, max_iter,
            time_steps=200, dt=0.01, seed=42
        )

        # May or may not converge depending on tolerance
        assert k_min_found <= k_max_found, "Range should remain valid"
        assert k_min_found >= 0.0, "K_min should be non-negative"
        assert k_max_found <= 5.0, "K_max should not exceed upper bound"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])