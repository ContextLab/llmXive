"""
Unit tests for graph metrics calculation.
"""
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


@pytest.fixture
def valid_matrix():
    """Create a valid symmetric connectivity matrix."""
    n = 10
    matrix = np.random.rand(n, n)
    matrix = (matrix + matrix.T) / 2  # Make symmetric
    np.fill_diagonal(matrix, 1.0)  # Set diagonal to 1
    # Ensure values are in [-1, 1]
    matrix = np.clip(matrix, -1, 1)
    return matrix


@pytest.fixture
def network_labels():
    """Create network labels for 10 nodes."""
    return np.array([0, 0, 1, 1, 2, 2, 3, 3, 4, 4])


@pytest.fixture
def network_names():
    """Create network names."""
    return ["DMN", "Salience", "Visual", "Motor", "Frontal"]


def test_validate_connectivity_matrix_valid(valid_matrix):
    """Test validation of a valid matrix."""
    result = validate_connectivity_matrix(valid_matrix)
    assert result is True


def test_validate_connectivity_matrix_asymmetric():
    """Test validation fails for asymmetric matrix."""
    matrix = np.random.rand(5, 5)
    with pytest.raises(ValueError, match="not symmetric"):
        validate_connectivity_matrix(matrix)


def test_validate_connectivity_matrix_wrong_shape():
    """Test validation fails for non-square matrix."""
    matrix = np.random.rand(3, 4)
    with pytest.raises(ValueError, match="must be square"):
        validate_connectivity_matrix(matrix)


def test_validate_connectivity_matrix_out_of_range():
    """Test validation fails for values outside [-1, 1]."""
    matrix = np.eye(5)
    matrix[0, 1] = 1.5
    matrix[1, 0] = 1.5
    with pytest.raises(ValueError, match="must be in range"):
        validate_connectivity_matrix(matrix)


def test_calculate_global_efficiency(valid_matrix):
    """Test global efficiency calculation."""
    eff = calculate_global_efficiency(valid_matrix)
    assert isinstance(eff, float)
    assert eff >= 0


def test_calculate_modularity(valid_matrix):
    """Test modularity calculation."""
    modularity, communities = calculate_modularity(valid_matrix)
    assert isinstance(modularity, float)
    assert isinstance(communities, list)
    assert len(communities) == valid_matrix.shape[0]
    assert all(isinstance(c, int) for c in communities)


def test_calculate_participation_coefficient(valid_matrix, network_labels):
    """Test participation coefficient calculation."""
    # First get communities from modularity
    _, communities = calculate_modularity(valid_matrix)
    pc = calculate_participation_coefficient(valid_matrix, communities)
    assert isinstance(pc, np.ndarray)
    assert pc.shape == (valid_matrix.shape[0],)
    assert all(0 <= p <= 1 for p in pc)


def test_calculate_network_specific_efficiencies(valid_matrix, network_labels, network_names):
    """Test network-specific efficiency calculation."""
    efficiencies = calculate_network_specific_efficiencies(
        valid_matrix, network_labels, network_names
    )
    assert isinstance(efficiencies, dict)
    assert set(efficiencies.keys()) == set(network_names)
    assert all(isinstance(v, float) for v in efficiencies.values())


def test_extract_edge_strengths(valid_matrix):
    """Test edge strength extraction."""
    edge_data = extract_edge_strengths(valid_matrix)
    assert "n_nodes" in edge_data
    assert "n_edges" in edge_data
    assert "edges" in edge_data
    assert edge_data["n_nodes"] == valid_matrix.shape[0]
    expected_edges = valid_matrix.shape[0] * (valid_matrix.shape[0] + 1) // 2
    assert edge_data["n_edges"] == expected_edges
    assert len(edge_data["edges"]) == expected_edges


def test_compute_all_metrics(valid_matrix, network_labels, network_names):
    """Test full metrics computation."""
    metrics = compute_all_metrics(valid_matrix, network_labels, network_names)
    
    assert "global_efficiency" in metrics
    assert "modularity" in metrics
    assert "community_assignments" in metrics
    assert "participation_coefficient" in metrics
    assert "network_efficiency" in metrics
    assert "edge_strength" in metrics


def test_save_metrics_to_json(valid_matrix):
    """Test saving metrics to JSON."""
    metrics = compute_all_metrics(valid_matrix)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "test_metrics.json"
        save_metrics_to_json(metrics, output_path)
        
        assert output_path.exists()
        
        with open(output_path, 'r') as f:
            loaded = json.load(f)
        
        assert loaded["global_efficiency"] == metrics["global_efficiency"]
        assert loaded["modularity"] == metrics["modularity"]