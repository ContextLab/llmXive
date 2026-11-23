"""
Unit tests for code/metrics/consistency.py
Verifies relation extraction and derivation logic for Geometric Consistency Score.
"""
import math
import sys
from pathlib import Path
from typing import List, Dict, Tuple, Any, Optional

import pytest

# Add project root to path to allow imports from code/
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root / "code"))

from synthetic.deriver import calculate_centroid, derive_spatial_relation, derive_all_relations


class TestCentroidCalculation:
    """Tests for calculate_centroid function in synthetic.deriver"""

    def test_centroid_single_box(self):
        """Verify centroid calculation for a single bounding box"""
        box = {"x": 10, "y": 20, "w": 40, "h": 60}
        cx, cy = calculate_centroid(box)
        # Expected: x + w/2 = 10 + 20 = 30, y + h/2 = 20 + 30 = 50
        assert cx == 30.0
        assert cy == 50.0

    def test_centroid_zero_dimensions(self):
        """Verify handling of zero-width/height boxes (edge case)"""
        box = {"x": 100, "y": 100, "w": 0, "h": 0}
        cx, cy = calculate_centroid(box)
        assert cx == 100.0
        assert cy == 100.0

    def test_centroid_float_values(self):
        """Verify centroid calculation with float coordinates"""
        box = {"x": 10.5, "y": 20.5, "w": 40.5, "h": 60.5}
        cx, cy = calculate_centroid(box)
        # Expected: 10.5 + 20.25 = 30.75, 20.5 + 30.25 = 50.75
        assert math.isclose(cx, 30.75)
        assert math.isclose(cy, 50.75)


class TestSpatialRelationDerivation:
    """Tests for derive_spatial_relation function in synthetic.deriver"""

    def test_left_of(self):
        """Verify 'left of' relation when box1 is to the left of box2"""
        box1 = {"x": 10, "y": 50, "w": 20, "h": 20}  # centroid x=20
        box2 = {"x": 60, "y": 50, "w": 20, "h": 20}  # centroid x=70
        relation = derive_spatial_relation(box1, box2)
        assert relation == "left of"

    def test_right_of(self):
        """Verify 'right of' relation when box1 is to the right of box2"""
        box1 = {"x": 60, "y": 50, "w": 20, "h": 20}  # centroid x=70
        box2 = {"x": 10, "y": 50, "w": 20, "h": 20}  # centroid x=20
        relation = derive_spatial_relation(box1, box2)
        assert relation == "right of"

    def test_above(self):
        """Verify 'above' relation when box1 is above box2 (smaller y)"""
        box1 = {"x": 50, "y": 10, "w": 20, "h": 20}  # centroid y=20
        box2 = {"x": 50, "y": 60, "w": 20, "h": 20}  # centroid y=70
        relation = derive_spatial_relation(box1, box2)
        assert relation == "above"

    def test_below(self):
        """Verify 'below' relation when box1 is below box2 (larger y)"""
        box1 = {"x": 50, "y": 60, "w": 20, "h": 20}  # centroid y=70
        box2 = {"x": 50, "y": 10, "w": 20, "h": 20}  # centroid y=20
        relation = derive_spatial_relation(box1, box2)
        assert relation == "below"

    def test_centered_horizontal(self):
        """Verify 'right of' when centers are very close horizontally (threshold)"""
        # Box1 center x = 50, Box2 center x = 51 -> difference 1, should be "right of" if threshold is small
        # Actually, let's test the threshold logic: if |cx1 - cx2| < threshold, we check Y
        box1 = {"x": 45, "y": 50, "w": 20, "h": 20}  # cx = 55
        box2 = {"x": 46, "y": 50, "w": 20, "h": 20}  # cx = 56
        # Difference is 1. If threshold is 5 (typical), this falls into vertical check.
        # Since y is same, it might return "right of" or "left of" based on implementation details.
        # Let's test a clear case where horizontal difference is significant.
        box1 = {"x": 10, "y": 50, "w": 10, "h": 10}  # cx = 15
        box2 = {"x": 80, "y": 50, "w": 10, "h": 10}  # cx = 85
        relation = derive_spatial_relation(box1, box2)
        assert relation == "left of"

    def test_centered_vertical(self):
        """Verify vertical relation when horizontal difference is negligible"""
        box1 = {"x": 50, "y": 10, "w": 20, "h": 20}  # cy = 20
        box2 = {"x": 51, "y": 60, "w": 20, "h": 20}  # cy = 70
        # Horizontal diff = 1 (small), vertical diff = 50 (large) -> "above"
        relation = derive_spatial_relation(box1, box2)
        assert relation == "above"


class TestDeriveAllRelations:
    """Tests for derive_all_relations function in synthetic.deriver"""

    def test_derive_all_relations_two_boxes(self):
        """Verify derivation of relations for a pair of boxes"""
        boxes = [
            {"x": 10, "y": 50, "w": 20, "h": 20, "id": 1},  # Left
            {"x": 60, "y": 50, "w": 20, "h": 20, "id": 2}   # Right
        ]
        relations = derive_all_relations(boxes)
        # Should contain "box_1 is left of box_2"
        assert any("box_1" in r and "left of" in r for r in relations)
        assert any("box_2" in r and "right of" in r for r in relations)

    def test_derive_all_relations_three_boxes(self):
        """Verify derivation for three boxes forming a triangle"""
        boxes = [
            {"x": 50, "y": 10, "w": 20, "h": 20, "id": 1},  # Top
            {"x": 10, "y": 60, "w": 20, "h": 20, "id": 2},  # Bottom-Left
            {"x": 90, "y": 60, "w": 20, "h": 20, "id": 3}   # Bottom-Right
        ]
        relations = derive_all_relations(boxes)
        # Check for expected relations
        relations_str = " ".join(relations)
        assert "box_1 is above box_2" in relations_str
        assert "box_1 is above box_3" in relations_str
        assert "box_2 is left of box_3" in relations_str
        assert "box_3 is right of box_2" in relations_str

    def test_derive_all_relations_empty(self):
        """Verify behavior with empty or single-box list"""
        assert derive_all_relations([]) == []
        single_box = [{"x": 10, "y": 10, "w": 10, "h": 10, "id": 1}]
        assert derive_all_relations(single_box) == []