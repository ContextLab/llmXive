"""
Unit tests for the HK simulation implementation.

The tests verify:

1. Convergence for a moderate confidence bound.
2. That the returned clusters respect the confidence bound.
3. Proper handling of the ``max_iter`` limit.
"""

import json

import numpy as np
import networkx as nx

from code.simulate_hk import run_simulation
from utils.convergence import compute_clusters, has_converged


def _one_more_iteration(G, opinions, epsilon):
    """Utility to apply a single HK update step (mirrors internal logic)."""
    node_ids = sorted(G.nodes())
    node_index = {node: idx for idx, node in enumerate(node_ids)}
    new_ops = np.empty_like(opinions)
    for node in G.nodes():
        i = node_index[node]
        neighbours = [node] + list(G.neighbors(node))
        eligible = [
            node_index[nbr]
            for nbr in neighbours
            if abs(opinions[i] - opinions[node_index[nbr]]) <= epsilon
        ]
        new_ops[i] = opinions[eligible].mean()
    return new_ops


def test_hk_converges_within_reasonable_iterations():
    # Small random graph (50 nodes) – deterministic seed for reproducibility
    G = nx.erdos_renyi_graph(50, 0.1, seed=42)
    epsilon = 0.2
    seed = 12345

    result = run_simulation(G, epsilon=epsilon, seed=seed, max_iter=5000, tol=1e-4)

    assert result["status"] == "converged"
    assert isinstance(result["convergence_time"], int)
    # The reference implementation converges quickly on this size of graph
    assert result["convergence_time"] <= 200

    # Verify that a *single* additional update changes opinions by less than tol
    final_ops = np.array(result["final_opinions"])
    next_ops = _one_more_iteration(G, final_ops, epsilon)
    assert has_converged(final_ops, next_ops, tol=1e-4)

    # Verify that the reported clusters respect the confidence bound
    clusters = compute_clusters(final_ops, epsilon, node_ids=sorted(G.nodes()))
    for cluster in clusters:
        # Extract opinions of the nodes in this cluster
        cluster_ops = [final_ops[sorted(G.nodes()).index(node)] for node in cluster]
        # All pairwise differences must be <= epsilon
        for i in range(len(cluster_ops)):
            for j in range(i + 1, len(cluster_ops)):
                assert abs(cluster_ops[i] - cluster_ops[j]) <= epsilon


def test_hk_respects_max_iter_limit():
    # A configuration that typically needs >5 iterations to converge
    G = nx.erdos_renyi_graph(50, 0.02, seed=7)
    epsilon = 0.05
    seed = 999

    result = run_simulation(G, epsilon=epsilon, seed=seed, max_iter=5, tol=1e-4)

    assert result["status"] == "non_converged"
    assert result["convergence_time"] is None