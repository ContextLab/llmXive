"""
Unit tests for code/data/preprocess.py
"""
import pytest
import numpy as np
from pathlib import Path
from code.data.preprocess import check_motion_threshold, calculate_fd

def test_check_motion_threshold_pass():
    """Test that motion below threshold returns True (pass)"""
    # Simulate motion metrics below threshold (3mm translation, 3deg rotation)
    motion_metrics = {
        'mean_trans_x': 1.0,
        'mean_trans_y': 1.0,
        'mean_trans_z': 1.0,
        'mean_rot_x': 1.0,
        'mean_rot_y': 1.0,
        'mean_rot_z': 1.0
    }
    result = check_motion_threshold(motion_metrics)
    assert result is True

def test_check_motion_threshold_fail_translation():
    """Test that motion above threshold in translation returns False (fail)"""
    # Simulate motion metrics with high translation
    motion_metrics = {
        'mean_trans_x': 4.0,  # Exceeds 3mm threshold
        'mean_trans_y': 1.0,
        'mean_trans_z': 1.0,
        'mean_rot_x': 1.0,
        'mean_rot_y': 1.0,
        'mean_rot_z': 1.0
    }
    result = check_motion_threshold(motion_metrics)
    assert result is False

def test_check_motion_threshold_fail_rotation():
    """Test that motion above threshold in rotation returns False (fail)"""
    # Simulate motion metrics with high rotation
    motion_metrics = {
        'mean_trans_x': 1.0,
        'mean_trans_y': 1.0,
        'mean_trans_z': 1.0,
        'mean_rot_x': 4.0,  # Exceeds 3deg threshold
        'mean_rot_y': 1.0,
        'mean_rot_z': 1.0
    }
    result = check_motion_threshold(motion_metrics)
    assert result is False

def test_calculate_fd_from_displacements():
    """Test FD calculation from displacement array"""
    # Create sample displacement array (6 columns: trans_x, trans_y, trans_z, rot_x, rot_y, rot_z)
    displacements = np.array([
        [0.1, 0.1, 0.1, 0.01, 0.01, 0.01],
        [0.2, 0.2, 0.2, 0.02, 0.02, 0.02],
        [0.3, 0.3, 0.3, 0.03, 0.03, 0.03]
    ])
    
    fd = calculate_fd(displacements)
    
    # FD should be positive and finite
    assert fd > 0
    assert np.isfinite(fd)
