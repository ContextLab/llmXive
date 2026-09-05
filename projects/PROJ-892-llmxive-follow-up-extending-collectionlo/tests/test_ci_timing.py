import json
import os
import sys
from pathlib import Path
import pytest

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from main import record_ci_timing

def test_record_ci_timing_creates_file():
    """Test that record_ci_timing creates the ci_report.json file."""
    # Remove existing file if it exists
    output_path = "data/ci_report.json"
    if os.path.exists(output_path):
        os.remove(output_path)
    
    # Run the function
    result = record_ci_timing()
    
    # Check that file was created
    assert os.path.exists(output_path), f"File {output_path} was not created"
    
    # Check file contents
    with open(output_path, 'r') as f:
        report = json.load(f)
    
    assert "start_time" in report
    assert "end_time" in report
    assert "duration_seconds" in report
    assert "status" in report
    assert report["status"] == "completed"
    assert "pipeline_version" in report
    assert "environment" in report
    
    # Clean up
    os.remove(output_path)

def test_record_ci_timing_returns_valid_data():
    """Test that record_ci_timing returns valid data structure."""
    result = record_ci_timing()
    
    assert isinstance(result, dict)
    assert "start_time" in result
    assert "end_time" in result
    assert "duration_seconds" in result
    assert isinstance(result["duration_seconds"], (int, float))
    assert result["duration_seconds"] >= 0

def test_record_ci_timing_idempotent():
    """Test that calling record_ci_timing multiple times works correctly."""
    # First call
    result1 = record_ci_timing()
    
    # Second call
    result2 = record_ci_timing()
    
    # Both should have valid structure
    assert "start_time" in result1
    assert "start_time" in result2
    
    # Duration should be positive
    assert result1["duration_seconds"] > 0
    assert result2["duration_seconds"] > 0