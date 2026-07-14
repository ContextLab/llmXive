"""
Unit tests for T021: Graph Metric Extractor.
"""
import numpy as np
import pytest
from code.data.metrics import calculate_graph_metrics, calculate_node_level_metrics, aggregate_node_metrics

def test_calculate_graph_metrics_modularity():
    """Test that modularity is calculated correctly on a known community structure."""
    # Create a graph with two clear communities
    # Community 1: nodes 0-4, Community 2: nodes 5-9
    # Strong intra-community edges, weak inter-community edges
    n = 10
    matrix = np.random.rand(n, n) * 0.1 # Weak base
    # Intra-community
    for i in range(5):
        for j in range(5):
            if i != j:
                matrix[i, j] = 0.8
    for i in range(5, 10):
        for j in range(5, 10):
            if i != j:
                matrix[i, j] = 0.8
    
    # Inter-community (weak)
    # Already set by random base

    metrics = calculate_graph_metrics(matrix, threshold=0.5)
    
    assert "modularity" in metrics
    assert "global_efficiency" in metrics
    assert "participation_coef" in metrics
    assert "within_module_degree" in metrics
    
    # Modularity should be positive for this structure
    assert metrics["modularity"] > 0.0

def test_calculate_graph_metrics_random():
    """Test on a random matrix (Erdos-Renyi like)."""
    matrix = np.random.rand(20, 20)
    metrics = calculate_graph_metrics(matrix, threshold=0.5)
    
    assert metrics["modularity"] >= -1.0 # Modularity range
    assert metrics["global_efficiency"] >= 0.0

def test_calculate_node_level_metrics():
    """Test node-level metric calculation."""
    n = 10
    matrix = np.random.rand(n, n)
    # Create communities manually
    communities = [0]*5 + [1]*5
    
    pc, wmd = calculate_node_level_metrics(matrix, communities)
    
    assert len(pc) == n
    assert len(wmd) == n
    assert all(isinstance(x, float) for x in pc)
    assert all(isinstance(x, float) for x in wmd)

def test_aggregate_node_metrics():
    """Test aggregation logic."""
    pc = [0.1, 0.2, 0.3]
    wmd = [1.0, 2.0, 3.0]
    
    result = aggregate_node_metrics(pc, wmd)
    
    assert result["participation_coef"] == 0.2
    assert result["within_module_degree"] == 2.0