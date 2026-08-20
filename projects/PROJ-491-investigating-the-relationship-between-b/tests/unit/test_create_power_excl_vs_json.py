import json
import math
import tempfile
from pathlib import Path
import pytest

from create_power_excl_vs_json import (
    load_json,
    calculate_distance,
    find_overlapping_nodes,
    write_exclusion_contract
)


class TestCalculateDistance:
    def test_same_coordinates(self):
        """Distance between identical points should be 0."""
        coord1 = [0.0, 0.0, 0.0]
        coord2 = [0.0, 0.0, 0.0]
        assert calculate_distance(coord1, coord2) == 0.0

    def test_axis_aligned_distance(self):
        """Distance along a single axis."""
        coord1 = [0.0, 0.0, 0.0]
        coord2 = [3.0, 0.0, 0.0]
        assert calculate_distance(coord1, coord2) == 3.0

    def test_3d_distance(self):
        """3D Euclidean distance calculation."""
        coord1 = [0.0, 0.0, 0.0]
        coord2 = [3.0, 4.0, 0.0]
        assert calculate_distance(coord1, coord2) == 5.0

    def test_invalid_coordinates(self):
        """Should raise ValueError for non-3D coordinates."""
        with pytest.raises(ValueError):
            calculate_distance([0.0, 0.0], [0.0, 0.0, 0.0])


class TestFindOverlappingNodes:
    def test_no_overlap(self):
        """No nodes should overlap when all are far from ROI."""
        power_nodes = [
            {"id": 1, "x": 0.0, "y": 0.0, "z": 0.0},
            {"id": 2, "x": 100.0, "y": 100.0, "z": 100.0}
        ]
        vs_roi = {"center": [50.0, 50.0, 50.0]}
        
        # All nodes are > 10mm from center
        overlapping = find_overlapping_nodes(power_nodes, vs_roi, distance_threshold=10.0)
        assert len(overlapping) == 0

    def test_single_overlap(self):
        """One node should overlap when close to ROI."""
        power_nodes = [
            {"id": 1, "x": 0.0, "y": 0.0, "z": 0.0},
            {"id": 2, "x": 5.0, "y": 0.0, "z": 0.0}
        ]
        vs_roi = {"center": [0.0, 0.0, 0.0]}
        
        overlapping = find_overlapping_nodes(power_nodes, vs_roi, distance_threshold=10.0)
        assert len(overlapping) == 1
        assert overlapping[0]["id"] == 1
        assert "distance_to_vs" in overlapping[0]

    def test_multiple_overlaps(self):
        """Multiple nodes should overlap when within threshold."""
        power_nodes = [
            {"id": 1, "x": 0.0, "y": 0.0, "z": 0.0},
            {"id": 2, "x": 5.0, "y": 0.0, "z": 0.0},
            {"id": 3, "x": 8.0, "y": 0.0, "z": 0.0},
            {"id": 4, "x": 15.0, "y": 0.0, "z": 0.0}
        ]
        vs_roi = {"center": [0.0, 0.0, 0.0]}
        
        overlapping = find_overlapping_nodes(power_nodes, vs_roi, distance_threshold=10.0)
        assert len(overlapping) == 3
        # Should include nodes 1, 2, 3 but not 4
        ids = [n["id"] for n in overlapping]
        assert 1 in ids and 2 in ids and 3 in ids and 4 not in ids

    def test_missing_coordinates(self):
        """Nodes without coordinates should be skipped."""
        power_nodes = [
            {"id": 1, "x": 0.0, "y": 0.0, "z": 0.0},
            {"id": 2, "x": 0.0},  # Missing y and z
            {"id": 3}  # No coordinates at all
        ]
        vs_roi = {"center": [0.0, 0.0, 0.0]}
        
        overlapping = find_overlapping_nodes(power_nodes, vs_roi, distance_threshold=10.0)
        assert len(overlapping) == 1
        assert overlapping[0]["id"] == 1

    def test_missing_vs_center(self):
        """Should raise ValueError if VS ROI has no center."""
        power_nodes = [{"id": 1, "x": 0.0, "y": 0.0, "z": 0.0}]
        vs_roi = {}  # No center key
        
        with pytest.raises(ValueError):
            find_overlapping_nodes(power_nodes, vs_roi)


class TestWriteExclusionContract:
    def test_writes_valid_json(self):
        """Contract file should be valid JSON."""
        overlapping_nodes = [
            {"id": 1, "x": 0.0, "y": 0.0, "z": 0.0, "distance_to_vs": 5.0}
        ]
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_path = f.name
        
        try:
            write_exclusion_contract(overlapping_nodes, temp_path)
            
            with open(temp_path, 'r') as f:
                data = json.load(f)
            
            assert "excluded_nodes" in data
            assert "excluded_node_ids" in data
            assert "total_excluded" in data
            assert data["total_excluded"] == 1
        finally:
            Path(temp_path).unlink()

    def test_includes_metadata(self):
        """Contract should include description and parameters."""
        overlapping_nodes = [
            {"id": 1, "x": 0.0, "y": 0.0, "z": 0.0, "distance_to_vs": 5.0}
        ]
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_path = f.name
        
        try:
            write_exclusion_contract(
                overlapping_nodes, 
                temp_path,
                vs_roi_id="test_roi",
                distance_threshold=15.0
            )
            
            with open(temp_path, 'r') as f:
                data = json.load(f)
            
            assert data["vs_roi_id"] == "test_roi"
            assert data["distance_threshold_mm"] == 15.0
            assert "Prevent double-dipping" in data["exclusion_reason"]
        finally:
            Path(temp_path).unlink()