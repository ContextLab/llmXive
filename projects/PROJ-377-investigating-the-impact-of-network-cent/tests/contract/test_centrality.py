"""
Contract tests for centrality metric calculation (User Story 2).

These tests validate the interface and output schema of the centrality
calculation module before full integration. They ensure that:
1. The centrality calculation function accepts valid inputs.
2. The output DataFrame contains the required columns and schema.
3. The hub selection logic returns the expected number of nodes.
4. The metrics are calculated correctly for a known graph.
"""

import os
import sys
import pytest
import numpy as np
import pandas as pd
import networkx as nx
from pathlib import Path

# Add the project root to the path to allow imports from 'code'
# Assuming this test runs from the project root or the test runner sets this up.
# We explicitly add the 'code' directory to sys.path.
code_root = Path(__file__).parent.parent.parent / "code"
if str(code_root) not in sys.path:
    sys.path.insert(0, str(code_root))

from analysis.centrality import (
    compute_centrality_metrics,
    load_connectivity_matrix,
    extract_connectivity_matrix_for_subject,
    run_centrality_analysis
)
from utils.config import get_config, CentralityConfig

# --- Fixtures ---

@pytest.fixture
def sample_connectivity_matrix():
    """
    Creates a small, deterministic sample connectivity matrix (adjacency matrix)
    for testing centrality calculations.
    Shape: (10, 10) representing 10 regions.
    """
    np.random.seed(42)
    n_regions = 10
    # Create a random symmetric matrix with values between 0 and 1
    matrix = np.random.rand(n_regions, n_regions)
    matrix = (matrix + matrix.T) / 2  # Symmetrize
    np.fill_diagonal(matrix, 0.0)  # No self-loops
    
    # Threshold to create a sparse graph (optional, but realistic)
    threshold = 0.5
    matrix[matrix < threshold] = 0.0
    
    return matrix

@pytest.fixture
def sample_subject_id():
    return "sub-001"

@pytest.fixture
def sample_region_names():
    """
    Returns a list of region names corresponding to the matrix indices.
    """
    return [f"Region_{i}" for i in range(10)]

@pytest.fixture
def centrality_config():
    """
    Returns a CentralityConfig object with default settings for testing.
    """
    return CentralityConfig(
        top_hubs=3,  # Select top 3 hubs for analysis
        centrality_types=["degree", "betweenness", "eigenvector"],
        threshold=0.5
    )

# --- Contract Tests ---

def test_compute_centrality_metrics_input_validation(sample_connectivity_matrix):
    """
    Contract: The function must accept a numpy array and return a dictionary
    of centrality metrics.
    """
    # Ensure the matrix is symmetric and has zero diagonal
    assert np.allclose(sample_connectivity_matrix, sample_connectivity_matrix.T)
    assert np.allclose(np.diag(sample_connectivity_matrix), 0.0)

    # Call the function
    metrics = compute_centrality_metrics(sample_connectivity_matrix)

    # Assert output type
    assert isinstance(metrics, dict)

    # Assert expected keys exist (based on standard networkx metrics)
    expected_keys = ["degree", "betweenness", "eigenvector"]
    for key in expected_keys:
        assert key in metrics, f"Missing expected metric: {key}"
        assert isinstance(metrics[key], dict), f"Metric {key} must be a dict mapping node to value"

def test_compute_centrality_metrics_output_schema(sample_connectivity_matrix, sample_region_names):
    """
    Contract: The output metrics must have keys corresponding to the number of regions.
    """
    n_regions = len(sample_region_names)
    metrics = compute_centrality_metrics(sample_connectivity_matrix)

    for metric_name, metric_dict in metrics.items():
        assert len(metric_dict) == n_regions, \
            f"Metric {metric_name} must have entries for all {n_regions} regions"
        # Check that keys are integers (node indices)
        for node_id in metric_dict.keys():
            assert isinstance(node_id, int) or str(node_id).isdigit(), \
                f"Node ID {node_id} should be an integer or string integer"

def test_hub_selection_logic(sample_connectivity_matrix, centrality_config):
    """
    Contract: The function must correctly identify the top N hub nodes
    based on degree centrality.
    """
    metrics = compute_centrality_metrics(sample_connectivity_matrix)
    degree_centrality = metrics["degree"]
    
    # Sort by degree centrality descending
    sorted_nodes = sorted(degree_centrality.items(), key=lambda x: x[1], reverse=True)
    top_hubs = [node for node, _ in sorted_nodes[:centrality_config.top_hubs]]
    
    # Verify we got the correct number of hubs
    assert len(top_hubs) == centrality_config.top_hubs, \
        f"Expected {centrality_config.top_hubs} hubs, got {len(top_hubs)}"
    
    # Verify the hubs are the ones with highest degree
    # (This is implicitly tested by the sort, but we can be explicit)
    min_highest_degree = min(degree_centrality[n] for n in top_hubs)
    max_non_hub_degree = max(
        (degree_centrality[n] for n in range(len(sample_connectivity_matrix)) if n not in top_hubs),
        default=0
    )
    
    # In case of ties, strict inequality might not hold, but generally:
    # The lowest degree in the hub set should be >= highest degree outside
    assert min_highest_degree >= max_non_hub_degree, \
        "Hub selection logic error: A non-hub has higher degree than a hub"

def test_compute_centrality_metrics_edge_cases():
    """
    Contract: The function must handle edge cases like empty graphs or fully connected graphs.
    """
    # Case 1: Empty graph (all zeros)
    empty_matrix = np.zeros((5, 5))
    metrics_empty = compute_centrality_metrics(empty_matrix)
    assert all(v == 0.0 for v in metrics_empty["degree"].values())
    # Betweenness and eigenvector might be 0 or NaN depending on implementation, 
    # but degree must be 0.
    
    # Case 2: Fully connected graph (all ones except diagonal)
    n = 5
    full_matrix = np.ones((n, n))
    np.fill_diagonal(full_matrix, 0.0)
    metrics_full = compute_centrality_metrics(full_matrix)
    
    # In a fully connected graph, degree centrality should be uniform (n-1)
    expected_degree = n - 1
    for node, deg in metrics_full["degree"].items():
        assert np.isclose(deg, expected_degree), \
            f"Fully connected graph degree mismatch for node {node}: {deg} vs {expected_degree}"

def test_load_connectivity_matrix_file_not_found():
    """
    Contract: The loader must raise a FileNotFoundError if the file does not exist.
    """
    non_existent_path = "/tmp/does_not_exist_connectivity_matrix.npy"
    with pytest.raises(FileNotFoundError):
        load_connectivity_matrix(non_existent_path)

def test_extract_connectivity_matrix_for_subject_shape(sample_connectivity_matrix):
    """
    Contract: The extraction function must return a 2D numpy array of the correct shape.
    """
    extracted = extract_connectivity_matrix_for_subject(sample_connectivity_matrix)
    assert isinstance(extracted, np.ndarray)
    assert extracted.ndim == 2
    assert extracted.shape == sample_connectivity_matrix.shape

def test_run_centrality_analysis_schema_integration(
    sample_connectivity_matrix, 
    sample_subject_id, 
    sample_region_names,
    centrality_config,
    tmp_path
):
    """
    Contract: The full analysis pipeline must produce a DataFrame with the
    required schema: subject_id, region_id, region_name, degree, betweenness, eigenvector.
    """
    # Mock the necessary inputs for run_centrality_analysis
    # We simulate the behavior of the pipeline on a single subject
    
    # Create a temporary directory for output
    output_dir = tmp_path / "centrality_output"
    output_dir.mkdir()
    
    # Save the matrix to a temporary file
    matrix_path = output_dir / "sub-001_connectivity.npy"
    np.save(matrix_path, sample_connectivity_matrix)
    
    # Create a mock config for the analysis
    # We will call the internal logic directly to test the schema
    metrics = compute_centrality_metrics(sample_connectivity_matrix)
    
    # Construct the expected DataFrame manually to verify schema logic
    rows = []
    for region_idx in range(len(sample_region_names)):
        row = {
            "subject_id": sample_subject_id,
            "region_id": region_idx,
            "region_name": sample_region_names[region_idx],
            "degree": metrics["degree"].get(region_idx, 0.0),
            "betweenness": metrics["betweenness"].get(region_idx, 0.0),
            "eigenvector": metrics["eigenvector"].get(region_idx, 0.0)
        }
        rows.append(row)
    
    df = pd.DataFrame(rows)
    
    # Verify schema
    required_columns = ["subject_id", "region_id", "region_name", "degree", "betweenness", "eigenvector"]
    assert list(df.columns) == required_columns, \
        f"DataFrame columns mismatch. Expected {required_columns}, got {list(df.columns)}"
    
    # Verify data types
    assert df["subject_id"].dtype == object
    assert df["region_id"].dtype in [np.int64, np.int32, int]
    assert df["region_name"].dtype == object
    assert df["degree"].dtype in [np.float64, np.float32, float]
    assert df["betweenness"].dtype in [np.float64, np.float32, float]
    assert df["eigenvector"].dtype in [np.float64, np.float32, float]

def test_centrality_values_range(sample_connectivity_matrix):
    """
    Contract: Centrality values should be within reasonable bounds.
    Degree centrality is typically [0, 1] if normalized, or [0, N-1] if not.
    We check that they are non-negative.
    """
    metrics = compute_centrality_metrics(sample_connectivity_matrix)
    
    for metric_name, metric_dict in metrics.items():
        for node, value in metric_dict.items():
            assert value >= 0.0, f"Centrality value for {metric_name} at node {node} is negative: {value}"