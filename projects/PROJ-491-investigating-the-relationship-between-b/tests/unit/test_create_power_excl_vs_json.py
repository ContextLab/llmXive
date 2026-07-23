"""
Unit tests for create_power_excl_vs_json module.
"""
import json
import math
import tempfile
from pathlib import Path
import pytest

# Import the functions to test
from create_power_excl_vs_json import (
    load_json,
    calculate_distance,
    find_overlapping_nodes,
    write_exclusion_contract,
    main
)


class TestCalculateDistance:
    def test_identical_coords(self):
        assert calculate_distance([0, 0, 0], [0, 0, 0]) == 0.0

    def test_simple_distance(self):
        # Distance between (0,0,0) and (3,4,0) is 5
        assert calculate_distance([0, 0, 0], [3, 4, 0]) == 5.0

    def test_3d_distance(self):
        # Distance between (0,0,0) and (1,2,2) is 3
        assert calculate_distance([0, 0, 0], [1, 2, 2]) == 3.0

    def test_invalid_coords(self):
        with pytest.raises(ValueError):
            calculate_distance([0, 0], [0, 0, 0])


class TestFindOverlappingNodes:
    def test_no_overlap(self):
        nodes = [{"node_id": 1, "coords": [0, 0, 0]}]
        vs_center = [100, 100, 100]
        overlaps = find_overlapping_nodes(nodes, vs_center, threshold_mm=10.0)
        assert len(overlaps) == 0

    def test_exact_overlap(self):
        nodes = [{"node_id": 1, "coords": [10, 10, 10]}]
        vs_center = [10, 10, 10]
        overlaps = find_overlapping_nodes(nodes, vs_center, threshold_mm=10.0)
        assert len(overlaps) == 1
        assert overlaps[0] == 1

    def test_threshold_boundary(self):
        # Distance is exactly 10.0
        nodes = [{"node_id": 1, "coords": [10, 0, 0]}]
        vs_center = [0, 0, 0]
        overlaps = find_overlapping_nodes(nodes, vs_center, threshold_mm=10.0)
        assert len(overlaps) == 1

    def test_just_outside_threshold(self):
        # Distance is 10.1
        nodes = [{"node_id": 1, "coords": [10.1, 0, 0]}]
        vs_center = [0, 0, 0]
        overlaps = find_overlapping_nodes(nodes, vs_center, threshold_mm=10.0)
        assert len(overlaps) == 0

    def test_mixed_results(self):
        nodes = [
            {"node_id": 1, "coords": [0, 0, 0]},      # Dist 0
            {"node_id": 2, "coords": [5, 0, 0]},      # Dist 5
            {"node_id": 3, "coords": [15, 0, 0]}      # Dist 15
        ]
        vs_center = [0, 0, 0]
        overlaps = find_overlapping_nodes(nodes, vs_center, threshold_mm=10.0)
        assert len(overlaps) == 2
        assert 1 in overlaps
        assert 2 in overlaps
        assert 3 not in overlaps


class TestWriteExclusionContract:
    def test_write_contract(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_contract.json"
            ids = [1, 2, 3]
            write_exclusion_contract(ids, output_path)
            
            assert output_path.exists()
            with open(output_path, "r") as f:
                data = json.load(f)
            
            assert "overlapping_node_ids" in data
            assert data["overlapping_node_ids"] == [1, 2, 3]
            assert data["count"] == 3
            assert data["threshold_mm"] == 10.0