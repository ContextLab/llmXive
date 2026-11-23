import numpy as np
import networkx as nx
import pytest
from src.simulation import find_critical_coupling, discrete_sweep_fallback
from data_models import SynchronizationStatus

def test_ring_graph_analytical_match_pct():
    """
    Verify that the critical coupling found for a ring graph matches the analytical
    approximation K_c ≈ (2 * π²) / N within a 5 % relative error.
    """
    N = 200
    G = nx.cycle_graph(N)

    # Analytical approximation for the Kuramoto model on a 1‑D lattice
    analytical_Kc = (2 * np.pi**2) / N

    # Use the bisection search implementation with a modest tolerance
    Kc = find_critical_coupling(
        G,
        K_min=0.0,
        K_max=2.0,
        tol=0.01,
        max_iter=50,
        seed=123,
    )

    assert Kc is not None, "Critical coupling should be found for a connected ring graph"
    rel_error = abs(Kc - analytical_Kc) / analytical_Kc
    assert rel_error <= 0.05, f"Relative error {rel_error:.2%} exceeds 5 %"

def test_k_sweep_converges():
    """
    Ensure that the critical coupling search converges for a typical random graph
    and that the discrete fallback also produces a valid coupling value.
    """
    # Generate a modestly sized Erdős–Rényi graph
    G = nx.erdos_renyi_graph(50, 0.3, seed=42)

    # Bisection search should return a finite coupling within the search interval
    Kc = find_critical_coupling(
        G,
        K_min=0.0,
        K_max=5.0,
        tol=0.001,
        max_iter=30,
        seed=42,
    )
    assert Kc is not None, "Bisection failed to locate a critical coupling"
    assert 0.0 < Kc <= 5.0, f"Critical coupling {Kc} lies outside expected bounds"

    # If bisection were to fail, the discrete sweep fallback must still yield a result
    Kc_fallback = discrete_sweep_fallback(G, K_min=0.0, K_max=5.0, step=0.1, seed=42)
    assert Kc_fallback is not None, "Discrete sweep fallback did not return a coupling"
    assert 0.0 <= Kc_fallback <= 5.0, f"Fallback coupling {Kc_fallback} out of bounds"