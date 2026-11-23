import pytest
import json
import tempfile
from pathlib import Path
from synthetic.validator import boxes_overlap, validate_no_overlaps, validate_synthetic_image_file

class TestBoxesOverlap:
    def test_no_overlap_horizontal(self):
        # Box1: (0,0,10,10), Box2: (10,0,20,10) -> Touching at x=10
        box1 = (0, 0, 10, 10)
        box2 = (10, 0, 20, 10)
        assert boxes_overlap(box1, box2, tolerance=0) is False

    def test_overlap_horizontal(self):
        # Box1: (0,0,10,10), Box2: (5,0,15,10) -> Overlap x in [5,10]
        box1 = (0, 0, 10, 10)
        box2 = (5, 0, 15, 10)
        assert boxes_overlap(box1, box2, tolerance=0) is True

    def test_no_overlap_vertical(self):
        # Box1: (0,0,10,10), Box2: (0,10,10,20) -> Touching at y=10
        box1 = (0, 0, 10, 10)
        box2 = (0, 10, 10, 20)
        assert boxes_overlap(box1, box2, tolerance=0) is False

    def test_overlap_vertical(self):
        # Box1: (0,0,10,10), Box2: (0,5,10,15) -> Overlap y in [5,10]
        box1 = (0, 0, 10, 10)
        box2 = (0, 5, 10, 15)
        assert boxes_overlap(box1, box2, tolerance=0) is True

    def test_tolerance_gap(self):
        # Box1: (0,0,10,10), Box2: (11,0,21,10) -> Gap of 1
        box1 = (0, 0, 10, 10)
        box2 = (11, 0, 21, 10)
        # With tolerance=1, gap of 1 is required, so they should NOT overlap
        assert boxes_overlap(box1, box2, tolerance=1) is False
        
        # With tolerance=2, gap of 1 is NOT enough, so they are considered overlapping (or rather, the check fails)
        # Wait: logic is: if x2_1 + tolerance <= x1_2 -> no overlap.
        # 10 + 2 <= 11 -> 12 <= 11 (False)
        # 11 + 2 <= 0 (False)
        # So returns True (overlap)
        assert boxes_overlap(box1, box2, tolerance=2) is True

class TestValidateNoOverlaps:
    def test_empty_list(self):
        assert validate_no_overlaps([]) is True

    def test_single_box(self):
        assert validate_no_overlaps([(0, 0, 10, 10)]) is True

    def test_no_overlap(self):
        boxes = [(0, 0, 10, 10), (10, 0, 20, 10), (0, 10, 10, 20)]
        assert validate_no_overlaps(boxes) is True

    def test_with_overlap(self):
        boxes = [(0, 0, 10, 10), (5, 0, 15, 10)]
        assert validate_no_overlaps(boxes) is False

class TestValidateSyntheticImageFile:
    def test_valid_file(self):
        valid_data = {
            "image_path": "test.png",
            "bounding_boxes": [
                {"x": 0, "y": 0, "w": 10, "h": 10, "id": 1},
                {"x": 20, "y": 20, "w": 10, "h": 10, "id": 2}
            ],
            "derived_relations": []
        }
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(valid_data, f)
            temp_path = Path(f.name)
        
        try:
            # Note: This relies on contracts.validator.validate_synthetic_image
            # which we assume is implemented correctly in T042.
            # If the schema check passes and no overlaps exist, it should return True.
            result = validate_synthetic_image_file(temp_path)
            # Depending on schema strictness, this might be True or False if schema is strict about types.
            # We assume the schema allows this structure.
            assert result is True
        finally:
            temp_path.unlink()

    def test_overlapping_boxes(self):
        overlapping_data = {
            "image_path": "test.png",
            "bounding_boxes": [
                {"x": 0, "y": 0, "w": 10, "h": 10, "id": 1},
                {"x": 5, "y": 0, "w": 10, "h": 10, "id": 2}
            ],
            "derived_relations": []
        }
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(overlapping_data, f)
            temp_path = Path(f.name)
        
        try:
            result = validate_synthetic_image_file(temp_path)
            assert result is False
        finally:
            temp_path.unlink()

    def test_missing_file(self):
        result = validate_synthetic_image_file(Path("/nonexistent/file.json"))
        assert result is False

    def test_invalid_json(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write("not valid json")
            temp_path = Path(f.name)
        
        try:
            result = validate_synthetic_image_file(temp_path)
            assert result is False
        finally:
            temp_path.unlink()
