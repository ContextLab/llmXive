"""Unit tests for graph metric calculation functions."""
import pytest
import numpy as np
import networkx as nx
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.graph import create_graph_from_adjacency, calculate_global_efficiency, calculate_clustering_coefficient, calculate_degree_centrality
from code_03_compute_graph_metrics import compute_subject_metrics


def test_create_graph_from_adjacency():
    """Test graph creation from adjacency matrix."""
    adj = np.array([
        [0, 1, 1, 0],
        [1, 0, 1, 1],
        [1, 1, 0, 0],
        [0, 1, 0, 0]
    ])
    G = create_graph_from_adjacency(adj)
    assert G.number_of_nodes() == 4
    assert G.number_of_edges() == 5


def test_calculate_degree_centrality():
    """Test degree centrality calculation."""
    adj = np.array([
        [0, 1, 1, 0],
        [1, 0, 1, 1],
        [1, 1, 0, 0],
        [0, 1, 0, 0]
    ])
    G = create_graph_from_adjacency(adj)
    degree = calculate_degree_centrality(G)
    assert len(degree) == 4
    # Node 1 (index 1) has degree 3, normalized should be 3/3 = 1.0
    assert degree[1] == 1.0


def test_calculate_global_efficiency():
    """Test global efficiency calculation."""
    # Complete graph should have efficiency 1.0
    adj = np.ones((4, 4)) - np.eye(4)
    G = create_graph_from_adjacency(adj)
    eff = calculate_global_efficiency(G)
    assert np.isclose(eff, 1.0)


def test_calculate_clustering_coefficient():
    """Test clustering coefficient calculation."""
    # Triangle graph: all nodes have clustering 1.0
    adj = np.array([
        [0, 1, 1],
        [1, 0, 1],
        [1, 1, 0]
    ])
    G = create_graph_from_adjacency(adj)
    clustering = calculate_clustering_coefficient(G)
    # Average clustering should be 1.0
    assert np.isclose(np.mean(list(clustering.values())), 1.0)


def test_compute_subject_metrics_with_realistic_matrix():
    """Test metric computation with a realistic connectivity matrix."""
    # Create a random correlation-like matrix
    np.random.seed(42)
    n_regions = 90  # AAL atlas size
    matrix = np.random.randn(n_regions, 100)
    corr_matrix = np.corrcoef(matrix)
    corr_matrix = np.nan_to_num(corr_matrix, nan=0.0)
    
    metrics = compute_subject_metrics(corr_matrix)
    
    assert "degree" in metrics
    assert "global_efficiency" in metrics
    assert "clustering_coefficient" in metrics
    assert "path_length" in metrics
    
    # Values should be reasonable
    assert 0 <= metrics["degree"] <= n_regions - 1
    assert 0 <= metrics["global_efficiency"] <= 1.0
    assert 0 <= metrics["clustering_coefficient"] <= 1.0
    assert metrics["path_length"] >= 0


def test_compute_subject_metrics_with_none():
    """Test that None input returns zeros."""
    metrics = compute_subject_metrics(None)
    assert metrics["degree"] == 0.0
    assert metrics["global_efficiency"] == 0.0
    assert metrics["clustering_coefficient"] == 0.0
    assert metrics["path_length"] == 0.0


def test_empty_graph_metrics():
    """Test metrics computation on empty graph."""
    adj = np.zeros((5, 5))
    metrics = compute_subject_metrics(adj)
    assert metrics["degree"] == 0.0
    assert metrics["global_efficiency"] == 0.0
    assert metrics["clustering_coefficient"] == 0.0
    assert metrics["path_length"] == 0.0
