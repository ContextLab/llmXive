"""
Unit tests for structural graph metric calculation (T015a).
"""
import numpy as np
import pandas as pd
import networkx as nx
import pytest
from pathlib import Path
import sys

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from preprocess.structural import calculate_graph_metrics, process_subject_structural_metrics

def test_calculate_graph_metrics_basic():
    """Test basic graph metrics calculation."""
    # Create a simple 5x5 adjacency matrix
    # A fully connected graph should have high efficiency and clustering
    n = 5
    adj = np.ones((n, n))
    np.fill_diagonal(adj, 0.0)
    
    metrics = calculate_graph_metrics(adj, density_threshold=1.0)
    
    assert 'global_efficiency' in metrics
    assert 'average_clustering_coefficient' in metrics
    assert 'modularity' in metrics
    assert metrics['global_efficiency'] > 0
    assert metrics['average_clustering_coefficient'] > 0
    assert metrics['num_nodes'] == n

def test_calculate_graph_metrics_sparse():
    """Test metrics on a sparse graph."""
    # Create a ring graph (each node connected to 2 neighbors)
    n = 10
    adj = np.zeros((n, n))
    for i in range(n):
        adj[i, (i+1)%n] = 1.0
        adj[i, (i-1)%n] = 1.0
    
    metrics = calculate_graph_metrics(adj, density_threshold=1.0)
    
    # Ring graph has lower clustering than complete graph
    assert metrics['average_clustering_coefficient'] < 1.0
    assert metrics['num_edges'] == n

def test_density_threshold():
    """Test that density threshold correctly filters edges."""
    # Create a graph with varying edge weights
    n = 10
    adj = np.random.rand(n, n)
    np.fill_diagonal(adj, 0.0)
    adj = (adj + adj.T) / 2.0 # Symmetric
    
    # High threshold should result in fewer edges
    metrics_high = calculate_graph_metrics(adj, density_threshold=0.5)
    metrics_low = calculate_graph_metrics(adj, density_threshold=0.1)
    
    # Higher threshold -> more edges retained (top 50% vs top 10%)
    # Wait: density_threshold=0.5 means keep top 50% of edges.
    # density_threshold=0.1 means keep top 10% of edges.
    # So metrics_high should have MORE edges than metrics_low.
    assert metrics_high['num_edges'] >= metrics_low['num_edges']
    assert metrics_high['actual_density'] >= metrics_low['actual_density']

def test_process_subject_structural_metrics():
    """Test the subject-level processing function."""
    n = 5
    adj = np.ones((n, n))
    np.fill_diagonal(adj, 0.0)
    
    result = process_subject_structural_metrics("sub_001", adj, density_threshold=1.0)
    
    assert result['subject_id'] == "sub_001"
    assert 'global_efficiency' in result
    assert 'modularity' in result

def test_empty_graph_handling():
    """Test behavior with no edges."""
    n = 5
    adj = np.zeros((n, n))
    
    with pytest.raises(ValueError):
        calculate_graph_metrics(adj, density_threshold=0.1)

def test_self_loop_removal():
    """Test that self-loops are removed."""
    n = 5
    adj = np.ones((n, n))
    # Add self loops
    np.fill_diagonal(adj, 1.0)
    
    metrics = calculate_graph_metrics(adj, density_threshold=1.0)
    
    # Self loops should be removed, so they don't count in edge calculation
    # In a complete graph without self-loops, num_edges = n*(n-1)/2
    expected_edges = n * (n - 1) // 2
    assert metrics['num_edges'] == expected_edges
