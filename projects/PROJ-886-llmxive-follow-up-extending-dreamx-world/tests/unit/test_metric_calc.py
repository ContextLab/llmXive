import pytest
import numpy as np
import os
import sys
from pathlib import Path
import tempfile
import json

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "code"))

from pipeline.evaluate import (
    calculate_metrics,
    calculate_procrustes_alignment,
    calculate_rotation_error,
    write_metrics_to_csv
)

def create_dummy_pose(R=None, t=None):
    """Create a dummy pose (R, t) tuple."""
    if R is None:
        R = np.eye(3)
    if t is None:
        t = np.zeros(3)
    return (R, t)

def test_procrustes_alignment_identity():
    """Test that aligning identical poses returns identity transformation."""
    poses = [create_dummy_pose(np.eye(3), np.array([i, 0, 0])) for i in range(5)]
    
    aligned, scale, rot_err = calculate_procrustes_alignment(poses, poses)
    
    # Scale should be ~1.0
    assert np.isclose(scale, 1.0, atol=0.01)
    # Rotation error should be ~0
    assert np.isclose(rot_err, 0.0, atol=0.1)
    
    # Aligned poses should be very close to original
    for (gt_r, gt_t), (aligned_r, aligned_t) in zip(poses, aligned):
        assert np.allclose(gt_r, aligned_r, atol=1e-5)
        assert np.allclose(gt_t, aligned_t, atol=1e-5)

def test_procrustes_alignment_with_scale():
    """Test alignment with scaled poses."""
    gt_poses = [create_dummy_pose(np.eye(3), np.array([i, 0, 0])) for i in range(5)]
    pred_poses = [create_dummy_pose(np.eye(3), np.array([i * 2.0, 0, 0])) for i in range(5)]
    
    aligned, scale, rot_err = calculate_procrustes_alignment(gt_poses, pred_poses)
    
    # Scale should be ~0.5 (pred is 2x larger)
    assert np.isclose(scale, 0.5, atol=0.01)
    # Rotation error should be ~0
    assert np.isclose(rot_err, 0.0, atol=0.1)

def test_rotation_error_zero():
    """Test rotation error calculation for identical rotations."""
    R = np.eye(3)
    error = calculate_rotation_error(R, R)
    assert np.isclose(error, 0.0, atol=0.01)

def test_rotation_error_90_degrees():
    """Test rotation error calculation for 90 degree rotation."""
    R1 = np.eye(3)
    # 90 degree rotation around Z
    R2 = np.array([
        [0, -1, 0],
        [1, 0, 0],
        [0, 0, 1]
    ])
    error = calculate_rotation_error(R1, R2)
    assert np.isclose(error, 90.0, atol=0.1)

def test_calculate_metrics_success():
    """Test full metric calculation pipeline."""
    gt_poses = [create_dummy_pose(np.eye(3), np.array([i, 0, 0])) for i in range(5)]
    pred_poses = [create_dummy_pose(np.eye(3), np.array([i, 0, 0])) for i in range(5)]
    
    metrics = calculate_metrics(
        gt_poses, pred_poses, 
        trajectory_id="test_001", 
        model_name="TestModel"
    )
    
    assert metrics["trajectory_id"] == "test_001"
    assert metrics["model"] == "TestModel"
    assert metrics["convergence"] is True
    assert metrics["sfm_failure_reason"] == ""
    assert metrics["mae_position"] is not None
    assert metrics["mae_rotation"] is not None
    assert np.isclose(metrics["mae_position"], 0.0, atol=0.01)
    assert np.isclose(metrics["mae_rotation"], 0.0, atol=0.1)

def test_calculate_metrics_empty():
    """Test metric calculation with empty trajectories."""
    metrics = calculate_metrics(
        [], [], 
        trajectory_id="test_002", 
        model_name="TestModel"
    )
    
    assert metrics["trajectory_id"] == "test_002"
    assert metrics["convergence"] is False
    assert metrics["mae_position"] is None
    assert metrics["mae_rotation"] is None
    assert metrics["sfm_failure_reason"] == "empty_trajectory"

def test_write_metrics_to_csv():
    """Test writing metrics to CSV."""
    metrics_list = [
        {
            "trajectory_id": "test_001",
            "model": "TestModel",
            "mae_position": 0.5,
            "mae_rotation": 1.2,
            "convergence": True,
            "sfm_failure_reason": ""
        },
        {
            "trajectory_id": "test_002",
            "model": "TestModel",
            "mae_position": None,
            "mae_rotation": None,
            "convergence": False,
            "sfm_failure_reason": "insufficient_features"
        }
    ]
    
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as f:
        temp_path = f.name
    
    try:
        write_metrics_to_csv(metrics_list, temp_path)
        
        # Read back and verify
        with open(temp_path, 'r') as f:
            content = f.read()
        
        assert "trajectory_id,model,mae_position,mae_rotation,convergence,sfm_failure_reason" in content
        assert "test_001" in content
        assert "test_002" in content
        assert "insufficient_features" in content
        # Check that None values are written as empty strings
        assert ",," in content  # Two consecutive commas for null values
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)

def test_metrics_csv_schema():
    """Verify the CSV schema matches the specification."""
    metrics_list = [
        {
            "trajectory_id": "test_001",
            "model": "DreamXLite",
            "mae_position": 0.5,
            "mae_rotation": 1.2,
            "convergence": True,
            "sfm_failure_reason": ""
        }
    ]
    
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as f:
        temp_path = f.name
    
    try:
        write_metrics_to_csv(metrics_list, temp_path)
        
        with open(temp_path, 'r') as f:
            reader = csv.DictReader(f)
            headers = reader.fieldnames
            
            expected_headers = [
                "trajectory_id", "model", "mae_position", "mae_rotation",
                "convergence", "sfm_failure_reason"
            ]
            
            assert headers == expected_headers
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)

import csv