"""
Unit test for FD calculation and exclusion logic (T013).
"""
import pytest
import numpy as np
from code.data.preprocess import calculate_fd, filter_by_fd_threshold

def test_calculate_fd_simple():
    """Test FD calculation with simple displacement data."""
    # Create dummy displacement data (6 columns: x, y, z, pitch, yaw, roll)
    # Assuming units are mm and radians
    displacements = np.array([
        [0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
        [0.1, 0.0, 0.0, 0.0, 0.0, 0.0], # Move 0.1mm in X
        [0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
    ])
    
    fd = calculate_fd(displacements)
    
    # FD is sum of absolute differences
    # Diff between row 0 and 1: 0.1 (x) + 0 + 0 + 0 + 0 + 0 = 0.1
    # Diff between row 1 and 2: 0.1 (x) + ...
    # FD is usually sum of diffs, sometimes mean. 
    # Assuming simple sum of absolute differences for this test
    assert isinstance(fd, float)
    assert fd > 0

def test_filter_by_fd_threshold():
    """Test filtering subjects based on FD threshold."""
    # Mock subject data with FD
    subjects = [
        {"id": "sub-01", "mean_fd": 0.2},
        {"id": "sub-02", "mean_fd": 0.6}, # Exceeds 0.5
        {"id": "sub-03", "mean_fd": 0.1},
    ]
    
    threshold = 0.5
    filtered = filter_by_fd_threshold(subjects, threshold)
    
    assert len(filtered) == 2
    ids = [s["id"] for s in filtered]
    assert "sub-02" not in ids
    assert "sub-01" in ids
    assert "sub-03" in ids
