"""
Unit tests for code/data/preprocess.py
"""
import pytest
import pandas as pd
import numpy as np
from unittest.mock import MagicMock, patch
from pathlib import Path

# Import the functions to test
from code.data.preprocess import calculate_fd, check_motion_threshold, MOTION_THRESHOLD_MM, MOTION_THRESHOLD_DEG

def test_calculate_fd_no_confounds():
    """Test FD calculation with missing columns."""
    confounds = pd.DataFrame({"other_col": [1, 2, 3]})
    fd = calculate_fd(confounds)
    assert fd == 0.0

def test_calculate_fd_basic():
    """Test FD calculation with valid motion parameters."""
    # Create dummy motion data
    # trans_x, trans_y, trans_z, rot_x, rot_y, rot_z
    data = {
        "trans_x": [0, 0.1, 0.2],
        "trans_y": [0, 0.1, 0.2],
        "trans_z": [0, 0.1, 0.2],
        "rot_x": [0, 0.01, 0.02],
        "rot_y": [0, 0.01, 0.02],
        "rot_z": [0, 0.01, 0.02]
    }
    confounds = pd.DataFrame(data)
    fd = calculate_fd(confounds)
    # Manual calculation:
    # diff = [0.1, 0.1] for each trans, [0.01, 0.01] for rot
    # abs diff sum per frame: (0.1+0.1+0.1) + (0.01+0.01+0.01) = 0.33 per frame
    # mean of 2 frames = 0.33
    assert abs(fd - 0.33) < 0.01

def test_check_motion_threshold_pass():
    """Test motion check when within limits."""
    data = {
        "trans_x": [0, 1, 2], # max ~3.7mm (sqrt(1+4+4) = 3) -> wait, max of sqrt sums
        "trans_y": [0, 1, 2],
        "trans_z": [0, 1, 2],
        "rot_x": [0, 0.01, 0.02],
        "rot_y": [0, 0.01, 0.02],
        "rot_z": [0, 0.01, 0.02]
    }
    # Max trans: sqrt(2^2 + 2^2 + 2^2) = sqrt(12) ~ 3.46 -> This should fail?
    # Let's make it smaller.
    data = {
        "trans_x": [0, 1, 1],
        "trans_y": [0, 0, 0],
        "trans_z": [0, 0, 0],
        "rot_x": [0, 0, 0],
        "rot_y": [0, 0, 0],
        "rot_z": [0, 0, 0]
    }
    confounds = pd.DataFrame(data)
    is_excluded, max_trans, max_rot_deg = check_motion_threshold(confounds)
    assert not is_excluded
    assert max_trans < MOTION_THRESHOLD_MM

def test_check_motion_threshold_fail_translation():
    """Test motion check when translation exceeds limit."""
    # Create a frame with 4mm translation
    data = {
        "trans_x": [0, 4, 0],
        "trans_y": [0, 0, 0],
        "trans_z": [0, 0, 0],
        "rot_x": [0, 0, 0],
        "rot_y": [0, 0, 0],
        "rot_z": [0, 0, 0]
    }
    confounds = pd.DataFrame(data)
    is_excluded, max_trans, max_rot_deg = check_motion_threshold(confounds)
    assert is_excluded
    assert max_trans >= MOTION_THRESHOLD_MM

def test_check_motion_threshold_fail_rotation():
    """Test motion check when rotation exceeds limit."""
    # 3 degrees = 0.0523 rad. Let's use 0.06 rad (~3.4 deg)
    data = {
        "trans_x": [0, 0, 0],
        "trans_y": [0, 0, 0],
        "trans_z": [0, 0, 0],
        "rot_x": [0, 0.06, 0],
        "rot_y": [0, 0, 0],
        "rot_z": [0, 0, 0]
    }
    confounds = pd.DataFrame(data)
    is_excluded, max_trans, max_rot_deg = check_motion_threshold(confounds)
    assert is_excluded
    # Convert back to deg to check
    assert max_rot_deg >= MOTION_THRESHOLD_DEG
