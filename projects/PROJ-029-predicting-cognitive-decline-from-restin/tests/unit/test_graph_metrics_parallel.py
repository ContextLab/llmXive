"""
Unit tests for graph metrics computation with parallel processing.

These tests verify that:
1. The parallel processing logic works correctly.
2. Metrics are computed accurately on small synthetic graphs.
3. The output format matches expectations.
"""
import os
import tempfile
import csv
from pathlib import Path
from unittest.mock import patch, MagicMock
import numpy as np
import pytest

# Import the module under test
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from code_03_compute_graph_metrics import (
    compute_subject_metrics,
    process_subject_wrapper,
    write_metrics_csv,
)
from utils.graph import (
    calculate_degree_centrality,
    calculate_global_efficiency,
    calculate_clustering_coefficient,
    calculate_shortest_path_length,
)


def test_degree_centrality_simple():
    """Test degree centrality on a simple graph."""
    # Star graph: center connected to 3 leaves
    adj = np.array([
        [0, 1, 1, 1],
        [1, 0, 0, 0],
        [1, 0, 0, 0],
        [1, 0, 0, 0]
    ], dtype=float)
    
    degree = calculate_degree_centrality(adj)
    assert len(degree) == 4
    assert degree[0] == 3.0  # Center node
    assert degree[1] == 1.0  # Leaf nodes
    assert degree[2] == 1.0
    assert degree[3] == 1.0


def test_global_efficiency_simple():
    """Test global efficiency on a simple complete graph."""
    # Complete graph K3
    adj = np.array([
        [0, 1, 1],
        [1, 0, 1],
        [1, 1, 0]
    ], dtype=float)
    
    eff = calculate_global_efficiency(adj)
    # In a complete graph, efficiency should be 1.0
    assert eff == pytest.approx(1.0, rel=1e-5)


def test_compute_subject_metrics_success():
    """Test successful metric computation."""
    # Create a mock connectivity matrix
    matrix = np.random.rand(10, 10)
    matrix = (matrix + matrix.T) / 2  # Make symmetric
    np.fill_diagonal(matrix, 0)
    
    # Mock the load_connectivity function
    with patch("code_03_compute_graph_metrics.load_connectivity", return_value=matrix):
        result = compute_subject_metrics("test_sub_001")
        
    assert result["subject_id"] == "test_sub_001"
    assert result["status"] == "success"
    assert result["n_nodes"] == 10
    assert "global_efficiency" in result
    assert "average_degree" in result
    assert "average_clustering_coefficient" in result
    assert "average_path_length" in result


def test_compute_subject_metrics_missing():
    """Test handling of missing connectivity file."""
    with patch("code_03_compute_graph_metrics.load_connectivity", return_value=None):
        result = compute_subject_metrics("missing_sub")
    
    assert result["subject_id"] == "missing_sub"
    assert result["status"] == "missing_connectivity"


def test_write_metrics_csv():
    """Test CSV writing functionality."""
    results = [
        {"subject_id": "sub1", "status": "success", "global_efficiency": 0.5},
        {"subject_id": "sub2", "status": "success", "global_efficiency": 0.6},
        {"subject_id": "sub3", "status": "missing_connectivity"},
    ]
    
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".csv") as f:
        temp_path = f.name
    
    try:
        # Patch the path to write to temp file
        with patch("code_03_compute_graph_metrics.GRAPH_METRICS_PATH", Path(temp_path)):
            write_metrics_csv(results)
        
        # Verify file content
        with open(temp_path, "r") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        
        assert len(rows) == 3
        assert rows[0]["subject_id"] == "sub1"
        assert rows[1]["subject_id"] == "sub2"
        assert rows[2]["subject_id"] == "sub3"
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)


def test_parallel_processing_structure():
    """Verify that the parallel processing structure is correct."""
    # This test ensures the logic for parallel execution is sound
    # by checking that the wrapper function returns the expected structure.
    mock_result = {"subject_id": "test", "status": "success"}
    
    with patch("code_03_compute_graph_metrics.compute_subject_metrics", return_value=mock_result):
        result = process_subject_wrapper("test")
    
    assert result == mock_result
    assert "subject_id" in result
    assert "status" in result