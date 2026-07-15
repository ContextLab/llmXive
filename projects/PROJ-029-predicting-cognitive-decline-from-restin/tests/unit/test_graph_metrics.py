"""
Unit tests for graph metric calculation (T019).
"""
import numpy as np
import networkx as nx
import pytest
from pathlib import Path
import sys
import os

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from utils.graph import (
    calculate_degree_centrality,
    calculate_global_efficiency,
    calculate_clustering_coefficient,
    calculate_shortest_path_length
)
from code_03_compute_graph_metrics import compute_subject_metrics

def test_compute_subject_metrics_basic():
    """Test basic metric calculation on a simple graph."""
    # Create a simple 4-node fully connected graph (K4)
    matrix = np.ones((4, 4)) - np.eye(4)
    
    metrics = compute_subject_metrics(matrix, "test_sub")
    
    assert metrics["subject_id"] == "test_sub"
    assert metrics["num_nodes"] == 4
    assert metrics["num_edges"] == 6  # 4*3/2
    assert metrics["degree"] == 3.0  # Each node has degree 3
    assert metrics["global_efficiency"] > 0
    assert metrics["clustering_coefficient"] > 0
    assert metrics["avg_path_length"] == 1.0  # Direct connection between all

def test_compute_subject_metrics_disconnected():
    """Test metrics on a disconnected graph."""
    # Create two disconnected triangles
    matrix = np.zeros((6, 6))
    # Triangle 1: nodes 0,1,2
    matrix[0, 1] = matrix[1, 0] = 1
    matrix[1, 2] = matrix[2, 1] = 1
    matrix[2, 0] = matrix[0, 2] = 1
    # Triangle 2: nodes 3,4,5
    matrix[3, 4] = matrix[4, 3] = 1
    matrix[4, 5] = matrix[5, 4] = 1
    matrix[5, 3] = matrix[3, 5] = 1
    
    metrics = compute_subject_metrics(matrix, "disconnected_sub")
    
    assert metrics["num_nodes"] == 6
    assert metrics["num_edges"] == 6
    # Degree should be 2 for all nodes
    assert metrics["degree"] == 2.0
    # Global efficiency should be positive but less than connected
    assert metrics["global_efficiency"] > 0
    # Clustering should be 1.0 for triangles
    assert abs(metrics["clustering_coefficient"] - 1.0) < 1e-6
    # Avg path length should be calculated on largest component
    assert metrics["avg_path_length"] > 0

def test_compute_subject_metrics_empty():
    """Test metrics on an empty graph."""
    matrix = np.zeros((3, 3))
    metrics = compute_subject_metrics(matrix, "empty_sub")
    
    assert metrics["num_nodes"] == 3
    assert metrics["num_edges"] == 0
    assert metrics["degree"] == 0.0
    # Global efficiency of empty graph is 0
    assert metrics["global_efficiency"] == 0.0
    assert metrics["clustering_coefficient"] == 0.0
    # Path length might be NaN for empty graph
    assert np.isnan(metrics["avg_path_length"]) or metrics["avg_path_length"] == 0

def test_compute_subject_metrics_symmetrization():
    """Test that asymmetric matrices are symmetrized."""
    # Create asymmetric matrix
    matrix = np.array([
        [0, 1, 0],
        [0, 0, 1],
        [1, 0, 0]
    ], dtype=float)
    
    metrics = compute_subject_metrics(matrix, "asym_sub")
    
    # Should be processed without error
    assert metrics["num_nodes"] == 3

def test_compute_subject_metrics_float_weights():
    """Test metrics on weighted graph."""
    # Create weighted graph
    matrix = np.array([
        [0, 0.5, 0.8],
        [0.5, 0, 0.3],
        [0.8, 0.3, 0]
    ], dtype=float)
    
    metrics = compute_subject_metrics(matrix, "weighted_sub")
    
    assert metrics["num_nodes"] == 3
    assert metrics["num_edges"] == 3
    assert metrics["degree"] > 0
    assert metrics["global_efficiency"] > 0