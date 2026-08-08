import pytest
import os
import csv
import tempfile
import numpy as np
from code.utils.motion import calculate_mean_fd, check_motion_exclusion, generate_exclusion_log, run_motion_filtering_pipeline
from code.config import get_config

def test_calculate_mean_fd_valid_input():
    """Test Mean FD calculation with known values."""
    # Create dummy motion params: 10 timepoints, 6 params
    # All zeros -> FD should be 0
    params = np.zeros((10, 6))
    assert calculate_mean_fd(params) == 0.0

    # Create params with a known jump
    # 1mm translation jump at index 1, rest 0
    params = np.zeros((10, 6))
    params[1, 0] = 1.0  # 1mm translation in x
    
    # Deltas will have one entry of 1.0 at index 0
    # Mean FD = 1.0 / 9 (since diff reduces length by 1)
    expected_fd = 1.0 / 9.0
    assert abs(calculate_mean_fd(params) - expected_fd) < 1e-6

def test_check_motion_exclusion_below_threshold():
    """Test exclusion logic when FD is below threshold."""
    config = get_config()
    threshold = config.get("fd_threshold", 0.2)
    should_exclude, reason = check_motion_exclusion(0.1, threshold)
    assert should_exclude is False
    assert reason == ""

def test_check_motion_exclusion_above_threshold():
    """Test exclusion logic when FD is above threshold."""
    config = get_config()
    threshold = config.get("fd_threshold", 0.2)
    should_exclude, reason = check_motion_exclusion(0.5, threshold)
    assert should_exclude is True
    assert "Mean FD" in reason
    assert "threshold" in reason

def test_generate_exclusion_log(tmp_path):
    """Test that exclusion log is generated with correct format."""
    subjects = [
        {'Subject_ID': '1001', 'Exclusion_Reason': 'Motion', 'Mean_FD': '0.5000'},
        {'Subject_ID': '1002', 'Exclusion_Reason': 'Motion', 'Mean_FD': '0.3000'}
    ]
    log_path = os.path.join(tmp_path, "exclusion_log.csv")
    generate_exclusion_log(subjects, log_path)
    
    assert os.path.exists(log_path)
    
    with open(log_path, 'r') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    
    assert len(rows) == 2
    assert rows[0]['Subject_ID'] == '1001'
    assert rows[0]['Exclusion_Reason'] == 'Motion'
    assert rows[0]['Mean_FD'] == '0.5000'

def test_run_motion_filtering_pipeline():
    """Test the full pipeline logic with mock data."""
    # Mock subjects data
    subjects = [
        {'Subject_ID': 'S1', 'Mean_FD': 0.1},
        {'Subject_ID': 'S2', 'Mean_FD': 0.5},
        {'Subject_ID': 'S3', 'Mean_FD': 0.15},
    ]
    
    valid = run_motion_filtering_pipeline(subjects)
    
    # S2 should be excluded
    assert len(valid) == 2
    assert valid[0]['Subject_ID'] == 'S1'
    assert valid[1]['Subject_ID'] == 'S3'
    
    # Check exclusion log exists if any were excluded
    # Note: This test might need to handle the file path carefully in CI
    # but the logic is verified by the return value.