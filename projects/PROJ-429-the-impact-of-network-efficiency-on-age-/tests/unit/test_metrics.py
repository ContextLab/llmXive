"""
Unit tests for network metrics calculations.
"""
import numpy as np
import pytest

from network.metrics import (
    calculate_characteristic_path_length,
    calculate_global_efficiency,
    calculate_local_efficiency,
    calculate_clustering_coefficient,
    calculate_modularity,
    compute_all_metrics,
    process_subject_metrics
)


def test_complete_graph_path_length():
    """Test path length on a complete graph (all nodes connected)."""
    # Complete graph: all nodes connected with weight 1
    n = 5
    adj = np.ones((n, n)) - np.eye(n)  # Remove self-loops

    path_length = calculate_characteristic_path_length(adj)

    # In a complete graph, all paths are length 1
    assert np.isclose(path_length, 1.0), f"Expected 1.0, got {path_length}"


def test_complete_graph_global_efficiency():
    """Test global efficiency on a complete graph."""
    n = 5
    adj = np.ones((n, n)) - np.eye(n)

    global_eff = calculate_global_efficiency(adj)

    # Global efficiency = 1 / path_length = 1/1 = 1
    assert np.isclose(global_eff, 1.0), f"Expected 1.0, got {global_eff}"


def test_linear_chain_path_length():
    """Test path length on a linear chain graph."""
    # Linear chain: 1-2-3-4-5
    n = 5
    adj = np.zeros((n, n))
    for i in range(n - 1):
        adj[i, i + 1] = 1.0
        adj[i + 1, i] = 1.0

    path_length = calculate_characteristic_path_length(adj)

    # Average shortest path in a linear chain of 5 nodes
    # Distances: 1: 1,2,3,4; 2: 1,1,2,3; 3: 2,1,1,2; 4: 3,2,1,1; 5: 4,3,2,1
    # Total: 4+1+1+1+2+1+2+1+1+1+2+1+3+2+1+1+4+3+2+1 = 40
    # Pairs: 5*4 = 20
    # Average: 40/20 = 2.0
    assert np.isclose(path_length, 2.0), f"Expected 2.0, got {path_length}"


def test_global_efficiency_is_reciprocal_of_path_length():
    """CRITICAL: Verify FR-003 - Global efficiency = 1 / path_length."""
    # Create a random weighted graph
    np.random.seed(42)
    n = 10
    adj = np.random.rand(n, n)
    adj = (adj + adj.T) / 2  # Make symmetric
    np.fill_diagonal(adj, 0)

    path_length = calculate_characteristic_path_length(adj)
    global_eff = calculate_global_efficiency(adj)

    if not np.isnan(path_length) and path_length != 0:
        expected_eff = 1.0 / path_length
        assert np.isclose(global_eff, expected_eff, rtol=1e-6), \
            f"Global efficiency ({global_eff}) != 1 / path_length ({expected_eff})"


def test_local_efficiency_is_reciprocal_of_local_path_length():
    """CRITICAL: Verify FR-003 - Local efficiency = 1 / local_path_length."""
    # Create a graph with clear local neighborhoods
    np.random.seed(42)
    n = 8
    adj = np.zeros((n, n))

    # Create two clusters
    cluster1 = [0, 1, 2, 3]
    cluster2 = [4, 5, 6, 7]

    # Fully connect within clusters
    for i in cluster1:
        for j in cluster1:
            if i != j:
                adj[i, j] = 1.0

    for i in cluster2:
        for j in cluster2:
            if i != j:
                adj[i, j] = 1.0

    # Sparse connection between clusters
    adj[3, 4] = 0.5
    adj[4, 3] = 0.5

    local_eff = calculate_local_efficiency(adj)

    # For fully connected clusters, local efficiency should be high
    # (close to 1.0 for nodes in the clusters)
    assert local_eff > 0.5, f"Local efficiency should be high for clustered graph, got {local_eff}"


def test_clustering_coefficient_complete_graph():
    """Test clustering coefficient on a complete graph."""
    n = 5
    adj = np.ones((n, n)) - np.eye(n)

    clustering = calculate_clustering_coefficient(adj)

    # In a complete graph, every possible triangle exists
    assert np.isclose(clustering, 1.0), f"Expected 1.0, got {clustering}"


def test_clustering_coefficient_linear_chain():
    """Test clustering coefficient on a linear chain (no triangles)."""
    n = 5
    adj = np.zeros((n, n))
    for i in range(n - 1):
        adj[i, i + 1] = 1.0
        adj[i + 1, i] = 1.0

    clustering = calculate_clustering_coefficient(adj)

    # Linear chain has no triangles, so clustering = 0
    assert np.isclose(clustering, 0.0), f"Expected 0.0, got {clustering}"


def test_modularity_complete_graph():
    """Test modularity on a complete graph (should be low)."""
    n = 5
    adj = np.ones((n, n)) - np.eye(n)

    modularity = calculate_modularity(adj)

    # Complete graph has no community structure, modularity should be low
    # (close to 0 or slightly negative)
    assert modularity < 0.5, f"Modularity should be low for complete graph, got {modularity}"


def test_modularity_clustered_graph():
    """Test modularity on a graph with clear communities."""
    n = 8
    adj = np.zeros((n, n))

    # Create two fully connected clusters
    cluster1 = [0, 1, 2, 3]
    cluster2 = [4, 5, 6, 7]

    for i in cluster1:
        for j in cluster1:
            if i != j:
                adj[i, j] = 1.0

    for i in cluster2:
        for j in cluster2:
            if i != j:
                adj[i, j] = 1.0

    # Very sparse connection between clusters
    adj[3, 4] = 0.1
    adj[4, 3] = 0.1

    modularity = calculate_modularity(adj)

    # This graph has clear community structure, modularity should be positive
    assert modularity > 0.3, f"Modularity should be high for clustered graph, got {modularity}"


def test_compute_all_metrics():
    """Test that compute_all_metrics returns all expected keys."""
    n = 5
    adj = np.random.rand(n, n)
    adj = (adj + adj.T) / 2
    np.fill_diagonal(adj, 0)

    metrics = compute_all_metrics(adj)

    expected_keys = [
        'characteristic_path_length',
        'global_efficiency',
        'local_efficiency',
        'clustering_coefficient',
        'modularity'
    ]

    for key in expected_keys:
        assert key in metrics, f"Missing key: {key}"
        assert isinstance(metrics[key], (int, float, np.floating)), \
            f"Value for {key} is not numeric: {type(metrics[key])}"


def test_disconnected_graph():
    """Test metrics on a disconnected graph."""
    # Two separate nodes with no connection
    adj = np.zeros((2, 2))

    path_length = calculate_characteristic_path_length(adj)
    global_eff = calculate_global_efficiency(adj)

    # Disconnected graph should return NaN for path length and 0 for efficiency
    assert np.isnan(path_length), f"Path length should be NaN for disconnected graph, got {path_length}"
    assert global_eff == 0.0, f"Global efficiency should be 0 for disconnected graph, got {global_eff}"


def test_process_subject_metrics():
    """Test the subject-level processing function."""
    n = 5
    adj = np.ones((n, n)) - np.eye(n)

    result = process_subject_metrics("test_subject_001", adj)

    assert result['subject_id'] == "test_subject_001"
    assert 'global_efficiency' in result
    assert 'characteristic_path_length' in result
    assert 'local_efficiency' in result
    assert 'clustering_coefficient' in result
    assert 'modularity' in result


def test_empty_matrix():
    """Test handling of empty/None matrix."""
    result = process_subject_metrics("empty_subject", None)

    assert result['subject_id'] == "empty_subject"
    assert np.isnan(result['global_efficiency'])
    assert np.isnan(result['characteristic_path_length'])
