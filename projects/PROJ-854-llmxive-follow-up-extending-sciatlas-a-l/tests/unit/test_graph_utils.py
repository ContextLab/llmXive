import pytest
import networkx as nx
from src.models.graph_utils import calc_bridging

def test_calc_bridging_complete_graph():
    """
    Test that a complete graph (all nodes connected to all others)
    results in a bridging coefficient of 0.0 (no inter-cluster edges).
    """
    # Create a complete graph with 5 nodes
    G = nx.complete_graph(5)
    
    # Assign all nodes to the same cluster (0)
    clusters = {i: 0 for i in G.nodes()}
    
    result = calc_bridging(G, clusters)
    
    # In a complete graph where everyone is in the same cluster,
    # every edge is intra-cluster. Bridging coefficient should be 0.0.
    for node, coeff in result.items():
        assert coeff == 0.0, f"Node {node} should have bridging coefficient 0.0, got {coeff}"

def test_calc_bridging_bipartite_clusters():
    """
    Test a bipartite-like structure where nodes are split into two clusters
    and only connected across clusters. This should yield a high bridging coefficient.
    """
    # Create a graph: 0-1, 1-2, 2-3, 3-0 (a square)
    # Cluster A: {0, 2}, Cluster B: {1, 3}
    # Edges: (0,1) [cross], (1,2) [cross], (2,3) [cross], (3,0) [cross]
    # Every edge is an inter-cluster edge.
    G = nx.Graph()
    G.add_edges_from([(0, 1), (1, 2), (2, 3), (3, 0)])
    
    clusters = {0: 'A', 1: 'B', 2: 'A', 3: 'B'}
    
    result = calc_bridging(G, clusters)
    
    # Node 0: degree 2 (neighbors 1, 3). Both neighbors are in 'B'.
    # Inter-cluster edges = 2. Total degree = 2. Coeff = 1.0.
    assert result[0] == 1.0, f"Node 0 expected 1.0, got {result[0]}"
    assert result[1] == 1.0
    assert result[2] == 1.0
    assert result[3] == 1.0

def test_isolated_node():
    """
    Test that an isolated node (degree 0) is handled gracefully.
    According to spec, bridging coefficient for degree-0 nodes should be 0.0.
    """
    G = nx.Graph()
    G.add_node(0)  # Isolated node
    G.add_node(1)  # Another isolated node
    
    clusters = {0: 1, 1: 1}
    
    result = calc_bridging(G, clusters)
    
    # Check that isolated nodes have a bridging coefficient of 0.0
    assert 0 in result, "Result should contain isolated node 0"
    assert result[0] == 0.0, f"Isolated node 0 should have bridging coefficient 0.0, got {result[0]}"
    assert result[1] == 0.0, f"Isolated node 1 should have bridging coefficient 0.0, got {result[1]}"

def test_single_node_cluster():
    """
    Test a graph where one cluster contains only a single node.
    If that node has edges to other clusters, its bridging coefficient should be 1.0.
    """
    # Star graph: Center (0) connected to leaves (1, 2, 3)
    G = nx.star_graph(3)
    # Nodes: 0 (center), 1, 2, 3 (leaves)
    
    # Assign center to cluster 'A', leaves to cluster 'B'
    clusters = {0: 'A', 1: 'B', 2: 'B', 3: 'B'}
    
    result = calc_bridging(G, clusters)
    
    # Node 0 (center): degree 3. All neighbors (1, 2, 3) are in 'B'.
    # Inter-cluster edges = 3. Total degree = 3. Coeff = 1.0.
    assert result[0] == 1.0, f"Center node 0 should have bridging coefficient 1.0, got {result[0]}"
    
    # Leaf nodes (1, 2, 3): degree 1. Neighbor is 0 (cluster 'A').
    # Inter-cluster edges = 1. Total degree = 1. Coeff = 1.0.
    for leaf in [1, 2, 3]:
        assert result[leaf] == 1.0, f"Leaf node {leaf} should have bridging coefficient 1.0, got {result[leaf]}"

def test_calc_bridging_missing_cluster_assignment():
    """
    Test behavior when a node in the graph is missing from the clusters dictionary.
    The function should handle this gracefully, typically by skipping or assigning 0.0.
    """
    G = nx.Graph()
    G.add_edges_from([(0, 1), (1, 2)])
    
    # Node 2 is missing from clusters
    clusters = {0: 'A', 1: 'B'}
    
    # The function should not crash. It might return 0.0 or skip the node.
    # Based on typical implementation, it should handle missing keys.
    result = calc_bridging(G, clusters)
    
    # Check that the function ran without raising a KeyError
    assert isinstance(result, dict)
    # Depending on implementation, node 2 might be in result with 0.0 or not present.
    # We assert that 0 and 1 are present and valid.
    assert 0 in result
    assert 1 in result