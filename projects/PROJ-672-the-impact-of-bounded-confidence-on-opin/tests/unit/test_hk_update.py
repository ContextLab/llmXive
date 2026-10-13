"""
Unit tests for the Hegselmann‑Krause update logic.
These tests verify that the ``run_simulation`` function from
``code.simulate_hk`` behaves as expected on a small synthetic graph.
"""

import numpy as np
import networkx as nx
import pytest

from simulate_hk import run_simulation

@pytest.fixture
def small_graph():
    # Simple 5‑node ring graph
    G = nx.cycle_graph(5)
    return G

def test_converged_small_graph(small_graph):
    # With a relatively large epsilon the system should converge quickly
    epsilon = 0.3
    seed = 42
    result = run_simulation(small_graph, epsilon=epsilon, seed=seed, max_iter=500, tol=1e-4)
    assert result["status"] == "converged"
    assert result["convergence_time"] is not None
    assert result["convergence_time"] <= 200

    # Verify that all opinion updates respect the confidence bound
    opinions = np.array(result["final_opinions"])
    # Since the graph is a ring, each node has two neighbours
    for node in small_graph.nodes():
        neighbours = list(small_graph.neighbors(node)) + [node]
        diffs = np.abs(opinions[node] - opinions[neighbours])
        assert np.all(diffs <= epsilon + 1e-8)

def test_non_converged_due_to_max_iter(small_graph):
    # Force non‑convergence by setting a very low max_iter
    epsilon = 0.2
    seed = 123
    result = run_simulation(small_graph, epsilon=epsilon, seed=seed, max_iter=5, tol=1e-4)
    assert result["status"] == "non_converged"
    assert result["convergence_time"] is None