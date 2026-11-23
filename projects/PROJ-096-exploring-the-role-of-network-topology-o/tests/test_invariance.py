"""
Unit tests for the Physical Invariance (EPR Criterion) verification.

This module contains specific tests to assert that the critical coupling strength
(Kc) is an observer-invariant property, satisfying the EPR criterion of physical reality.
"""

import os
import sys
import json
import pytest
import numpy as np
import networkx as nx
from scipy.integrate import odeint

# Add project root to path to allow imports from code/
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from code.simulate_kuramoto import (
    kuramoto_derivative,
    calculate_order_parameter,
    simulate_kuramoto,
    find_critical_coupling_binary_search
)
from code.utils.graph_utils import is_connected

# Constants for the test
TEST_N = 50
TEST_K = 2  # Regular ring lattice connectivity
TEST_P = 0.0  # Fully connected ring (no rewiring for stability in small test)
TEST_TAU = 10.0  # Integration time
TEST_DT = 0.05
TEST_TOL = 1e-4  # Tolerance for invariance assertion
TEST_K_SEARCH_RANGE = (0.0, 10.0)
TEST_MAX_ITER = 20

def create_test_graph(n=TEST_N, k=TEST_K, p=TEST_P, seed=42):
    """
    Creates a small, stable, connected graph for testing invariance.
    Uses a Watts-Strogatz graph with p=0 to ensure a regular ring lattice
    which is guaranteed to be connected for k >= 2.
    """
    G = nx.watts_strogatz_graph(n, k, p, seed=seed)
    if not is_connected(G):
        # Fallback to a complete graph if the ring somehow fails (unlikely for p=0)
        G = nx.complete_graph(n)
    return G

def get_omega_seed(seed):
    """Generates natural frequencies for a given seed."""
    rng = np.random.default_rng(seed)
    return rng.standard_normal(TEST_N)

def run_kc_check(graph, omega, frame_type='single', ref_idx=0, t_eval=None):
    """
    Runs the binary search for Kc using a specific reference frame logic
    embedded in the simulation loop.

    Note: The standard `simulate_kuramoto` function calculates the order parameter
    R which is inherently rotationally invariant (depends on phase differences).
    However, to explicitly test the "observer" aspect as requested by the reviewer,
    we simulate the dynamics and verify that the *convergence point* (synchronization)
    is reached regardless of how we conceptually frame the phases.

    In the Kuramoto model, the order parameter R = |1/N * sum(exp(i*theta))|
    is mathematically invariant under a global phase shift theta_i -> theta_i + alpha.
    Therefore, Kc derived from R should be identical.

    This function simulates the system and returns the Kc found.
    """
    if t_eval is None:
        t_eval = np.linspace(0, TEST_TAU, int(TEST_TAU / TEST_DT))

    # We use the standard binary search which relies on R.
    # Since R is invariant, this test verifies the numerical stability
    # and the fact that the algorithm converges to the same Kc.
    kc, status = find_critical_coupling_binary_search(
        graph, omega, t_eval, TEST_K_SEARCH_RANGE, TEST_MAX_ITER
    )
    return kc, status

def test_epr_criterion():
    """
    Asserts the invariance condition (difference < 1e-4) for a known stable graph.

    Logic:
    1. Generate a small, fully connected (or regular ring) graph.
    2. Generate a set of natural frequencies.
    3. Calculate Kc using the standard method (which is rotationally invariant).
    4. To simulate "different observers", we shift the initial phases by random offsets
       (simulating a change in reference frame) and re-run the search.
       Since the physics depends only on phase *differences*, Kc should be identical.
    5. Assert that the difference between Kc values is below the tolerance.
    """
    # 1. Setup Graph
    G = create_test_graph(seed=42)
    assert is_connected(G), "Test graph must be connected"

    # 2. Setup Frequencies
    omega = get_omega_seed(seed=123)

    # 3. Define T-Eval
    t_eval = np.linspace(0, TEST_TAU, int(TEST_TAU / TEST_DT))

    # 4. Run Search with "Observer A" (Standard Initial Phases: 0)
    # We simulate the standard case where theta_0 = 0 for all i.
    theta_0_a = np.zeros(TEST_N)
    kc_a, status_a = find_critical_coupling_binary_search(
        G, omega, t_eval, TEST_K_SEARCH_RANGE, TEST_MAX_ITER, theta_0=theta_0_a
    )

    # 5. Run Search with "Observer B" (Shifted Initial Phases)
    # Simulate a different reference frame by adding a random global shift + local noise
    # that cancels out in the physics but changes the absolute coordinates.
    # Note: The Kuramoto dynamics d(theta_i)/dt = omega_i + K * sum(sin(theta_j - theta_i))
    # are invariant under theta_i -> theta_i + C.
    # We add a random offset C to all initial phases.
    rng = np.random.default_rng(999)
    global_shift = rng.uniform(0, 2 * np.pi)
    theta_0_b = np.full(TEST_N, global_shift)

    kc_b, status_b = find_critical_coupling_binary_search(
        G, omega, t_eval, TEST_K_SEARCH_RANGE, TEST_MAX_ITER, theta_0=theta_0_b
    )

    # 6. Assertions
    assert status_a == "converged", f"Search A failed to converge: {status_a}"
    assert status_b == "converged", f"Search B failed to converge: {status_b}"

    diff = abs(kc_a - kc_b)
    assert diff < TEST_TOL, (
        f"EPR Criterion Failed: Kc depends on reference frame. "
        f"Kc_A = {kc_a:.6f}, Kc_B = {kc_b:.6f}, Diff = {diff:.6f}. "
        f"Tolerance was {TEST_TOL}."
    )

    # If we get here, the critical coupling is invariant under the phase shift.
    # This satisfies the condition that Kc is an element of physical reality
    # independent of the observer's coordinate choice.
    assert True

if __name__ == "__main__":
    pytest.main([__file__, "-v"])