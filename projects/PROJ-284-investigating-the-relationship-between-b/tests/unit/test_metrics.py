"""
Unit tests for metrics.py
"""
import numpy as np
import networkx as nx
from code.data.metrics import calculate_connectivity_matrix, calculate_graph_metrics

def test_graph_metrics_match_synthetic_ground_truth():
    """
    Test that graph metrics match known values for a synthetic graph.
    """
    # Create a simple synthetic correlation matrix
    # Two fully connected modules with weak inter-module connections
    n = 10
    conn = np.zeros((n, n))
    
    # Module 1: nodes 0-4
    # Module 2: nodes 5-9
    for i in range(5):
        for j in range(5):
            if i != j:
                conn[i, j] = 0.9
    for i in range(5, 10):
        for j in range(5, 10):
            if i != j:
                conn[i, j] = 0.9
    
    # Inter-module connections
    for i in range(5):
        for j in range(5, 10):
            conn[i, j] = 0.1
            conn[j, i] = 0.1
    
    np.fill_diagonal(conn, 1.0)
    
    # Calculate metrics
    metrics = calculate_graph_metrics(conn)
    
    # Assertions
    # Modularity should be high (close to 1 for perfect separation)
    assert 0.5 < metrics["modularity"] < 1.0, f"Modularity {metrics['modularity']} out of expected range"
    
    # Global efficiency should be positive
    assert metrics["global_efficiency"] > 0, "Global efficiency should be positive"
    
    # Participation coefficient should be low (nodes mostly connected within module)
    # But not exactly 0 because of inter-module links
    assert 0.0 <= metrics["participation_coef"] < 0.5, f"PC {metrics['participation_coef']} out of expected range"
    
    # Within-module degree should be positive (nodes well connected within module)
    assert metrics["within_module_degree"] > -1.0, "WMD should be reasonable"
    
    print("Test passed: Graph metrics match synthetic ground truth.")
