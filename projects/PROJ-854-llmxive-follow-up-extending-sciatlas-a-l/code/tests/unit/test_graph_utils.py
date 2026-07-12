import pytest
import networkx as nx
from src.models.graph_utils import calc_bridging

def test_calc_bridging_complete_graph():
    G = nx.complete_graph(5)
    clusters = {str(i): 0 for i in range(5)}
    result = calc_bridging(G, clusters)
    for node, coef in result.items():
        assert coef == 0.0

def test_calc_bridging_bipartite_clusters():
    G = nx.Graph()
    G.add_edges_from([(0, 1), (2, 3), (0, 2), (1, 3)])
    clusters = {str(0): 0, str(1): 0, str(2): 1, str(3): 1}
    result = calc_bridging(G, clusters)
    assert result['0'] == 0.5
    assert result['1'] == 0.5
    assert result['2'] == 0.5
    assert result['3'] == 0.5

def test_isolated_node():
    G = nx.Graph()
    G.add_node(0)
    clusters = {str(0): 0}
    result = calc_bridging(G, clusters)
    assert result['0'] == 0.0

def test_single_node_cluster():
    G = nx.path_graph(4)
    clusters = {str(i): 0 for i in range(4)}
    result = calc_bridging(G, clusters)
    for node, coef in result.items():
        assert coef == 0.0

def test_calc_bridging_missing_cluster_assignment():
    G = nx.Graph()
    G.add_edges_from([(0, 1), (1, 2)])
    clusters = {str(0): 0, str(1): 0}
    try:
        result = calc_bridging(G, clusters)
    except KeyError:
        pytest.fail("calc_bridging raised KeyError for missing cluster assignment")