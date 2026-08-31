import json
import os
import pytest
from pathlib import Path
from typing import Set, Tuple

# Import the module under test
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from data.graph_utils import (
    load_ground_truth,
    load_processed_routes,
    build_route_graph,
    compute_jaccard_index,
    validate_graph_against_ground_truth,
    main
)


class TestBuildRouteGraph:
    """Tests for build_route_graph function."""

    def test_empty_routes(self):
        """Test with empty route list."""
        routes = []
        edges = build_route_graph(routes)
        assert edges == set()

    def test_single_station_route(self):
        """Test with a route containing only one station."""
        routes = [{"stations": ["StationA"]}]
        edges = build_route_graph(routes)
        assert edges == set()

    def test_two_station_route(self):
        """Test with a route containing two stations."""
        routes = [{"stations": ["StationA", "StationB"]}]
        edges = build_route_graph(routes)
        expected = {("StationA", "StationB")}
        assert edges == expected

    def test_multi_station_route(self):
        """Test with a route containing multiple stations."""
        routes = [{"stations": ["A", "B", "C", "D"]}]
        edges = build_route_graph(routes)
        expected = {("A", "B"), ("B", "C"), ("C", "D")}
        assert edges == expected

    def test_multiple_routes(self):
        """Test with multiple routes."""
        routes = [
            {"stations": ["A", "B", "C"]},
            {"stations": ["C", "D", "E"]},
            {"stations": ["A", "E"]}
        ]
        edges = build_route_graph(routes)
        expected = {("A", "B"), ("B", "C"), ("C", "D"), ("D", "E"), ("A", "E")}
        assert edges == expected

    def test_duplicate_edges(self):
        """Test that duplicate edges are deduplicated."""
        routes = [
            {"stations": ["A", "B", "C"]},
            {"stations": ["A", "B", "C"]}
        ]
        edges = build_route_graph(routes)
        expected = {("A", "B"), ("B", "C")}
        assert edges == expected


class TestComputeJaccardIndex:
    """Tests for compute_jaccard_index function."""

    def test_identical_sets(self):
        """Test with identical sets."""
        set_a = {"A", "B", "C"}
        set_b = {"A", "B", "C"}
        index = compute_jaccard_index(set_a, set_b)
        assert index == 1.0

    def test_disjoint_sets(self):
        """Test with disjoint sets."""
        set_a = {"A", "B"}
        set_b = {"C", "D"}
        index = compute_jaccard_index(set_a, set_b)
        assert index == 0.0

    def test_partial_overlap(self):
        """Test with partially overlapping sets."""
        set_a = {"A", "B", "C"}
        set_b = {"B", "C", "D"}
        # Intersection: {B, C} -> 2
        # Union: {A, B, C, D} -> 4
        # Jaccard: 2/4 = 0.5
        index = compute_jaccard_index(set_a, set_b)
        assert index == 0.5

    def test_empty_sets(self):
        """Test with both sets empty."""
        set_a = set()
        set_b = set()
        index = compute_jaccard_index(set_a, set_b)
        assert index == 1.0

    def test_one_empty_set(self):
        """Test with one empty set."""
        set_a = {"A", "B"}
        set_b = set()
        index = compute_jaccard_index(set_a, set_b)
        assert index == 0.0


class TestValidateGraphAgainstGroundTruth:
    """Tests for validate_graph_against_ground_truth function."""

    def test_passing_validation(self, tmp_path):
        """Test validation that passes the threshold."""
        # Create ground truth file
        gt_data = {
            "data": [
                {"stations": ["A", "B", "C"]},
                {"stations": ["C", "D"]}
            ]
        }
        gt_path = tmp_path / "ground_truth.json"
        with open(gt_path, 'w') as f:
            json.dump(gt_data, f)

        # Create processed routes file (identical)
        processed_path = tmp_path / "processed.jsonl"
        with open(processed_path, 'w') as f:
            f.write(json.dumps({"stations": ["A", "B", "C"]}) + "\n")
            f.write(json.dumps({"stations": ["C", "D"]}) + "\n")

        # Output path
        output_path = tmp_path / "report.json"

        # Run validation
        report = validate_graph_against_ground_truth(
            str(gt_path),
            str(processed_path),
            str(output_path),
            threshold=0.95
        )

        assert report["status"] == "PASS"
        assert report["jaccard_index"] == 1.0
        assert output_path.exists()

    def test_failing_validation(self, tmp_path):
        """Test validation that fails the threshold."""
        # Create ground truth file
        gt_data = {
            "data": [
                {"stations": ["A", "B", "C", "D"]}
            ]
        }
        gt_path = tmp_path / "ground_truth.json"
        with open(gt_path, 'w') as f:
            json.dump(gt_data, f)

        # Create processed routes file (different edges)
        processed_path = tmp_path / "processed.jsonl"
        with open(processed_path, 'w') as f:
            f.write(json.dumps({"stations": ["X", "Y", "Z"]}) + "\n")

        # Output path
        output_path = tmp_path / "report.json"

        # Run validation - should raise RuntimeError
        with pytest.raises(RuntimeError, match="Graph validation FAILED"):
            validate_graph_against_ground_truth(
                str(gt_path),
                str(processed_path),
                str(output_path),
                threshold=0.95
            )

    def test_missing_ground_truth_file(self, tmp_path):
        """Test with missing ground truth file."""
        processed_path = tmp_path / "processed.jsonl"
        output_path = tmp_path / "report.json"

        with pytest.raises(FileNotFoundError):
            validate_graph_against_ground_truth(
                str(tmp_path / "nonexistent.json"),
                str(processed_path),
                str(output_path)
            )

    def test_missing_processed_routes_file(self, tmp_path):
        """Test with missing processed routes file."""
        gt_path = tmp_path / "ground_truth.json"
        with open(gt_path, 'w') as f:
            json.dump({"data": []}, f)

        output_path = tmp_path / "report.json"

        with pytest.raises(FileNotFoundError):
            validate_graph_against_ground_truth(
                str(gt_path),
                str(tmp_path / "nonexistent.jsonl"),
                str(output_path)
            )


class TestLoadGroundTruth:
    """Tests for load_ground_truth function."""

    def test_load_valid_json(self, tmp_path):
        """Test loading a valid JSON file."""
        data = {"key": "value", "number": 42}
        path = tmp_path / "test.json"
        with open(path, 'w') as f:
            json.dump(data, f)

        result = load_ground_truth(str(path))
        assert result == data

    def test_file_not_found(self, tmp_path):
        """Test loading a non-existent file."""
        with pytest.raises(FileNotFoundError):
            load_ground_truth(str(tmp_path / "nonexistent.json"))


class TestLoadProcessedRoutes:
    """Tests for load_processed_routes function."""

    def test_load_valid_jsonl(self, tmp_path):
        """Test loading a valid JSONL file."""
        path = tmp_path / "test.jsonl"
        with open(path, 'w') as f:
            f.write('{"stations": ["A", "B"]}\n')
            f.write('{"stations": ["C", "D"]}\n')

        result = load_processed_routes(str(path))
        assert len(result) == 2
        assert result[0]["stations"] == ["A", "B"]
        assert result[1]["stations"] == ["C", "D"]

    def test_file_not_found(self, tmp_path):
        """Test loading a non-existent file."""
        with pytest.raises(FileNotFoundError):
            load_processed_routes(str(tmp_path / "nonexistent.jsonl"))

    def test_empty_file(self, tmp_path):
        """Test loading an empty file."""
        path = tmp_path / "empty.jsonl"
        path.touch()

        result = load_processed_routes(str(path))
        assert result == []
