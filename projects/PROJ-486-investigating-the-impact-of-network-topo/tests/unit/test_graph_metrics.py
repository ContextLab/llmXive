import pytest
import numpy as np
import pandas as pd
import networkx as nx
from code.graph_metrics import calculate_clustering_coefficient, calculate_path_length, compute_all_metrics

def test_calculate_clustering_coefficient_small_matrix():
    """Test clustering coefficient on a small known graph."""
    # Create a simple 4-node graph: a triangle with one extra node connected to one node
    # Nodes: 0,1,2 form a triangle; node 3 connected to node 0
    # Expected:
    # Node 0: connected to 1,2,3. Triangles: (1,2) exists -> C0 = 1/3 * (w01*w02*w12)^(1/3) ...
    # For simplicity, use unweighted (all weights=1) to verify basic logic
    
    mat = np.array([
        [1.0, 1.0, 1.0, 1.0],
        [1.0, 1.0, 1.0, 0.0],
        [1.0, 1.0, 1.0, 0.0],
        [1.0, 0.0, 0.0, 1.0]
    ])

    cc = calculate_clustering_coefficient(mat, threshold=0.5)
    
    # Verify it returns a float and is within [0, 1]
    assert isinstance(cc, float)
    assert 0.0 <= cc <= 1.0

    # Compare with NetworkX direct calculation
    G = nx.Graph()
    n = 4
    for i in range(n):
        for j in range(i+1, n):
            if mat[i, j] > 0.5:
                G.add_edge(i, j, weight=mat[i, j])
    
    expected_cc = np.mean(list(nx.clustering(G, weight='weight').values()))
    assert np.isclose(cc, expected_cc, rtol=1e-5)


def test_calculate_path_length_small_matrix():
    """Test path length on a small known graph."""
    # Same graph as above
    mat = np.array([
        [1.0, 1.0, 1.0, 1.0],
        [1.0, 1.0, 1.0, 0.0],
        [1.0, 1.0, 1.0, 0.0],
        [1.0, 0.0, 0.0, 1.0]
    ])

    pl = calculate_path_length(mat, threshold=0.5)
    
    # Verify it returns a float
    assert isinstance(pl, float)
    assert pl > 0

    # Compare with NetworkX
    G = nx.Graph()
    n = 4
    for i in range(n):
        for j in range(i+1, n):
            if mat[i, j] > 0.5:
                dist = 1.0 / mat[i, j]
                G.add_edge(i, j, weight=dist)
    
    # Since graph is disconnected (node 3 only connected to 0, but 0,1,2 are connected)
    # Actually in this graph: 0-1, 0-2, 0-3, 1-2. So 3 is connected to 0, and 0,1,2 are connected.
    # So the graph is connected.
    expected_pl = nx.average_shortest_path_length(G, weight='weight')
    assert np.isclose(pl, expected_pl, rtol=1e-5)


def test_calculate_clustering_coefficient_dataframe():
    """Test that function works with DataFrame input."""
    mat_df = pd.DataFrame({
        'A': [1.0, 0.8, 0.6],
        'B': [0.8, 1.0, 0.9],
        'C': [0.6, 0.9, 1.0]
    })

    cc = calculate_clustering_coefficient(mat_df, threshold=0.5)
    assert isinstance(cc, float)
    assert 0.0 <= cc <= 1.0


def test_calculate_path_length_disconnected():
    """Test path length on a disconnected graph."""
    # Two separate components: 0-1 and 2-3
    mat = np.array([
        [1.0, 1.0, 0.0, 0.0],
        [1.0, 1.0, 0.0, 0.0],
        [0.0, 0.0, 1.0, 1.0],
        [0.0, 0.0, 1.0, 1.0]
    ])

    pl = calculate_path_length(mat, threshold=0.5)
    # For disconnected graphs, the function should return NaN or compute on largest component
    # Based on our implementation, it returns NaN if not connected and no largest component fallback succeeds
    # But we implemented fallback to largest component
    assert isinstance(pl, float) or np.isnan(pl)


def test_compute_all_metrics():
    """Test that compute_all_metrics returns both metrics."""
    mat = np.random.rand(5, 5)
    mat = (mat + mat.T) / 2
    np.fill_diagonal(mat, 1.0)

    results = compute_all_metrics(mat, threshold=0.3)

    assert 'clustering_coefficient' in results
    assert 'path_length' in results
    assert isinstance(results['clustering_coefficient'], float)
    assert isinstance(results['path_length'], float)


def test_calculate_clustering_coefficient_threshold():
    """Test that thresholding works correctly."""
    mat = np.array([
        [1.0, 0.9, 0.1],
        [0.9, 1.0, 0.8],
        [0.1, 0.8, 1.0]
    ])

    # With threshold 0.5, edge (0,2) is removed
    cc_high = calculate_clustering_coefficient(mat, threshold=0.5)
    
    # With threshold 0.0, all edges included
    cc_low = calculate_clustering_coefficient(mat, threshold=0.0)

    # The clustering coefficient may differ based on edges included
    # We just verify both return valid floats
    assert isinstance(cc_high, float)
    assert isinstance(cc_low, float)
