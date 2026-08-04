"""
tests/unit/test_geometry_validator.py

Unit tests for code/synthetic/geometry_validator.py
"""

import json
import tempfile
import os
from pathlib import Path
import pytest

from synthetic.geometry_validator import validate_geometry_in_file, validate_all_in_directory
from synthetic.deriver import calculate_centroid, derive_spatial_relation

def test_validate_geometry_in_file_correct():
    """Test validation with correct geometric relations."""
    # Create a temporary JSON file with correct relations
    data = {
        "image_path": "test.jpg",
        "bounding_boxes": [
            {"x": 0, "y": 0, "w": 10, "h": 10, "id": 1},
            {"x": 20, "y": 0, "w": 10, "h": 10, "id": 2}
        ],
        "derived_relations": ["left of"]  # Box 1 is left of Box 2
    }

    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(data, f)
        temp_path = f.name

    try:
        is_valid, errors = validate_geometry_in_file(temp_path)
        assert is_valid, f"Expected valid, got errors: {errors}"
        assert len(errors) == 0
    finally:
        os.unlink(temp_path)

def test_validate_geometry_in_file_incorrect():
    """Test validation with incorrect geometric relations."""
    # Box 1 is at x=0, Box 2 is at x=20. Box 1 is LEFT of Box 2.
    # We store "right of" which is incorrect.
    data = {
        "image_path": "test.jpg",
        "bounding_boxes": [
            {"x": 0, "y": 0, "w": 10, "h": 10, "id": 1},
            {"x": 20, "y": 0, "w": 10, "h": 10, "id": 2}
        ],
        "derived_relations": ["right of"]  # Incorrect!
    }

    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(data, f)
        temp_path = f.name

    try:
        is_valid, errors = validate_geometry_in_file(temp_path)
        assert not is_valid, "Expected invalid due to mismatched relation"
        assert len(errors) > 0
        assert any("Missing relations" in e or "Extra relations" in e for e in errors)
    finally:
        os.unlink(temp_path)

def test_validate_geometry_in_file_missing_file():
    """Test validation on a non-existent file."""
    with pytest.raises(FileNotFoundError):
        validate_geometry_in_file("/non/existent/path/file.json")

def test_validate_geometry_in_file_missing_key():
    """Test validation on a file missing required keys."""
    data = {
        "image_path": "test.jpg"
        # Missing bounding_boxes and derived_relations
    }

    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(data, f)
        temp_path = f.name

    try:
        with pytest.raises(ValueError):
            validate_geometry_in_file(temp_path)
    finally:
        os.unlink(temp_path)

def test_validate_all_in_directory():
    """Test validation of a directory with mixed valid/invalid files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a valid file
        valid_data = {
            "image_path": "valid.jpg",
            "bounding_boxes": [
                {"x": 0, "y": 0, "w": 10, "h": 10, "id": 1},
                {"x": 20, "y": 0, "w": 10, "h": 10, "id": 2}
            ],
            "derived_relations": ["left of"]
        }
        valid_path = os.path.join(tmpdir, "valid.json")
        with open(valid_path, 'w') as f:
            json.dump(valid_data, f)

        # Create an invalid file
        invalid_data = {
            "image_path": "invalid.jpg",
            "bounding_boxes": [
                {"x": 0, "y": 0, "w": 10, "h": 10, "id": 1},
                {"x": 20, "y": 0, "w": 10, "h": 10, "id": 2}
            ],
            "derived_relations": ["right of"]
        }
        invalid_path = os.path.join(tmpdir, "invalid.json")
        with open(invalid_path, 'w') as f:
            json.dump(invalid_data, f)

        total, valid, errors = validate_all_in_directory(tmpdir)

        assert total == 2
        assert valid == 1
        assert len(errors) == 1
        assert "invalid.json" in errors[0]

def test_centroid_calculation():
    """Test that centroid calculation is correct."""
    box = {"x": 10, "y": 10, "w": 20, "h": 20}
    centroid = calculate_centroid(box)
    assert centroid[0] == 20.0  # x + w/2
    assert centroid[1] == 20.0  # y + h/2

def test_derive_spatial_relation():
    """Test spatial relation derivation."""
    c1 = (10, 10)
    c2 = (30, 10)
    relation = derive_spatial_relation(c1, c2)
    assert relation == "left of"

    c3 = (30, 10)
    c4 = (10, 10)
    relation = derive_spatial_relation(c3, c4)
    assert relation == "right of"

    c5 = (10, 10)
    c6 = (10, 30)
    relation = derive_spatial_relation(c5, c6)
    assert relation == "above"

    c7 = (10, 30)
    c8 = (10, 10)
    relation = derive_spatial_relation(c7, c8)
    assert relation == "below"