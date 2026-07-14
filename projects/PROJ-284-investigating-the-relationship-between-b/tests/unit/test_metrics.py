"""
tests/unit/test_metrics.py
--------------------------

Unit tests for graph metric extraction (T021).
"""
import numpy as np
import pytest
from code.data.metrics import extract_graph_metrics, aggregate_node_metrics, calculate_connectivity_matrix


def test_graph_metrics_match_synthetic_ground_truth():
    """
    Test T021: Verify graph metrics on a synthetic matrix with known structure.
    
    We create a block-diagonal matrix representing two distinct communities.
    Expected:
    - Modularity > 0.3 (strong community structure)
    - Global Efficiency > 0
    - Participation Coefficient mean < 0.5 (nodes mostly within modules)
    """
    # Create a 20x20 matrix with two clear communities
    n = 20
    matrix = np.zeros((n, n))
    
    # Community 1: nodes 0-9 (strong internal connections)
    for i in range(10):
        for j in range(10):
            if i != j:
                matrix[i, j] = 0.8
    
    # Community 2: nodes 10-19 (strong internal connections)
    for i in range(10, 20):
        for j in range(10, 20):
            if i != j:
                matrix[i, j] = 0.8
    
    # Weak inter-community connections
    for i in range(10):
        for j in range(10, 20):
            matrix[i, j] = 0.1
            matrix[j, i] = 0.1
    
    np.fill_diagonal(matrix, 1.0)
    
    # Extract metrics
    metrics = extract_graph_metrics(matrix, threshold=0.3)
    
    # Assertions
    assert 'modularity' in metrics
    assert 'global_efficiency' in metrics
    assert 'participation_coef' in metrics
    assert 'within_module_degree' in metrics
    
    # Check scalar values
    assert metrics['modularity'] > 0.3, f"Expected modularity > 0.3, got {metrics['modularity']}"
    assert metrics['global_efficiency'] > 0, f"Expected global_efficiency > 0, got {metrics['global_efficiency']}"
    
    # Check node-level arrays
    assert len(metrics['participation_coef']) == n
    assert len(metrics['within_module_degree']) == n
    
    # Aggregate and check
    agg = aggregate_node_metrics(metrics)
    assert 'participation_coef_mean' in agg
    assert 'within_module_degree_mean' in agg
    
    # For a block-diagonal matrix, PC should be low (nodes connected mostly within module)
    # But not zero because of the weak inter-module links
    assert 0.0 <= agg['participation_coef_mean'] <= 0.5, \
        f"Expected low PC mean for block matrix, got {agg['participation_coef_mean']}"

def test_connectivity_matrix_shape():
    """Test T020: Verify connectivity matrix returns correct shape."""
    # 400 timepoints, 400 regions
    ts = np.random.randn(400, 400)
    cm = calculate_connectivity_matrix(ts)
    assert cm.shape == (400, 400)
    assert np.allclose(np.diag(cm), 1.0)

def test_connectivity_matrix_invalid_shape():
    """Test T020: Verify error on invalid shape."""
    ts = np.random.randn(100, 50) # Wrong number of regions
    with pytest.raises(ValueError):
        calculate_connectivity_matrix(ts)