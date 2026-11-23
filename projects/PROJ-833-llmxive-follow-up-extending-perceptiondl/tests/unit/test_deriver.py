"""
Unit tests for code/synthetic/deriver.py.
Verifies that derived relations correctly match the geometric reality of bounding box coordinates.
"""

import pytest
import math
from synthetic.deriver import calculate_centroid, derive_spatial_relation, derive_all_relations

class TestCalculateCentroid:
    def test_centroid_basic(self):
        """Test centroid calculation for a simple box."""
        box = {'x': 10, 'y': 10, 'w': 20, 'h': 20, 'id': 0}
        cx, cy = calculate_centroid(box)
        assert cx == 20.0
        assert cy == 20.0

    def test_centroid_asymmetric(self):
        """Test centroid calculation for an asymmetric box."""
        box = {'x': 0, 'y': 0, 'w': 100, 'h': 50, 'id': 1}
        cx, cy = calculate_centroid(box)
        assert cx == 50.0
        assert cy == 25.0

class TestDeriveSpatialRelation:
    def test_left_of(self):
        """Verify 'left of' relation when box1 is to the left of box2."""
        box1 = {'x': 10, 'y': 50, 'w': 20, 'h': 20, 'id': 0}  # centroid x = 20
        box2 = {'x': 100, 'y': 50, 'w': 20, 'h': 20, 'id': 1} # centroid x = 110
        # dx = 110 - 20 = 90 > threshold (20)
        relation = derive_spatial_relation(box1, box2)
        assert relation == "right of", f"Expected 'right of', got '{relation}'"

    def test_right_of(self):
        """Verify 'right of' relation when box1 is to the right of box2."""
        # Note: derive_spatial_relation(box1, box2) describes box2 relative to box1.
        # If box1 is at x=100 and box2 is at x=10, box2 is LEFT of box1.
        box1 = {'x': 100, 'y': 50, 'w': 20, 'h': 20, 'id': 0} # centroid x = 110
        box2 = {'x': 10, 'y': 50, 'w': 20, 'h': 20, 'id': 1}  # centroid x = 20
        relation = derive_spatial_relation(box1, box2)
        assert relation == "left of", f"Expected 'left of', got '{relation}'"

    def test_above(self):
        """Verify 'above' relation (y is smaller in image coords)."""
        box1 = {'x': 50, 'y': 100, 'w': 20, 'h': 20, 'id': 0} # centroid y = 110
        box2 = {'x': 50, 'y': 10, 'w': 20, 'h': 20, 'id': 1}  # centroid y = 20
        # dy = 20 - 110 = -90 < -threshold -> above
        relation = derive_spatial_relation(box1, box2)
        assert relation == "above", f"Expected 'above', got '{relation}'"

    def test_below(self):
        """Verify 'below' relation."""
        box1 = {'x': 50, 'y': 10, 'w': 20, 'h': 20, 'id': 0}  # centroid y = 20
        box2 = {'x': 50, 'y': 100, 'w': 20, 'h': 20, 'id': 1} # centroid y = 110
        # dy = 110 - 20 = 90 > threshold -> below
        relation = derive_spatial_relation(box1, box2)
        assert relation == "below", f"Expected 'below', got '{relation}'"

    def test_diagonal(self):
        """Verify diagonal relation."""
        box1 = {'x': 10, 'y': 10, 'w': 20, 'h': 20, 'id': 0}  # c=(20, 20)
        box2 = {'x': 100, 'y': 100, 'w': 20, 'h': 20, 'id': 1} # c=(110, 110)
        # dx = 90 (right), dy = 90 (below)
        relation = derive_spatial_relation(box1, box2)
        assert relation == "right and below", f"Expected 'right and below', got '{relation}'"

    def test_ambiguous_small_distance(self):
        """Verify None when boxes are too close."""
        box1 = {'x': 50, 'y': 50, 'w': 20, 'h': 20, 'id': 0} # c=(60, 60)
        box2 = {'x': 55, 'y': 55, 'w': 20, 'h': 20, 'id': 1} # c=(65, 65)
        # dx = 5, dy = 5 (both < 20 threshold)
        relation = derive_spatial_relation(box1, box2)
        assert relation is None, f"Expected None for ambiguous distance, got '{relation}'"

class TestDeriveAllRelations:
    def test_pairwise_relations(self):
        """Test that all pairwise relations are derived correctly."""
        boxes = [
            {'x': 10, 'y': 10, 'w': 20, 'h': 20, 'id': 0},
            {'x': 100, 'y': 10, 'w': 20, 'h': 20, 'id': 1},
            {'x': 10, 'y': 100, 'w': 20, 'h': 20, 'id': 2}
        ]
        relations = derive_all_relations(boxes)
        
        # Check count: 3 pairs (0-1, 0-2, 1-2)
        assert len(relations) == 3, f"Expected 3 relations, got {len(relations)}"

        # Verify specific relations based on geometry
        # Box 0 (20,20) vs Box 1 (110,20) -> Box 1 is right of Box 0
        assert any("box_0 is right of box_1" in r for r in relations)
        
        # Box 0 (20,20) vs Box 2 (20,110) -> Box 2 is below Box 0
        assert any("box_0 is below box_2" in r for r in relations)
        
        # Box 1 (110,20) vs Box 2 (20,110) -> Box 2 is left and below Box 1
        assert any("box_1 is left and below box_2" in r for r in relations)

    def test_empty_boxes(self):
        """Test with empty list."""
        relations = derive_all_relations([])
        assert relations == []

    def test_single_box(self):
        """Test with single box (no pairs)."""
        boxes = [{'x': 10, 'y': 10, 'w': 20, 'h': 20, 'id': 0}]
        relations = derive_all_relations(boxes)
        assert relations == []

class TestGeometricConsistency:
    """
    Tests that explicitly verify the core requirement:
    Derived relations MUST match the geometric reality of the coordinates.
    """
    def test_geometric_truth_verification(self):
        """
        Re-compute geometry from returned relation string and assert it matches coordinates.
        This ensures the 'deriver' is not hallucinating relations.
        """
        # Setup: Box A at (0,0), Box B at (100, 0)
        # Geometric truth: B is to the RIGHT of A.
        box_a = {'x': 0, 'y': 0, 'w': 20, 'h': 20, 'id': 'A'}
        box_b = {'x': 100, 'y': 0, 'w': 20, 'h': 20, 'id': 'B'}
        
        relation = derive_spatial_relation(box_a, box_b)
        
        # Verify the relation string contains the correct geometric fact
        assert "right of" in relation, f"Geometric truth is 'right', but derived: {relation}"
        
        # Verify the reverse is true
        reverse_relation = derive_spatial_relation(box_b, box_a)
        assert "left of" in reverse_relation, f"Geometric truth is 'left', but derived: {reverse_relation}"

    def test_geometric_truth_vertical(self):
        """Verify vertical geometric truth."""
        # Box A at (0, 100), Box B at (0, 0)
        # Geometric truth: B is ABOVE A (smaller Y is higher in image coords)
        box_a = {'x': 0, 'y': 100, 'w': 20, 'h': 20, 'id': 'A'}
        box_b = {'x': 0, 'y': 0, 'w': 20, 'h': 20, 'id': 'B'}
        
        relation = derive_spatial_relation(box_a, box_b)
        assert "above" in relation, f"Geometric truth is 'above', but derived: {relation}"

    def test_consistency_with_centroid_calculation(self):
        """Ensure relation derivation is consistent with centroid math."""
        box1 = {'x': 10, 'y': 10, 'w': 10, 'h': 10, 'id': 1} # c=(15, 15)
        box2 = {'x': 20, 'y': 10, 'w': 10, 'h': 10, 'id': 2} # c=(25, 15)
        
        c1 = calculate_centroid(box1)
        c2 = calculate_centroid(box2)
        
        # Manual check
        dx = c2[0] - c1[0] # 10
        # Since dx > 20 is false, but dx > 20 is the threshold in deriver
        # Wait, threshold is 20. dx=10. This should be None?
        # Let's adjust boxes to be clearly separated.
        
        box1 = {'x': 0, 'y': 0, 'w': 10, 'h': 10, 'id': 1} # c=(5, 5)
        box2 = {'x': 100, 'y': 0, 'w': 10, 'h': 10, 'id': 2} # c=(105, 5)
        
        c1 = calculate_centroid(box1)
        c2 = calculate_centroid(box2)
        dx = c2[0] - c1[0] # 100
        
        relation = derive_spatial_relation(box1, box2)
        
        # If dx > 20, it should be "right of"
        assert dx > 20
        assert relation == "right of"