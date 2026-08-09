import json
import os
import pytest
from pathlib import Path
from unittest.mock import patch, mock_open

# Import the functions to test
from data.graph_utils import (
    build_route_graph,
    compute_jaccard_index,
    validate_graph_against_ground_truth,
    load_ground_truth,
    load_processed_routes
)

def test_build_route_graph_basic():
    """Test building a graph from a simple list of routes."""
    routes = [
        {"stops": ["A", "B", "C"]},
        {"stops": ["C", "D"]}
    ]
    edges = build_route_graph(routes)
    expected = {("A", "B"), ("B", "C"), ("C", "D")}
    assert edges == expected

def test_build_route_graph_empty():
    """Test building a graph from empty or invalid routes."""
    routes = [
        {"stops": []},
        {"stops": ["A"]},
        {},
        None
    ]
    edges = build_route_graph(routes)
    assert edges == set()

def test_build_route_graph_alternative_keys():
    """Test that the function handles alternative keys for stops."""
    routes = [
        {"stations": ["X", "Y"]},
        {"stop_sequence": ["Y", "Z"]}
    ]
    edges = build_route_graph(routes)
    expected = {("X", "Y"), ("Y", "Z")}
    assert edges == expected

def test_jaccard_index_identical_sets():
    """Test Jaccard index for identical sets."""
    s1 = {"A", "B", "C"}
    s2 = {"A", "B", "C"}
    assert compute_jaccard_index(s1, s2) == 1.0

def test_jaccard_index_disjoint_sets():
    """Test Jaccard index for disjoint sets."""
    s1 = {"A", "B"}
    s2 = {"C", "D"}
    assert compute_jaccard_index(s1, s2) == 0.0

def test_jaccard_index_partial_overlap():
    """Test Jaccard index for partially overlapping sets."""
    s1 = {"A", "B", "C"}
    s2 = {"B", "C", "D"}
    # Intersection: {B, C} (2)
    # Union: {A, B, C, D} (4)
    assert compute_jaccard_index(s1, s2) == 0.5

def test_jaccard_index_empty_sets():
    """Test Jaccard index for empty sets."""
    assert compute_jaccard_index(set(), set()) == 1.0
    assert compute_jaccard_index({"A"}, set()) == 0.0
    assert compute_jaccard_index(set(), {"A"}) == 0.0

@pytest.mark.parametrize("threshold,expected_status", [
    (0.95, "PASS"),
    (0.99, "FAIL")
])
def test_validate_graph_against_ground_truth_success_and_fail(tmp_path, threshold, expected_status):
    """
    Test validate_graph_against_ground_truth with mock data.
    This test verifies the logic of the validation and the raising of RuntimeError on failure.
    """
    # Prepare mock data
    routes_data = [
        {"stops": ["A", "B", "C"]},
        {"stops": ["C", "D"]}
    ]
    # Ground truth has slightly different edges to test threshold
    gt_data = [
        {"stops": ["A", "B", "C"]},
        {"stops": ["C", "D"]},
        {"stops": ["E", "F"]} # Extra edge in GT
    ]

    routes_file = tmp_path / "routes.jsonl"
    gt_file = tmp_path / "gt.json"
    report_file = tmp_path / "report.json"

    with open(routes_file, 'w') as f:
        for r in routes_data:
            f.write(json.dumps(r) + "\n")

    with open(gt_file, 'w') as f:
        json.dump(gt_data, f)

    # Calculate expected Jaccard manually
    # Route edges: (A,B), (B,C), (C,D) -> 3 edges
    # GT edges: (A,B), (B,C), (C,D), (E,F) -> 4 edges
    # Intersection: 3
    # Union: 4
    # Jaccard: 0.75

    if expected_status == "FAIL":
        with pytest.raises(RuntimeError, match="Graph validation FAILED"):
            validate_graph_against_ground_truth(
                routes_path=str(routes_file),
                ground_truth_path=str(gt_file),
                output_path=str(report_file),
                threshold=threshold
            )
    else:
        # For PASS, we need Jaccard >= threshold.
        # With current data J=0.75. If threshold is 0.95, it should fail.
        # Let's adjust the test data for the PASS case.
        if threshold == 0.95:
            # Make GT identical to routes
            gt_data_pass = [
                {"stops": ["A", "B", "C"]},
                {"stops": ["C", "D"]}
            ]
            with open(gt_file, 'w') as f:
                json.dump(gt_data_pass, f)
            
            validate_graph_against_ground_truth(
                routes_path=str(routes_file),
                ground_truth_path=str(gt_file),
                output_path=str(report_file),
                threshold=threshold
            )
            
            assert report_file.exists()
            with open(report_file) as f:
                report = json.load(f)
            assert report["status"] == "PASS"
            assert report["jaccard_index"] == 1.0
def test_load_ground_truth_file_not_found():
    """Test that load_ground_truth raises FileNotFoundError."""
    with pytest.raises(FileNotFoundError):
        load_ground_truth("non_existent_file.json")

def test_load_processed_routes_file_not_found():
    """Test that load_processed_routes raises FileNotFoundError."""
    with pytest.raises(FileNotFoundError):
        load_processed_routes("non_existent_file.jsonl")
