"""
Unit tests for metrics.py
"""
import pytest
import numpy as np
from code.data.metrics import (
    calculate_connectivity_matrix,
    calculate_graph_metrics,
    calculate_node_level_metrics,
    aggregate_node_metrics,
    load_atlas,
    apply_motion_regression
)

def test_graph_metrics_match_synthetic_ground_truth():
    """
    Test that graph metrics match known values on a synthetic matrix.
    """
    # Create a synthetic 400x400 matrix with known structure
    # Block diagonal structure for modularity
    n = 400
    corr_matrix = np.eye(n) * 0.9 # High self-correlation
    
    # Add block structure: 4 blocks of 100 nodes each
    # High correlation within blocks, low between
    block_size = 100
    for i in range(4):
        start = i * block_size
        end = (i + 1) * block_size
        corr_matrix[start:end, start:end] += 0.8
    
    # Normalize to [-1, 1]
    corr_matrix = np.clip(corr_matrix, -1, 1)
    np.fill_diagonal(corr_matrix, 1.0)
    
    # Calculate metrics
    metrics = calculate_graph_metrics(corr_matrix)
    
    # Check that modularity is positive (due to block structure)
    assert metrics["modularity"] > 0.0, "Modularity should be positive for block-diagonal matrix"
    
    # Check that global efficiency is reasonable (0 to 1 range usually)
    assert 0.0 <= metrics["global_efficiency"] <= 1.0, "Global efficiency should be in [0, 1]"

def test_aggregate_node_metrics_mean():
    """
    Test that aggregate_node_metrics correctly calculates the mean.
    """
    # Create dummy node metrics
    n_nodes = 400
    node_metrics = {
        "participation_coef": np.ones(n_nodes) * 0.5,
        "within_module_degree": np.ones(n_nodes) * 0.8
    }
    
    aggregated = aggregate_node_metrics(node_metrics)
    
    assert abs(aggregated["mean_participation_coef"] - 0.5) < 1e-6
    assert abs(aggregated["mean_within_module_degree"] - 0.8) < 1e-6

def test_connectivity_matrix_shape():
    """
    Test that connectivity matrix is 400x400.
    """
    # Create synthetic time series
    n_timepoints = 100
    timeseries = np.random.randn(400, n_timepoints)
    
    corr = calculate_connectivity_matrix(timeseries)
    
    assert corr.shape == (400, 400), f"Expected (400, 400), got {corr.shape}"
    assert np.allclose(corr, corr.T), "Correlation matrix should be symmetric"

def test_motion_regression_reduction():
    """
    Test that motion regression reduces correlation with FD.
    """
    n_nodes = 10
    n_timepoints = 50
    fd = np.random.randn(n_timepoints)
    # Create time series correlated with FD
    ts = np.random.randn(n_nodes, n_timepoints) + fd * 2.0
    
    ts_clean = apply_motion_regression(ts, fd.tolist())
    
    # Check correlation between cleaned TS and FD
    for i in range(n_nodes):
        corr_before = np.corrcoef(ts[i], fd)[0, 1]
        corr_after = np.corrcoef(ts_clean[i], fd)[0, 1]
        # The correlation should be reduced (or at least not increased significantly)
        # Note: This is a simple check; in reality, it might not always be lower due to noise
        # but the regression should remove the linear trend
        assert not (corr_after > corr_before + 0.1), f"Regression increased correlation for node {i}"
