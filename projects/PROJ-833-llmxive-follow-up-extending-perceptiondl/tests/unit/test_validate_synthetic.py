import pytest
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import sys
import os

# Add the code directory to the path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))

from analysis.validate_synthetic import (
    load_json_file,
    validate_relations_in_file,
    validate_all_files
)
from synthetic.deriver import calculate_centroid, derive_spatial_relation


class TestValidateSynthetic:
    """Unit tests for synthetic dataset validation logic."""

    def test_load_json_file_success(self, tmp_path):
        """Test loading a valid JSON file."""
        test_data = {"key": "value", "number": 42}
        test_file = tmp_path / "test.json"
        
        with open(test_file, 'w') as f:
            json.dump(test_data, f)
        
        result = load_json_file(test_file)
        
        assert result == test_data
        assert result["key"] == "value"
        assert result["number"] == 42

    def test_load_json_file_not_found(self, tmp_path):
        """Test loading a non-existent file raises error."""
        test_file = tmp_path / "nonexistent.json"
        
        with pytest.raises(FileNotFoundError):
            load_json_file(test_file)

    def test_validate_relations_in_file_valid(self, tmp_path):
        """Test validation with correct geometric relations."""
        # Create a simple test case with two boxes
        test_data = {
            "bounding_boxes": [
                {"id": 0, "x": 10, "y": 10, "w": 20, "h": 20},
                {"id": 1, "x": 100, "y": 10, "w": 20, "h": 20}
            ],
            "derived_relations": ["box_0 left of box_1"]
        }
        
        test_file = tmp_path / "valid.json"
        with open(test_file, 'w') as f:
            json.dump(test_data, f)
        
        is_valid, errors = validate_relations_in_file(test_file)
        
        assert is_valid is True
        assert len(errors) == 0

    def test_validate_relations_in_file_invalid(self, tmp_path):
        """Test validation with incorrect geometric relations."""
        # Create test case where relation is wrong
        test_data = {
            "bounding_boxes": [
                {"id": 0, "x": 10, "y": 10, "w": 20, "h": 20},
                {"id": 1, "x": 100, "y": 10, "w": 20, "h": 20}
            ],
            "derived_relations": ["box_0 right of box_1"]  # Wrong!
        }
        
        test_file = tmp_path / "invalid.json"
        with open(test_file, 'w') as f:
            json.dump(test_data, f)
        
        is_valid, errors = validate_relations_in_file(test_file)
        
        assert is_valid is False
        assert len(errors) > 0
        assert any("Missing relations" in error for error in errors)

    def test_validate_relations_in_file_no_boxes(self, tmp_path):
        """Test validation with no bounding boxes."""
        test_data = {
            "bounding_boxes": [],
            "derived_relations": []
        }
        
        test_file = tmp_path / "no_boxes.json"
        with open(test_file, 'w') as f:
            json.dump(test_data, f)
        
        is_valid, errors = validate_relations_in_file(test_file)
        
        assert is_valid is False
        assert any("No bounding boxes found" in error for error in errors)

    def test_validate_all_files_multiple_files(self, tmp_path):
        """Test validation of multiple files."""
        # Create valid file
        valid_data = {
            "bounding_boxes": [
                {"id": 0, "x": 10, "y": 10, "w": 20, "h": 20},
                {"id": 1, "x": 100, "y": 10, "w": 20, "h": 20}
            ],
            "derived_relations": ["box_0 left of box_1"]
        }
        
        valid_file = tmp_path / "valid.json"
        with open(valid_file, 'w') as f:
            json.dump(valid_data, f)
        
        # Create invalid file
        invalid_data = {
            "bounding_boxes": [
                {"id": 0, "x": 10, "y": 10, "w": 20, "h": 20},
                {"id": 1, "x": 100, "y": 10, "w": 20, "h": 20}
            ],
            "derived_relations": ["box_0 right of box_1"]
        }
        
        invalid_file = tmp_path / "invalid.json"
        with open(invalid_file, 'w') as f:
            json.dump(invalid_data, f)
        
        all_valid, errors = validate_all_files(tmp_path)
        
        assert all_valid is False
        assert len(errors) > 0

    def test_centroid_calculation(self):
        """Test centroid calculation matches geometric reality."""
        box = {"x": 10, "y": 20, "w": 100, "h": 50}
        centroid = calculate_centroid(box)
        
        expected_x = 10 + 100 / 2  # 60
        expected_y = 20 + 50 / 2   # 45
        
        assert abs(centroid[0] - expected_x) < 0.001
        assert abs(centroid[1] - expected_y) < 0.001

    def test_spatial_relation_derivation(self):
        """Test spatial relation derivation matches geometric reality."""
        # Box A at (0, 0), Box B at (100, 0) -> A is left of B
        centroid_a = (0, 0)
        centroid_b = (100, 0)
        
        relation = derive_spatial_relation(centroid_a, centroid_b)
        
        assert relation == "left of"
        
        # Box A at (100, 0), Box B at (0, 0) -> A is right of B
        relation = derive_spatial_relation(centroid_b, centroid_a)
        
        assert relation == "right of"
        
        # Box A at (0, 0), Box B at (0, 100) -> A is above B
        relation = derive_spatial_relation(centroid_a, (0, 100))
        
        assert relation == "above"
        
        # Box A at (0, 100), Box B at (0, 0) -> A is below B
        relation = derive_spatial_relation((0, 100), centroid_a)
        
        assert relation == "below"
