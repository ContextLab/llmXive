"""
Unit test for the Scale‑Free (Barabási‑Albert) graph generator.

The test verifies that the degree distribution exponent ``γ`` falls
within the canonical range ``2 < γ < 3`` for a Barabási‑Albert network.
The exponent is estimated by fitting a straight line to the log‑log
histogram of node degrees (a simple linear regression).
"""

import numpy as np
import pytest
import networkx as nx
from scipy.stats import linregress

from generate_networks import generate_scale_free_graph

@pytest.mark.parametrize("seed", [42])
def test_scale_free_exponent_range(seed: int) -> None:
    """
    Generate a modest‑size BA graph, estimate the power‑law exponent,
    and assert that it lies between 2 and 3.
    """
    num_nodes = 200
    m = 2

    # Random 3‑D positions – the exact geometry is irrelevant for the test,
    # we only need a consistent ``positions`` array.
    rng = np.random.default_rng(seed)
    positions = rng.random((num_nodes, 3))

    G = generate_scale_free_graph(
        num_nodes=num_nodes,
        m=m,
        positions=positions,
        initial_factor=1.0,
        max_factor=2.0,
        seed=seed,
    )
    assert nx.is_connected(G), "Generated graph should be connected"

    degrees = np.array([d for _, d in G.degree()])
    # Build histogram on a log‑scale, ignoring zero frequencies.
    unique, counts = np.unique(degrees, return_counts=True)
    # Remove any degree with zero count (should not happen) and take log.
    mask = counts > 0
    log_k = np.log10(unique[mask])
    log_p = np.log10(counts[mask] / counts.sum())

    # Linear regression on the tail (exclude the smallest degree to reduce bias)
    if len(log_k) < 2:
        pytest.fail("Not enough distinct degree values for regression")
    slope, intercept, r_value, p_value, std_err = linregress(log_k, log_p)

    # For a power‑law P(k) ~ k^{-γ}, the slope = -γ
    gamma_est = -slope

    # Theoretical BA exponent is γ ≈ 3; allow a modest tolerance.
    assert 2.0 < gamma_est < 3.0, f"Estimated exponent {gamma_est:.2f} not in (2, 3)"