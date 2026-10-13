"""
Unit tests for the Hegselmann‑Krause update logic.
"""
import numpy as np
import networkx as nx
import pytest
from code.simulate_hk import run_simulation

@pytest.fixture
def small_graph():
    return nx.cycle_graph(5)

def test_converged_small_graph(small_graph):
    epsilon = 0.3
    seed = 42
    result = run_simulation(small_graph, epsilon=epsilon, seed=seed, max_iter=500, tol=1e-4)
    assert result["status"] == "converged"
    
    opinions = np.array(result["final_opinions"])
    node_ids = sorted(small_graph.nodes())
    node_index = {node: idx for idx, node in enumerate(node_ids)}
    
    for node in small_graph.nodes():
        i = node_index[node]
        neighbours = [node] + list(small_graph.neighbors(node))
        eligible = [
            node_index[nbr]
            for nbr in neighbours
            if abs(opinions[i] - opinions[node_index[nbr]]) <= epsilon + 1e-8
        ]
        # The final opinion must be the average of its eligible neighbors
        expected_val = opinions[eligible].mean()
        assert np.abs(opinions[i] - expected_val) < 1e-4

def test_non_converged_due_to_max_iter(small_graph):
    epsilon = 0.2
    seed = 123
    result = run_simulation(small_graph, epsilon=epsilon, seed=seed, max_iter=2, tol=1e-4)
    assert result["status"] == "non_converged"
    assert result["convergence_time"] is None