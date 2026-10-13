"""
Unit tests for the HK simulation implementation.
"""
import numpy as np
import networkx as nx
from code.simulate_hk import run_simulation
from utils.convergence import compute_clusters, has_converged

def test_hk_converges_within_reasonable_iterations():
    # Small random graph (50 nodes)
    G = nx.erdos_renyi_graph(50, 0.1, seed=42)
    epsilon = 0.2
    seed = 12345

    result = run_simulation(G, epsilon=epsilon, seed=seed, max_iter=5000, tol=1e-4)

    assert result["status"] == "converged"
    assert isinstance(result["convergence_time"], int)
    assert result["convergence_time"] <= 500

    # Verify clusters respect the confidence bound
    final_ops = np.array(result["final_opinions"])
    clusters = compute_clusters(final_ops, epsilon, node_ids=sorted(G.nodes()))
    for cluster in clusters:
        cluster_ops = [final_ops[sorted(G.nodes()).index(node)] for node in cluster]
        for i in range(len(cluster_ops)):
            for j in range(i + 1, len(cluster_ops)):
                assert abs(cluster_ops[i] - cluster_ops[j]) <= epsilon + 1e-8

def test_hk_respects_max_iter_limit():
    # Configuration that needs more than 5 iterations
    G = nx.erdos_renyi_graph(50, 0.02, seed=7)
    epsilon = 0.05
    seed = 999

    result = run_simulation(G, epsilon=epsilon, seed=seed, max_iter=5, tol=1e-4)

    assert result["status"] == "non_converged"
    assert result["convergence_time"] is None
