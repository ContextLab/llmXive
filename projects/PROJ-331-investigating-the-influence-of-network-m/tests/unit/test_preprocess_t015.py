import os
import json
import numpy as np
import pytest
from preprocess import compute_rsfc, compute_global_efficiency

def test_compute_rsfc():
    """Test rsFC computation with known data."""
    # Create a simple time series: 2 regions, 10 time points
    # Region 1: [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
    # Region 2: [2, 4, 6, 8, 10, 12, 14, 16, 18, 20] (perfect correlation)
    ts = np.array([
        [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
        [2, 4, 6, 8, 10, 12, 14, 16, 18, 20]
    ]).T # Shape (10, 2)
    
    corr = compute_rsfc(ts)
    assert corr.shape == (2, 2)
    assert np.isclose(corr[0, 1], 1.0)
    assert np.isclose(corr[1, 0], 1.0)
    assert np.allclose(np.diag(corr), 1.0)

def test_compute_global_efficiency():
    """Test global efficiency computation."""
    # Create a simple weighted adjacency matrix
    # 3x3 matrix
    adj = np.array([
        [0, 1, 1],
        [1, 0, 1],
        [1, 1, 0]
    ], dtype=float)
    
    eff = compute_global_efficiency(adj)
    assert eff > 0.0
    assert isinstance(eff, float)

def test_compute_global_efficiency_zero_weight():
    """Test global efficiency with zero weights."""
    adj = np.array([
        [0, 0, 1],
        [0, 0, 0],
        [1, 0, 0]
    ], dtype=float)
    
    eff = compute_global_efficiency(adj)
    # Should handle disconnected components or zero weights gracefully
    assert eff >= 0.0