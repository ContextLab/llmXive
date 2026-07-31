"""
Unit tests for code/synthetic/geometry_validator.py
"""
import json
import tempfile
from pathlib import Path
import pytest

from synthetic.geometry_validator import validate_geometry_in_file, validate_all_in_directory
from synthetic.deriver import calculate_centroid, derive_spatial_relation


def test_validate_geometry_pass():
    """Test that a file with correct derived_relations passes validation."""
    # Create a simple case: two boxes, one left of the other
    # Box 1: (0, 0, 10, 10) -> centroid (5, 5)
    # Box 2: (20, 0, 10, 10) -> centroid (25, 5)
    # Relation: Box 1 is "left of" Box 2, Box 2 is "right of" Box 1
    
    data = {
        "image_path": "test.png",
        "bounding_boxes": [
            {"x": 0, "y": 0, "w": 10, "h": 10, "id": "box1"},
            {"x": 20, "y": 0, "w": 10, "h": 10, "id": "box2"}
        ],
        "derived_relations": [
            "box1 left of box2",
            "box2 right of box1"
        ]
    }

    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(data, f)
        temp_path = Path(f.name)

    try:
        result = validate_geometry_in_file(temp_path)
        assert result is True
    finally:
        temp_path.unlink()


def test_validate_geometry_fail_missing_relation():
    """Test that a file with missing derived_relation fails validation."""
    # Same geometry as above, but missing one relation
    data = {
        "image_path": "test.png",
        "bounding_boxes": [
            {"x": 0, "y": 0, "w": 10, "h": 10, "id": "box1"},
            {"x": 20, "y": 0, "w": 10, "h": 10, "id": "box2"}
        ],
        "derived_relations": [
            "box1 left of box2"
            # Missing: "box2 right of box1"
        ]
    }

    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(data, f)
        temp_path = Path(f.name)

    try:
        with pytest.raises(ValueError, match="Missing"):
            validate_geometry_in_file(temp_path)
    finally:
        temp_path.unlink()


def test_validate_geometry_fail_wrong_relation():
    """Test that a file with incorrect derived_relation fails validation."""
    data = {
        "image_path": "test.png",
        "bounding_boxes": [
            {"x": 0, "y": 0, "w": 10, "h": 10, "id": "box1"},
            {"x": 20, "y": 0, "w": 10, "h": 10, "id": "box2"}
        ],
        "derived_relations": [
            "box1 above box2",  # Wrong!
            "box2 below box1"   # Wrong!
        ]
    }

    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(data, f)
        temp_path = Path(f.name)

    try:
        with pytest.raises(ValueError, match="Missing"):
            validate_geometry_in_file(temp_path)
    finally:
        temp_path.unlink()


def test_validate_geometry_three_boxes():
    """Test validation with three boxes in a triangle arrangement."""
    # Box 1: (0, 0, 10, 10) -> centroid (5, 5)
    # Box 2: (20, 0, 10, 10) -> centroid (25, 5)
    # Box 3: (10, 20, 10, 10) -> centroid (15, 25)
    # Relations: 1 left of 2, 1 below 3, 2 below 3 (and inverses)
    
    data = {
        "image_path": "test.png",
        "bounding_boxes": [
            {"x": 0, "y": 0, "w": 10, "h": 10, "id": "box1"},
            {"x": 20, "y": 0, "w": 10, "h": 10, "id": "box2"},
            {"x": 10, "y": 20, "w": 10, "h": 10, "id": "box3"}
        ],
        "derived_relations": [
            "box1 left of box2",
            "box2 right of box1",
            "box1 below box3",
            "box3 above box1",
            "box2 below box3",
            "box3 above box2"
        ]
    }

    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(data, f)
        temp_path = Path(f.name)

    try:
        result = validate_geometry_in_file(temp_path)
        assert result is True
    finally:
        temp_path.unlink()


def test_validate_directory():
    """Test validating multiple files in a directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        
        # Create two valid JSON files
        for i in range(2):
            data = {
                "image_path": f"test{i}.png",
                "bounding_boxes": [
                    {"x": 0, "y": 0, "w": 10, "h": 10, "id": "box1"},
                    {"x": 20, "y": 0, "w": 10, "h": 10, "id": "box2"}
                ],
                "derived_relations": [
                    "box1 left of box2",
                    "box2 right of box1"
                ]
            }
            json_path = tmpdir_path / f"test{i}.json"
            with open(json_path, 'w') as f:
                json.dump(data, f)
        
        count = validate_all_in_directory(tmpdir_path)
        assert count == 2


def test_validate_directory_with_invalid_file():
    """Test that directory validation fails if any file is invalid."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        
        # Create one valid file
        data_valid = {
            "image_path": "test0.png",
            "bounding_boxes": [
                {"x": 0, "y": 0, "w": 10, "h": 10, "id": "box1"},
                {"x": 20, "y": 0, "w": 10, "h": 10, "id": "box2"}
            ],
            "derived_relations": [
                "box1 left of box2",
                "box2 right of box1"
            ]
        }
        json_path_valid = tmpdir_path / "test0.json"
        with open(json_path_valid, 'w') as f:
            json.dump(data_valid, f)
        
        # Create one invalid file
        data_invalid = {
            "image_path": "test1.png",
            "bounding_boxes": [
                {"x": 0, "y": 0, "w": 10, "h": 10, "id": "box1"},
                {"x": 20, "y": 0, "w": 10, "h": 10, "id": "box2"}
            ],
            "derived_relations": [
                "box1 above box2"  # Wrong relation
            ]
        }
        json_path_invalid = tmpdir_path / "test1.json"
        with open(json_path_invalid, 'w') as f:
            json.dump(data_invalid, f)
        
        with pytest.raises(ValueError):
            validate_all_in_directory(tmpdir_path)