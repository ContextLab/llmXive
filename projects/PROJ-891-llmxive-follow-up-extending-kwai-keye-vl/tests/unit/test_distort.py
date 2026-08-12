"""Unit tests for video distortion logic.

This module contains tests for:
- Aspect ratio calculation logic
- Bounding box integrity checks (FR-001)
- Aspect ratio tolerance verification
"""
import pytest
import math


def calculate_aspect_ratio(width: int, height: int) -> float:
    """Calculate the aspect ratio of a video frame.

    Args:
        width: Frame width in pixels.
        height: Frame height in pixels.

    Returns:
        The aspect ratio (width / height).
    """
    if height == 0:
        raise ValueError("Height cannot be zero")
    return width / height


def check_bounding_box_integrity(original_area: float, reduced_area: float) -> bool:
    """Check if a bounding box meets FR-001 integrity requirements.

    FR-001: Exclude clips where primary subject bounding box area is reduced >95%.
    This means the remaining area must be at least 5% of the original.

    Args:
        original_area: The area of the bounding box before distortion.
        reduced_area: The area of the bounding box after distortion.

    Returns:
        True if the bounding box is valid (area >= 5% of original), False otherwise.
    """
    if original_area <= 0:
        raise ValueError("Original area must be positive")
    if reduced_area < 0:
        raise ValueError("Reduced area cannot be negative")

    retention_ratio = reduced_area / original_area
    # Valid if at least 5% of the original area remains
    return retention_ratio >= 0.05


def verify_aspect_ratio_tolerance(target_ratio: float, actual_ratio: float, tolerance: float = 0.001) -> bool:
    """Verify if an actual aspect ratio is within tolerance of the target.

    Args:
        target_ratio: The expected aspect ratio.
        actual_ratio: The measured aspect ratio.
        tolerance: Maximum allowed relative deviation (default 0.1% = 0.001).

    Returns:
        True if within tolerance, False otherwise.
    """
    if target_ratio == 0:
        raise ValueError("Target ratio cannot be zero")
    if target_ratio < 0 or actual_ratio < 0:
        raise ValueError("Ratios must be non-negative")

    relative_deviation = abs(actual_ratio - target_ratio) / target_ratio
    return relative_deviation <= tolerance


def test_aspect_ratio_calculation():
    """Test aspect ratio calculation logic."""
    # Standard 1080p
    width = 1920
    height = 1080
    expected_ratio = width / height
    calculated_ratio = calculate_aspect_ratio(width, height)
    assert math.isclose(calculated_ratio, expected_ratio, rel_tol=1e-9)

    # Test extreme ratios
    assert math.isclose(calculate_aspect_ratio(1920, 192), 10.0, rel_tol=1e-9)  # 10:1
    assert math.isclose(calculate_aspect_ratio(192, 1920), 0.1, rel_tol=1e-9)   # 1:10
    assert math.isclose(calculate_aspect_ratio(1920, 96), 20.0, rel_tol=1e-9)   # 20:1
    assert math.isclose(calculate_aspect_ratio(96, 1920), 0.05, rel_tol=1e-9)   # 1:20

    # Test error cases
    with pytest.raises(ValueError):
        calculate_aspect_ratio(1920, 0)


def test_bounding_box_area_reduction():
    """Test bounding box integrity check (FR-001)."""
    original_area = 1000.0

    # Case 1: Area reduced > 95% (remaining < 5%) -> Invalid
    reduced_area = 40.0  # 4% remaining
    assert not check_bounding_box_integrity(original_area, reduced_area)

    # Case 2: Exactly at threshold (5% remaining) -> Valid
    reduced_area = 50.0  # 5% remaining
    assert check_bounding_box_integrity(original_area, reduced_area)

    # Case 3: Area reduced < 95% (remaining > 5%) -> Valid
    reduced_area = 100.0  # 10% remaining
    assert check_bounding_box_integrity(original_area, reduced_area)

    # Case 4: No reduction -> Valid
    reduced_area = 1000.0
    assert check_bounding_box_integrity(original_area, reduced_area)

    # Error cases
    with pytest.raises(ValueError):
        check_bounding_box_integrity(0, 100)
    with pytest.raises(ValueError):
        check_bounding_box_integrity(100, -10)


def test_aspect_ratio_tolerance():
    """Test aspect ratio tolerance verification (±0.1%)."""
    target_ratio = 10.0
    tolerance = 0.001  # 0.1%

    # Case 1: Within tolerance (0.0005% deviation)
    actual_ratio = 10.00005
    assert verify_aspect_ratio_tolerance(target_ratio, actual_ratio, tolerance)

    # Case 2: Exactly at tolerance boundary
    # 0.1% of 10.0 is 0.01, so 10.01 should be at the boundary
    actual_ratio = 10.01
    assert verify_aspect_ratio_tolerance(target_ratio, actual_ratio, tolerance)

    # Case 3: Out of tolerance (0.2% deviation)
    actual_ratio = 10.02
    assert not verify_aspect_ratio_tolerance(target_ratio, actual_ratio, tolerance)

    # Case 4: Very small ratios
    target_ratio = 0.1
    actual_ratio = 0.1001  # 0.1% deviation
    assert verify_aspect_ratio_tolerance(target_ratio, actual_ratio, tolerance)

    # Error cases
    with pytest.raises(ValueError):
        verify_aspect_ratio_tolerance(0, 1.0)
    with pytest.raises(ValueError):
        verify_aspect_ratio_tolerance(1.0, -1.0)


def test_extreme_aspect_ratio_cases():
    """Test specific extreme aspect ratios mentioned in the task description."""
    ratios = [
        (192, 1920, 0.1, "1:10"),
        (1920, 192, 10.0, "10:1"),
        (96, 1920, 0.05, "1:20"),
        (1920, 96, 20.0, "20:1"),
    ]

    for width, height, expected, name in ratios:
        calculated = calculate_aspect_ratio(width, height)
        assert math.isclose(calculated, expected, rel_tol=1e-9), f"Failed for {name}"

        # Verify tolerance check passes for exact match
        assert verify_aspect_ratio_tolerance(expected, calculated)