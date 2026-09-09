"""
Unit tests for the Boundedness/Escape Time Check module (T043).
"""
import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import numpy as np
import pytest

# Import the module under test
from analysis.boundedness import (
    check_trajectory_boundedness,
    run_boundedness_validation_batch,
    save_validation_report,
    BoundednessCheckResult,
    load_trajectory_for_check
)
from utils.stability import check_boundedness


@pytest.fixture
def temp_data_dir():
    """Create a temporary directory with mock trajectory files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        data_dir = Path(tmpdir)
        # Create a bounded trajectory (all norms < 100)
        bounded_data = np.array([
            [0.0, 1.0, 1.0, 1.0],
            [1.0, 1.0, 1.0, 1.0],
            [2.0, 1.0, 1.0, 1.0]
        ])
        np.savetxt(data_dir / "trajectory_N1_sigma0.01_trial1.csv", bounded_data, delimiter=',', header='t,x,y,z', comments='')
        
        # Create an escaped trajectory (norm > 100 at some point)
        escaped_data = np.array([
            [0.0, 1.0, 1.0, 1.0],
            [1.0, 10.0, 10.0, 10.0],
            [2.0, 200.0, 200.0, 200.0]  # Norm > 100
        ])
        np.savetxt(data_dir / "trajectory_N1_sigma0.5_trial1.csv", escaped_data, delimiter=',', header='t,x,y,z', comments='')
        
        yield data_dir


def test_load_trajectory_for_check(temp_data_dir):
    """Test loading a trajectory from CSV."""
    path = temp_data_dir / "trajectory_N1_sigma0.01_trial1.csv"
    state, time = load_trajectory_for_check(path)
    
    assert state.shape[0] == 3
    assert state.shape[1] == 3  # x, y, z
    assert time[0] == 0.0
    assert time[1] == 1.0


def test_check_trajectory_boundedness_bounded(temp_data_dir):
    """Test that a bounded trajectory is correctly identified."""
    path = temp_data_dir / "trajectory_N1_sigma0.01_trial1.csv"
    result = check_trajectory_boundedness(path, threshold=100.0)
    
    assert result.is_bounded is True
    assert result.escape_time is None
    assert result.max_norm > 0
    assert result.trajectory_id == "trajectory_N1_sigma0.01_trial1"


def test_check_trajectory_boundedness_escaped(temp_data_dir):
    """Test that an escaped trajectory is correctly identified with escape time."""
    path = temp_data_dir / "trajectory_N1_sigma0.5_trial1.csv"
    result = check_trajectory_boundedness(path, threshold=100.0)
    
    assert result.is_bounded is False
    assert result.escape_time is not None
    assert result.escape_time == 2.0  # Escaped at t=2.0
    assert result.max_norm > 100.0


def test_run_boundedness_validation_batch(temp_data_dir):
    """Test running the batch check on a directory."""
    results = run_boundedness_validation_batch(data_dir=temp_data_dir, pattern="trajectory_*.csv")
    
    assert len(results) == 2
    bounded_count = sum(1 for r in results if r.is_bounded)
    escaped_count = sum(1 for r in results if not r.is_bounded)
    
    assert bounded_count == 1
    assert escaped_count == 1


def test_save_validation_report(temp_data_dir):
    """Test saving the validation report to JSON."""
    results = run_boundedness_validation_batch(data_dir=temp_data_dir, pattern="trajectory_*.csv")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "report.json"
        saved_path = save_validation_report(results, output_path)
        
        assert saved_path.exists()
        
        with open(saved_path, 'r') as f:
            report = json.load(f)
        
        assert report["total_trajectories"] == 2
        assert report["bounded_count"] == 1
        assert report["escaped_count"] == 1
        assert "details" in report
        assert len(report["details"]) == 2


def test_boundedness_check_result_to_dict():
    """Test the to_dict method of BoundednessCheckResult."""
    result = BoundednessCheckResult(
        trajectory_id="test_id",
        is_bounded=False,
        escape_time=5.0,
        max_norm=150.0,
        threshold=100.0
    )
    
    d = result.to_dict()
    
    assert d["trajectory_id"] == "test_id"
    assert d["is_bounded"] is False
    assert d["escape_time"] == 5.0
    assert d["max_norm"] == 150.0
    assert d["status"] == "ESCAPED"
    assert d["threshold"] == 100.0
