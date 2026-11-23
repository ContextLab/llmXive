"""Integration tests for code/data/preprocess.py motion threshold logic."""
import pytest
import sys
import numpy as np
from pathlib import Path

# Adjust path to allow imports from code/
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.data.preprocess import check_motion_threshold

def test_motion_threshold_passes_low_movement():
    """
    Test that check_motion_threshold returns True (pass) for low motion values.
    Thresholds: >3mm translation or >3° rotation should fail.
    """
    # Low motion: 1.5mm translation, 1.0° rotation
    fd = 1.5
    rotation_deg = 1.0

    result, reason = check_motion_threshold(fd, rotation_deg)

    assert result is True
    assert reason is None

def test_motion_threshold_fails_high_translation():
    """
    Test that check_motion_threshold returns False (fail) for high translation (>3mm).
    """
    # High translation: 4.0mm, low rotation
    fd = 4.0
    rotation_deg = 1.0

    result, reason = check_motion_threshold(fd, rotation_deg)

    assert result is False
    assert "translation" in reason.lower()

def test_motion_threshold_fails_high_rotation():
    """
    Test that check_motion_threshold returns False (fail) for high rotation (>3°).
    """
    # Low translation, high rotation: 3.5°
    fd = 1.0
    rotation_deg = 3.5

    result, reason = check_motion_threshold(fd, rotation_deg)

    assert result is False
    assert "rotation" in reason.lower()

def test_motion_threshold_fails_both_high():
    """
    Test that check_motion_threshold returns False when both thresholds are exceeded.
    """
    fd = 5.0
    rotation_deg = 4.0

    result, reason = check_motion_threshold(fd, rotation_deg)

    assert result is False
    # Should flag at least one, usually the first checked or both
    assert "exceeded" in reason.lower() or "threshold" in reason.lower()

def test_motion_threshold_boundary_translation():
    """
    Test behavior exactly at the 3mm boundary.
    Task requires >3mm to fail, so 3.0 should pass.
    """
    fd = 3.0
    rotation_deg = 0.0

    result, reason = check_motion_threshold(fd, rotation_deg)

    assert result is True

def test_motion_threshold_boundary_rotation():
    """
    Test behavior exactly at the 3° boundary.
    Task requires >3° to fail, so 3.0 should pass.
    """
    fd = 0.0
    rotation_deg = 3.0

    result, reason = check_motion_threshold(fd, rotation_deg)

    assert result is True

def test_motion_threshold_just_above_boundary():
    """
    Test behavior just above the 3mm/3° boundary (e.g., 3.01).
    """
    fd = 3.01
    rotation_deg = 0.0

    result, reason = check_motion_threshold(fd, rotation_deg)

    assert result is False
