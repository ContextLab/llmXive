"""
Unit tests for graph_utils.py.
"""
import pytest
from collections import deque
from code.utils.graph_utils import build_undirected_graph, shortest_path_bfs, get_connected_components

def test_shortest_path_bfs_connected():
    graph = {"A": ["B"], "B": ["A", "C"], "C": ["B"]}
    adj = build_undirected_graph(graph)
    path = shortest_path_bfs(adj, "A", "C")
    assert path == ["A", "B", "C"]

def test_shortest_path_bfs_disconnected():
    graph = {"A": ["B"], "C": []}
    adj = build_undirected_graph(graph)
    path = shortest_path_bfs(adj, "A", "C")
    assert path is None

def test_connected_components():
    graph = {"A": ["B"], "B": ["A"], "C": ["D"], "D": ["C"]}
    adj = build_undirected_graph(graph)
    comps = get_connected_components(adj)
    assert len(comps) == 2

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
