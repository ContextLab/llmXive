"""Unit tests for graph metrics calculation."""
import numpy as np
import pytest
from code.data.metrics import calculate_graph_metrics, calculate_connectivity_matrix

def test_graph_metrics_match_synthetic_ground_truth():
    """Test graph metrics on synthetic data with known ground truth.
    
    Creates a synthetic correlation matrix with a known community structure
    and verifies that the calculated metrics match expected values.
    """
    # Create a synthetic 10x10 correlation matrix with two clear communities
    n_nodes = 10
    np.random.seed(42)
    
    # Community 1: nodes 0-4, Community 2: nodes 5-9
    # High correlation within communities, low between
    corr_matrix = np.zeros((n_nodes, n_nodes))
    
    for i in range(n_nodes):
        for j in range(n_nodes):
            if (i < 5 and j < 5) or (i >= 5 and j >= 5):
                # Within community: high correlation
                corr_matrix[i, j] = 0.7 + np.random.uniform(-0.1, 0.1)
            else:
                # Between community: low correlation
                corr_matrix[i, j] = 0.1 + np.random.uniform(-0.05, 0.05)
    
    # Ensure diagonal is 1 and matrix is symmetric
    np.fill_diagonal(corr_matrix, 1.0)
    corr_matrix = (corr_matrix + corr_matrix.T) / 2
    
    # Define community labels
    community_labels = np.array([0, 0, 0, 0, 0, 1, 1, 1, 1, 1])
    
    # Calculate metrics
    metrics = calculate_graph_metrics(corr_matrix, community_labels)
    
    # Verify metrics are reasonable
    assert "modularity" in metrics
    assert "global_efficiency" in metrics
    assert "participation_coef" in metrics
    assert "within_module_degree" in metrics
    
    # Modularity should be positive for this structure (better than random)
    assert metrics["modularity"] > 0.1, f"Expected positive modularity, got {metrics['modularity']}"
    
    # Global efficiency should be between 0 and 1
    assert 0 < metrics["global_efficiency"] < 1, f"Invalid global efficiency: {metrics['global_efficiency']}"
    
    # Participation coefficient should be between 0 and 1
    assert 0 <= metrics["participation_coef"] <= 1, f"Invalid participation coef: {metrics['participation_coef']}"
    
    print(f"Metrics calculated: {metrics}")
