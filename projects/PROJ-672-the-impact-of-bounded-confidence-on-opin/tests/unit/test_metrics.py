import pytest
import networkx as nx
import numpy as np
from code.utils.metrics import calculate_assortativity, calculate_average_path_length, calculate_structural_metrics

def test_assortativity_regular_graph():
    # Cycle graph is regular (all degrees = 2). Variance is 0.
    G = nx.cycle_graph(10)
    # Should return 0.0 instead of NaN
    assert calculate_assortativity(G) == 0.0

def test_path_length_disconnected():
    G = nx.Graph()
    G.add_edge(0, 1)
    G.add_edge(2, 3)
    # Should calculate based on largest component (size 2)
    # Path length of edge (0,1) is 1.0
    assert calculate_average_path_length(G) == 1.0

def test_structural_metrics_bundle():
    G = nx.erdos_renyi_graph(10, 0.5, seed=42)
    m = calculate_structural_metrics(G)
    assert "assortativity" in m
    assert "average_path_length" in m
    assert m["num_nodes"] == 10
