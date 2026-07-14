"""
tests/unit/test_metrics.py
Unit tests for graph metric extraction.
"""
import numpy as np
import pytest
from code.data.metrics import extract_graph_metrics, aggregate_node_metrics, calculate_connectivity_matrix


def test_graph_metrics_match_synthetic_ground_truth():
    """
    Tests that graph metrics match known ground truth on a synthetic correlation matrix.
    """
    # Create a synthetic correlation matrix with known structure
    # 10 nodes, first 5 highly correlated (community 1), last 5 highly correlated (community 2)
    n_nodes = 10
    corr_matrix = np.zeros((n_nodes, n_nodes))

    # Community 1 (0-4)
    corr_matrix[0:5, 0:5] = 0.8
    # Community 2 (5-9)
    corr_matrix[5:10, 5:10] = 0.8
    # Inter-community (weak)
    corr_matrix[0:5, 5:10] = 0.1
    corr_matrix[5:10, 0:5] = 0.1

    # Set diagonal to 1
    np.fill_diagonal(corr_matrix, 1.0)

    # Calculate metrics
    metrics = calculate_graph_metrics(corr_matrix, threshold=0.3)

    # Check that metrics are reasonable
    assert metrics["modularity"] > 0.3, "Modularity should be high for clear communities"
    assert metrics["global_efficiency"] > 0, "Global efficiency should be positive"
    assert 0 <= metrics["participation_coefficient"] <= 1, "Participation coefficient should be in [0, 1]"
    assert metrics["within_module_degree"] > 0, "Within-module degree should be positive"

    # Specific checks for community structure
    # Nodes in the same community should have higher within-module degree
    # and lower participation coefficient compared to random graphs
    assert metrics["modularity"] > 0.5, "Expected high modularity for this synthetic structure"

def test_connectivity_matrix_calculation():
    """
    Tests that the connectivity matrix is calculated correctly from time series.
    """
    # Create synthetic time series with known correlation
    n_timepoints = 100
    n_nodes = 5

    # Node 0 and 1 should be highly correlated
    ts = np.random.randn(n_nodes, n_timepoints)
    ts[1, :] = ts[0, :] + 0.1 * np.random.randn(n_timepoints)  # Add noise

    corr_matrix = calculate_connectivity_matrix(ts)

    # Check that corr[0,1] is high
    assert corr_matrix[0, 1] > 0.8, "Nodes 0 and 1 should be highly correlated"
    assert corr_matrix[0, 0] == 1.0, "Diagonal should be 1.0"
    assert corr_matrix.shape == (n_nodes, n_nodes), "Matrix shape should match input"

def test_graph_metrics_empty_graph():
    """
    Tests that graph metrics return zeros for an empty graph (no edges).
    """
    corr_matrix = np.zeros((5, 5))
    metrics = calculate_graph_metrics(corr_matrix, threshold=0.9)

    assert metrics["modularity"] == 0.0
    assert metrics["global_efficiency"] == 0.0
    assert metrics["participation_coefficient"] == 0.0
    assert metrics["within_module_degree"] == 0.0
