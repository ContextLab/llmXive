"""
Integration test for metric calculation (US2).

This test verifies that the system can process a single subject's connectivity
matrix and output a JSON object containing the required network metrics keys,
which can be successfully joined with a mock behavioral score.

Prerequisites:
- T013 must have produced a valid connectivity matrix in data/connectivity/
- T018a/b/c (graph_metrics.py) must be implemented to calculate metrics

This test is marked as [P] (parallel) because it only depends on completed
foundational tasks and does not block other user stories.
"""
import os
import json
import tempfile
from pathlib import Path
import pytest
import numpy as np
from typing import Dict, Any

# Import the metrics calculation function from the analysis module
# This import will fail if T018a/b/c is not implemented
try:
    from src.analysis.graph_metrics import calculate_network_metrics
except ImportError:
    pytest.skip("graph_metrics.py not implemented yet (T018a/b/c)", allow_module_level=True)


@pytest.fixture
def temp_metrics_dir():
    """Create a temporary directory for test outputs."""
    with tempfile.TemporaryDirectory() as tmpdir:
        data_dir = Path(tmpdir) / "data"
        connectivity_dir = data_dir / "connectivity"
        metrics_dir = data_dir / "metrics"
        connectivity_dir.mkdir(parents=True)
        metrics_dir.mkdir(parents=True)
        yield {
            "data_dir": data_dir,
            "connectivity_dir": connectivity_dir,
            "metrics_dir": metrics_dir
        }


@pytest.fixture
def mock_connectivity_matrix(temp_metrics_dir):
    """
    Create a realistic mock connectivity matrix for a single subject.
    
    In a real integration test, this would load an actual matrix from T013's output.
    For this test, we create a valid symmetric matrix with values in [-1, 1] and
    diagonal = 1.0, matching the schema validated by T013.
    """
    n_regions = 200  # Schaefer 200-parcel atlas
    matrix = np.random.rand(n_regions, n_regions)
    matrix = (matrix + matrix.T) / 2  # Make symmetric
    np.fill_diagonal(matrix, 1.0)  # Diagonal = 1.0
    
    # Ensure values are in [-1, 1]
    matrix = np.clip(matrix, -1.0, 1.0)
    
    # Save as JSON (matching T013's output format)
    matrix_path = temp_metrics_dir["connectivity_dir"] / "sub-001_connectivity.json"
    with open(matrix_path, "w") as f:
        json.dump(matrix.tolist(), f)
    
    return matrix_path


@pytest.fixture
def mock_behavioral_score():
    """
    Create a mock behavioral score for testing the merge operation.
    
    In a real scenario, this would come from the BMRQ data downloaded by T011.
    """
    return {
        "subject_id": "sub-001",
        "bmrq_total": 42.5,
        "bmrq_subscale_1": 12.3,
        "bmrq_subscale_2": 15.7,
        "bmrq_subscale_3": 14.5
    }


def test_metric_calculation_outputs_required_keys(
    mock_connectivity_matrix,
    mock_behavioral_score,
    temp_metrics_dir
):
    """
    Test that metric calculation produces a JSON object with all required keys.
    
    Required keys per US2 specification:
    - global_efficiency
    - modularity
    - participation_coefficient
    - network_efficiency
    - edge_strength
    """
    # Run the metric calculation
    result = calculate_network_metrics(
        connectivity_path=str(mock_connectivity_matrix),
        output_dir=str(temp_metrics_dir["metrics_dir"]),
        subject_id="sub-001"
    )
    
    # Verify the result is a dictionary
    assert isinstance(result, dict), "Metric calculation should return a dict"
    
    # Check for required keys
    required_keys = [
        "global_efficiency",
        "modularity",
        "participation_coefficient",
        "network_efficiency",
        "edge_strength"
    ]
    
    for key in required_keys:
        assert key in result, f"Missing required key: {key}"
    
    # Verify data types and reasonable ranges
    assert isinstance(result["global_efficiency"], (int, float))
    assert 0 <= result["global_efficiency"] <= 1, "Global efficiency should be in [0, 1]"
    
    assert isinstance(result["modularity"], (int, float))
    assert 0 <= result["modularity"] <= 1, "Modularity should be in [0, 1]"
    
    assert isinstance(result["participation_coefficient"], (int, float))
    assert 0 <= result["participation_coefficient"] <= 1, "Participation coefficient should be in [0, 1]"
    
    assert isinstance(result["network_efficiency"], dict), "Network efficiency should be a dict"
    # Check that network efficiency contains expected networks
    expected_networks = ["DMN", "Salience", "Visual"]
    for network in expected_networks:
        assert network in result["network_efficiency"], f"Missing network: {network}"
        assert isinstance(result["network_efficiency"][network], (int, float))
    
    assert isinstance(result["edge_strength"], list), "Edge strength should be a list"
    assert len(result["edge_strength"]) > 0, "Edge strength list should not be empty"
    
    # Verify each edge strength entry has required fields
    for edge in result["edge_strength"]:
        assert "source" in edge, "Edge missing 'source' field"
        assert "target" in edge, "Edge missing 'target' field"
        assert "strength" in edge, "Edge missing 'strength' field"
        assert isinstance(edge["strength"], (int, float))
        assert -1 <= edge["strength"] <= 1, "Edge strength should be in [-1, 1]"


def test_metrics_can_be_joined_with_behavioral_score(
    mock_connectivity_matrix,
    mock_behavioral_score,
    temp_metrics_dir
):
    """
    Test that calculated metrics can be successfully joined with behavioral scores.
    
    This simulates the data merging operation in T021.
    """
    # Calculate metrics
    metrics = calculate_network_metrics(
        connectivity_path=str(mock_connectivity_matrix),
        output_dir=str(temp_metrics_dir["metrics_dir"]),
        subject_id="sub-001"
    )
    
    # Simulate the merge operation (as would be done in T021)
    merged_data = {
        **mock_behavioral_score,
        **metrics
    }
    
    # Verify the merged data contains all expected fields
    assert merged_data["subject_id"] == "sub-001"
    assert merged_data["bmrq_total"] == 42.5
    assert "global_efficiency" in merged_data
    assert "modularity" in merged_data
    assert "participation_coefficient" in merged_data
    assert "network_efficiency" in merged_data
    assert "edge_strength" in merged_data
    
    # Verify we can save the merged data as JSON
    merged_path = temp_metrics_dir["metrics_dir"] / "sub-001_merged.json"
    with open(merged_path, "w") as f:
        json.dump(merged_data, f, indent=2)
    
    assert merged_path.exists(), "Merged data file should be created"
    
    # Verify we can reload and access all fields
    with open(merged_path, "r") as f:
        reloaded = json.load(f)
    
    assert reloaded["subject_id"] == "sub-001"
    assert reloaded["global_efficiency"] == metrics["global_efficiency"]
    assert reloaded["bmrq_total"] == mock_behavioral_score["bmrq_total"]


def test_metric_calculation_handles_single_subject_correctly(
    mock_connectivity_matrix,
    temp_metrics_dir
):
    """
    Test that the metric calculation works correctly for a single subject.
    
    This validates the "N=1" requirement for independent testing.
    """
    result = calculate_network_metrics(
        connectivity_path=str(mock_connectivity_matrix),
        output_dir=str(temp_metrics_dir["metrics_dir"]),
        subject_id="sub-001"
    )
    
    # Verify the output file was created
    output_path = temp_metrics_dir["metrics_dir"] / "sub-001_metrics.json"
    assert output_path.exists(), "Metrics output file should be created"
    
    # Verify the file contains valid JSON
    with open(output_path, "r") as f:
        saved_metrics = json.load(f)
    
    assert saved_metrics == result, "Saved metrics should match returned metrics"
    
    # Verify the metrics are consistent (same values on repeated calculation)
    result2 = calculate_network_metrics(
        connectivity_path=str(mock_connectivity_matrix),
        output_dir=str(temp_metrics_dir["metrics_dir"]),
        subject_id="sub-001"
    )
    
    assert result == result2, "Metrics should be deterministic"


def test_edge_strength_preserves_matrix_structure(
    mock_connectivity_matrix,
    temp_metrics_dir
):
    """
    Test that edge strength extraction preserves the matrix structure.
    
    For a 200x200 matrix, we expect 200*199/2 = 19900 unique edges (upper triangle).
    """
    result = calculate_network_metrics(
        connectivity_path=str(mock_connectivity_matrix),
        output_dir=str(temp_metrics_dir["metrics_dir"]),
        subject_id="sub-001"
    )
    
    edge_strengths = result["edge_strength"]
    
    # For a 200x200 matrix, upper triangle has 200*199/2 = 19900 edges
    expected_edge_count = 200 * 199 // 2
    assert len(edge_strengths) == expected_edge_count, \
        f"Expected {expected_edge_count} edges, got {len(edge_strengths)}"
    
    # Verify all edges are unique and within bounds
    edge_pairs = set()
    for edge in edge_strengths:
        pair = (edge["source"], edge["target"])
        assert pair not in edge_pairs, f"Duplicate edge: {pair}"
        edge_pairs.add(pair)
        assert 0 <= edge["source"] < 200
        assert 0 <= edge["target"] < 200
        assert edge["source"] != edge["target"]  # No self-loops
        assert edge["source"] < edge["target"]  # Upper triangle only


def test_metrics_output_schema_matches_contract(
    mock_connectivity_matrix,
    temp_metrics_dir
):
    """
    Test that the metrics output matches the contract defined in T016.
    
    This ensures compatibility with the downstream statistical analysis in US3.
    """
    from tests.contract.test_metrics_schema import validate_metrics_schema
    
    result = calculate_network_metrics(
        connectivity_path=str(mock_connectivity_matrix),
        output_dir=str(temp_metrics_dir["metrics_dir"]),
        subject_id="sub-001"
    )
    
    # Validate against the contract schema
    is_valid, errors = validate_metrics_schema(result)
    
    assert is_valid, f"Metrics output failed schema validation: {errors}"