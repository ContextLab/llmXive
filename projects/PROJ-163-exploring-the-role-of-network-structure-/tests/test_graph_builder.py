import pytest
import networkx as nx
from graph_builder import (
    build_coupling_graph,
    compute_shortest_path_metrics,
    compute_edge_betweenness_and_spectral_gap,
)

def test_build_coupling_graph():
    # Simple directed edge list should become undirected
    coupling_map = [[0, 1], [1, 2], [2, 3]]
    G = build_coupling_graph(coupling_map)
    assert isinstance(G, nx.Graph)
    assert G.number_of_nodes() == 4
    assert G.number_of_edges() == 3
    # Ensure edges are undirected (both directions present implicitly)
    assert G.has_edge(1, 0)
    assert G.has_edge(2, 1)
    assert G.has_edge(3, 2)

def test_compute_shortest_path_metrics_path_graph():
    # Path graph of 4 nodes
    G = nx.path_graph(4)  # edges: 0-1-2-3
    metrics = compute_shortest_path_metrics(G)
    # Average shortest path length = 10/6 ≈ 1.6667
    assert pytest.approx(metrics["avg_shortest_path"], rel=1e-3) == 1.6666666666666667
    assert metrics["diameter"] == 3

def test_compute_edge_betweenness_and_spectral_gap_disconnected():
    # Two-component graph: edges 0-1 and 2-3
    G = nx.Graph()
    G.add_edge(0, 1)
    G.add_edge(2, 3)
    metrics = compute_edge_betweenness_and_spectral_gap(G)
    # Spectral gap should be 0 for disconnected graphs per C-002
    assert metrics["spectral_gap"] == 0.0
    # Edge betweenness mean should be 1.0 for each edge in this simple case
    # (each edge lies on the only shortest path between its two nodes)
    assert pytest.approx(metrics["edge_betweenness_mean"], rel=1e-6) == 1.0