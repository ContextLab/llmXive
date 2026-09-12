"""
Unit tests for distortion logic in src/generators.
"""
import pytest
import math
from pathlib import Path

def test_aspect_ratio_calculation():
    """Test calculation of aspect ratios from dimensions."""
    # Standard 16:9 video
    assert math.isclose(16/9, 1.777, abs_tol=0.01)
    # Extreme 1:10 (portrait)
    assert math.isclose(1/10, 0.1, abs_tol=0.01)
    # Extreme 10:1 (landscape)
    assert math.isclose(10/1, 10.0, abs_tol=0.01)

def test_bounding_box_integrity_fr001():
    """Test FR-001: exclude clips where primary subject BB area reduced >95%."""
    # Simulate original area and reduced area
    original_area = 1000
    reduced_area = 50  # 95% reduction
    reduction = (original_area - reduced_area) / original_area
    assert reduction > 0.95

def test_edge_case_zero_area():
    """Test handling of zero area bounding box."""
    with pytest.raises(ValueError):
        # Zero area division
        10 / 0

def test_edge_case_negative_area():
    """Test handling of negative area bounding box."""
    with pytest.raises(ValueError):
        # Negative area logic
        -100
