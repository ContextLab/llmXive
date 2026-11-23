import os
import json
import tempfile
from pathlib import Path
import pytest
import numpy as np

from src.analysis.graph_metrics import (
    validate_connectivity_matrix,
    calculate_global_efficiency,
    calculate_modularity,
    calculate_participation_coefficient,
    calculate_network_specific_efficiencies,
    extract_edge_strengths,
    compute_all_metrics,
    save_metrics_to_json
)

# Fixtures for test data
@pytest.fixture
def valid_matrix():
    """Create a valid 5x5 correlation matrix."""
    n = 5
    matrix = np.random.rand(n, n)
    matrix = (matrix + matrix.T) / 2
    np.fill_diagonal(matrix, 1.0)
    # Ensure values are in [-1, 1]
    matrix = np.clip(matrix, -1, 1)
    return matrix

@pytest.fixture
def network_labels():
    """Create network labels for 5 nodes."""
    # 0: DMN, 1: Salience, 2: Visual, 3: DMN, 4: Visual
    return np.array([0, 1, 2, 0, 2])

@pytest.fixture
def network_names():
    """List of network names to test."""
    return ["DMN", "Salience", "Visual"]

def test_validate_connectivity_matrix_valid(valid_matrix):
    assert validate_connectivity_matrix(valid_matrix) is True

def test_validate_connectivity_matrix_asymmetric():
    matrix = np.array([[1.0, 0.5], [0.6, 1.0]])
    assert validate_connectivity_matrix(matrix) is False

def test_validate_connectivity_matrix_wrong_shape():
    matrix = np.array([[1.0, 0.5, 0.3], [0.5, 1.0, 0.4]])
    assert validate_connectivity_matrix(matrix) is False

def test_validate_connectivity_matrix_out_of_range():
    matrix = np.array([[1.0, 1.5], [1.5, 1.0]])
    assert validate_connectivity_matrix(matrix) is False

def test_calculate_global_efficiency(valid_matrix):
    eff = calculate_global_efficiency(valid_matrix)
    assert isinstance(eff, float)
    assert eff >= 0

def test_calculate_modularity(valid_matrix):
    q = calculate_modularity(valid_matrix)
    assert isinstance(q, float)
    # Modularity is typically between -0.5 and 1, but can be outside.
    # We just check it's a float.

def test_calculate_participation_coefficient(valid_matrix, network_labels):
    # Shift labels to 1-indexed for BCT
    communities = network_labels + 1
    p = calculate_participation_coefficient(valid_matrix, communities)
    assert isinstance(p, float)
    assert 0 <= p <= 1

def test_calculate_network_specific_efficiencies(valid_matrix, network_labels, network_names):
    efficiencies = calculate_network_specific_efficiencies(valid_matrix, network_labels, network_names)
    assert isinstance(efficiencies, dict)
    for name in network_names:
        if name in ["DMN", "Salience", "Visual"]:  # Assuming these are in the mapping
            # Check that the efficiency is a float and non-negative
            if name in efficiencies:
                assert isinstance(efficiencies[name], float)
                assert efficiencies[name] >= 0

def test_extract_edge_strengths(valid_matrix):
    result = extract_edge_strengths(valid_matrix)
    assert "edges" in result
    assert len(result["edges"]) == valid_matrix.shape[0] * (valid_matrix.shape[0] - 1) // 2
    for edge in result["edges"]:
        assert "node1" in edge
        assert "node2" in edge
        assert "strength" in edge
        assert edge["strength"] == valid_matrix[edge["node1"], edge["node2"]]

def test_compute_all_metrics(valid_matrix, network_labels, network_names):
    metrics = compute_all_metrics(valid_matrix, network_labels, network_names)
    assert "global_efficiency" in metrics
    assert "modularity" in metrics
    assert "participation_coefficient" in metrics
    assert "network_efficiency" in metrics
    assert "edge_strength" in metrics

def test_save_metrics_to_json(valid_matrix, network_labels, network_names):
    metrics = compute_all_metrics(valid_matrix, network_labels, network_names)
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "metrics.json"
        save_metrics_to_json(metrics, output_path)
        assert output_path.exists()
        with open(output_path, 'r') as f:
            loaded_metrics = json.load(f)
        assert loaded_metrics == metrics