"""
Unit tests for code/analysis/network.py
"""
import pytest
import numpy as np
import math
from code.analysis.network import calculate_network_metrics

def test_network_metrics_bounds():
    """Test that modularity Q is non-negative and efficiency values are finite"""
    # Create a simple adjacency matrix (symmetric, binary)
    adj_matrix = np.array([
        [0, 1, 1, 0],
        [1, 0, 1, 1],
        [1, 1, 0, 1],
        [0, 1, 1, 0]
    ], dtype=float)
    
    metrics = calculate_network_metrics(adj_matrix)
    
    # Check modularity Q is non-negative
    assert metrics['modularity_q'] >= 0, f"Modularity Q should be non-negative, got {metrics['modularity_q']}"
    
    # Check efficiency values are finite
    assert np.isfinite(metrics['global_efficiency']), "Global efficiency should be finite"
    assert np.isfinite(metrics['local_efficiency']), "Local efficiency should be finite"
    
    # Check efficiency values are non-negative
    assert metrics['global_efficiency'] >= 0, f"Global efficiency should be non-negative, got {metrics['global_efficiency']}"
    assert metrics['local_efficiency'] >= 0, f"Local efficiency should be non-negative, got {metrics['local_efficiency']}"

def test_network_metrics_nan_handling():
    """Test that NaN/Infinity in adjacency matrix are handled"""
    # Create adjacency matrix with NaN values
    adj_matrix = np.array([
        [0, 1, np.nan, 0],
        [1, 0, 1, 1],
        [np.nan, 1, 0, 1],
        [0, 1, 1, 0]
    ], dtype=float)
    
    # Should not raise an exception, but handle gracefully
    metrics = calculate_network_metrics(adj_matrix)
    
    # Check that metrics are still computed (might be NaN if graph is disconnected)
    assert isinstance(metrics['modularity_q'], (int, float))
