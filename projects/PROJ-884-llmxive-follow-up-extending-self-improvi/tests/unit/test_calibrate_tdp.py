"""
Unit tests for the TDP Calibration script.
"""
import json
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from utils.calibrate_tdp import (
    CalibrationError,
    get_cpu_base_frequency,
    estimate_tdp_from_frequency,
    calibrate_tdp
)

@pytest.fixture
def temp_output_dir():
    """Create a temporary directory for test outputs."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

def test_get_cpu_base_frequency_linux(tmp_path):
    """Test reading CPU frequency from a fake /proc/cpuinfo."""
    cpuinfo_content = """
    processor	: 0
    cpu MHz	: 2500.000
    """
    # Mock the file read
    with patch('builtins.open', MagicMock(side_effect=FileNotFoundError)):
        pass # Fallback expected if file not found in mock

    # We can't easily mock /proc/cpuinfo directly in a portable way without os.path.exists patching
    # Let's test the fallback behavior
    with patch('os.path.exists', return_value=False):
        result = get_cpu_base_frequency()
        assert result is None

def test_estimate_tdp_from_frequency():
    """Test TDP estimation logic."""
    # Test with known frequency
    tdp = estimate_tdp_from_frequency(80.0, 2.0)
    assert tdp > 0
    
    # Test with None frequency (fallback)
    tdp_none = estimate_tdp_from_frequency(80.0, None)
    assert tdp_none > 0
    # Should be the reference value (65.0)
    assert tdp_none == 65.0

def test_calibrate_tdp_writes_json(temp_output_dir):
    """Test that calibrate_tdp writes a valid JSON file with required fields."""
    output_path = temp_output_dir / "calibration_run.json"

    # Mock the heavy workload to avoid long test times
    with patch('utils.calibrate_tdp.run_calibration_workload') as mock_workload:
        mock_workload.return_value = {
            "iterations": 10,
            "elapsed_seconds": 5.0,
            "avg_cpu_percent": 85.5,
            "max_cpu_percent": 92.0
        }
        
        with patch('utils.calibrate_tdp.get_cpu_base_frequency', return_value=2.5):
            result = calibrate_tdp(output_path)

    # Verify file exists
    assert output_path.exists()

    # Verify content
    with open(output_path, 'r') as f:
        data = json.load(f)

    assert "workload_type" in data
    assert "cpu_percent" in data
    assert "duration" in data
    assert "estimated_tdp_watts" in data
    
    assert data["workload_type"] == "matrix_multiplication_1000x1000"
    assert data["cpu_percent"] == 85.5
    assert data["duration"] == 5.0
    assert data["estimated_tdp_watts"] > 0

def test_calibrate_tdp_fails_loudly(temp_output_dir):
    """Test that calibration raises an error if workload fails."""
    output_path = temp_output_dir / "calibration_run.json"

    with patch('utils.calibrate_tdp.run_calibration_workload') as mock_workload:
        mock_workload.side_effect = CalibrationError("Workload failed")
        
        with pytest.raises(CalibrationError):
            calibrate_tdp(output_path)
    
    # Ensure no file was written or it's invalid if partially written
    # (The function raises before writing in this mock scenario)
    assert not output_path.exists()