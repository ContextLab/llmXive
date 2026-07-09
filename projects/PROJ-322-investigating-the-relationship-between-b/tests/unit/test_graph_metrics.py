import pytest
import numpy as np
from pathlib import Path
import sys
import os

# Add the code directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from graph_metrics import (
    calculate_global_efficiency,
    calculate_local_efficiency,
    calculate_modularity,
    compute_metrics_from_matrix,
    apply_spatial_threshold
)

@pytest.fixture
def small_connected_graph():
    """Create a small connected graph for testing."""
    # Create a simple 5-node connected graph
    adj = np.array([
        [0, 1, 1, 0, 0],
        [1, 0, 1, 1, 0],
        [1, 1, 0, 1, 1],
        [0, 1, 1, 0, 1],
        [0, 0, 1, 1, 0]
    ], dtype=float)
    return adj

@pytest.fixture
def weighted_connected_graph():
    """Create a weighted connected graph."""
    adj = np.array([
        [0, 0.5, 0.8, 0, 0],
        [0.5, 0, 0.3, 0.9, 0],
        [0.8, 0.3, 0, 0.2, 0.6],
        [0, 0.9, 0.2, 0, 0.7],
        [0, 0, 0.6, 0.7, 0]
    ], dtype=float)
    return adj

def test_global_efficiency_returns_positive_scalar_for_connected_graph(small_connected_graph):
    """Test that global efficiency returns a positive scalar for a connected graph."""
    eff = calculate_global_efficiency(small_connected_graph)
    assert isinstance(eff, float), "Global efficiency should be a float."
    assert eff > 0, "Global efficiency should be positive for a connected graph."
    assert eff <= 1, "Global efficiency should be <= 1 for unweighted graphs (normalized)."

def test_local_efficiency_returns_positive_scalar_for_connected_graph(small_connected_graph):
    """Test that local efficiency returns a positive scalar for a connected graph."""
    eff = calculate_local_efficiency(small_connected_graph)
    assert isinstance(eff, float), "Local efficiency should be a float."
    assert eff > 0, "Local efficiency should be positive for a connected graph."

def test_modularity_returns_value_between_0_and_1(weighted_connected_graph):
    """Test that modularity returns a value between 0 and 1."""
    mod = calculate_modularity(weighted_connected_graph)
    assert isinstance(mod, float), "Modularity should be a float."
    # Modularity can be negative for random graphs, but typically between -0.5 and 1
    # For a structured graph, it should be positive
    assert mod >= -0.5, "Modularity should generally be >= -0.5."
    assert mod <= 1, "Modularity should be <= 1."

def test_apply_spatial_threshold_proportional(weighted_connected_graph):
    """Test proportional thresholding."""
    thresholded = apply_spatial_threshold(weighted_connected_graph, threshold_type='proportional', threshold_value=0.5)
    
    # Check that diagonal is zero
    assert np.all(np.diag(thresholded) == 0), "Diagonal should be zero."
    
    # Check that matrix is symmetric
    assert np.allclose(thresholded, thresholded.T), "Matrix should be symmetric."
    
    # Check that number of edges is approximately correct
    original_edges = np.sum(weighted_connected_graph > 0)
    thresholded_edges = np.sum(thresholded > 0)
    expected_edges = int(original_edges * 0.5)
    assert abs(thresholded_edges - expected_edges) <= 1, f"Expected ~{expected_edges} edges, got {thresholded_edges}"

def test_apply_spatial_threshold_absolute(weighted_connected_graph):
    """Test absolute thresholding."""
    thresholded = apply_spatial_threshold(weighted_connected_graph, threshold_type='absolute', threshold_value=0.4)
    
    # Check that all values are >= 0.4 or 0
    assert np.all((thresholded == 0) | (thresholded >= 0.4)), "All non-zero values should be >= 0.4."
    
    # Check that diagonal is zero
    assert np.all(np.diag(thresholded) == 0), "Diagonal should be zero."

def test_compute_metrics_from_matrix(weighted_connected_graph):
    """Test the full metrics computation pipeline."""
    metrics = compute_metrics_from_matrix(weighted_connected_graph, threshold_type='proportional', threshold_value=0.5)
    
    assert "global_efficiency" in metrics
    assert "local_efficiency" in metrics
    assert "modularity" in metrics
    assert "threshold_type" in metrics
    assert "threshold_value" in metrics
    assert "num_edges" in metrics
    
    assert metrics["global_efficiency"] > 0
    assert metrics["local_efficiency"] > 0
    assert isinstance(metrics["modularity"], float)
    assert metrics["threshold_type"] == "proportional"
    assert metrics["threshold_value"] == 0.5
    assert metrics["num_edges"] > 0

def test_invalid_threshold_value_raises_error(small_connected_graph):
    """Test that invalid threshold values raise errors."""
    with pytest.raises(ValueError):
        apply_spatial_threshold(small_connected_graph, threshold_type='proportional', threshold_value=0.0)
    
    with pytest.raises(ValueError):
        apply_spatial_threshold(small_connected_graph, threshold_type='proportional', threshold_value=1.5)

def test_non_square_matrix_raises_error():
    """Test that non-square matrices raise errors."""
    invalid_matrix = np.array([[1, 2, 3], [4, 5, 6]])
    
    with pytest.raises(ValueError):
        calculate_global_efficiency(invalid_matrix)
    
    with pytest.raises(ValueError):
        calculate_local_efficiency(invalid_matrix)
    
    with pytest.raises(ValueError):
        compute_metrics_from_matrix(invalid_matrix)