"""
Unit tests for graph metrics computation.
"""
import numpy as np
import networkx as nx
import pytest
from pathlib import Path
import tempfile
import json

# Import functions to test
from code.utils.graph import (
    calculate_degree_centrality,
    calculate_global_efficiency,
    calculate_clustering_coefficient,
    calculate_shortest_path_length,
)
from code import compute_subject_metrics, load_connectivity, read_eligible_subjects


def test_calculate_degree_centrality():
    """Test degree centrality calculation on a simple graph."""
    # Create a star graph (center node connected to all others)
    G = nx.star_graph(4)  # 5 nodes total
    degree = calculate_degree_centrality(G)
    # Center node should have highest centrality
    assert len(degree) == 5
    assert max(degree) > 0.5  # Center node


def test_calculate_global_efficiency():
    """Test global efficiency on a complete graph."""
    G = nx.complete_graph(5)
    efficiency = calculate_global_efficiency(G)
    assert efficiency == 1.0  # Complete graph has max efficiency


def test_calculate_clustering_coefficient():
    """Test clustering coefficient on a triangle."""
    G = nx.complete_graph(3)
    clustering = calculate_clustering_coefficient(G)
    assert clustering == 1.0  # Triangle has max clustering


def test_calculate_shortest_path_length():
    """Test shortest path length on a line graph."""
    G = nx.path_graph(5)
    path_len = calculate_shortest_path_length(G)
    # Average shortest path in a line of 5 nodes
    assert path_len > 0
    assert path_len < 5


def test_compute_subject_metrics_with_valid_matrix():
    """Test full metrics computation with a valid adjacency matrix."""
    # Create a simple 5x5 adjacency matrix
    np.random.seed(42)
    adj = np.random.rand(5, 5)
    adj = (adj + adj.T) / 2  # Symmetrize
    np.fill_diagonal(adj, 0)

    metrics = compute_subject_metrics(adj, "test_sub")

    assert "subject_id" in metrics
    assert metrics["subject_id"] == "test_sub"
    assert "degree" in metrics
    assert "global_efficiency" in metrics
    assert "clustering_coefficient" in metrics
    assert "average_path_length" in metrics

    # Values should be numeric (not NaN unless graph is disconnected)
    assert isinstance(metrics["degree"], float)
    assert isinstance(metrics["global_efficiency"], float)


def test_compute_subject_metrics_with_empty_matrix():
    """Test metrics computation with an empty matrix."""
    adj = np.zeros((3, 3))
    metrics = compute_subject_metrics(adj, "empty_sub")

    assert metrics["degree"] != metrics["degree"]  # NaN check
    assert metrics["global_efficiency"] != metrics["global_efficiency"]


def test_load_connectivity_npy(tmp_path):
    """Test loading a .npy connectivity file."""
    conn_dir = tmp_path / "connectivity_matrices"
    conn_dir.mkdir()
    sub_id = "sub001"
    matrix = np.random.rand(10, 10)
    file_path = conn_dir / f"{sub_id}_connectivity.npy"
    np.save(file_path, matrix)

    # Temporarily override CONNECTIVITY_DIR
    import code.compute_graph_metrics as module
    original_dir = module.CONNECTIVITY_DIR
    module.CONNECTIVITY_DIR = conn_dir

    try:
        loaded = load_connectivity(sub_id)
        assert loaded is not None
        assert np.allclose(loaded, matrix)
    finally:
        module.CONNECTIVITY_DIR = original_dir


def test_read_eligible_subjects(tmp_path):
    """Test reading eligible subjects from CSV."""
    csv_file = tmp_path / "eligible_subjects.csv"
    csv_file.write_text("subject_id\nsub001\nsub002\nsub003\n")

    subjects = read_eligible_subjects(csv_file)
    assert len(subjects) == 3
    assert subjects == ["sub001", "sub002", "sub003"]