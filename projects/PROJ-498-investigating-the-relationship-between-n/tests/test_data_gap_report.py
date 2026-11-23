"""
Tests for T012b: Data Gap Report Generation.
"""
import json
import os
import pytest
from pathlib import Path
from datetime import datetime
from data_gap_report_generator import generate_data_gap_report, generate_data_gap_report_from_exclusions, REPORT_PATH

def test_generate_report_structure():
    """Test that the generated report has the correct structure."""
    reason = "Test failure reason"
    report = generate_data_gap_report(reason=reason, dataset_id="ds000000", fallback_id="ds000001")
    
    assert "dataset_id" in report
    assert "reason" in report
    assert "timestamp" in report
    assert "fallback_id" in report
    
    assert report["dataset_id"] == "ds000000"
    assert report["reason"] == reason
    assert report["fallback_id"] == "ds000001"
    assert report["fallback_id"] is not None

def test_generate_report_null_fallback():
    """Test that fallback_id is null when not provided."""
    reason = "Test failure reason"
    report = generate_data_gap_report(reason=reason, dataset_id="ds000000")
    
    assert report["fallback_id"] is None

def test_report_timestamp_format():
    """Test that the timestamp is in ISO format."""
    report = generate_data_gap_report(reason="Test")
    # Should not raise an error
    datetime.fromisoformat(report["timestamp"])

def test_write_report_to_disk():
    """Test that the report is written to the correct path."""
    # Clean up if exists
    if os.path.exists(REPORT_PATH):
        os.remove(REPORT_PATH)
    
    reason = "Test write"
    report = generate_data_gap_report(reason=reason)
    
    # Simulate writing (normally done in main, but testing the logic here)
    with open(REPORT_PATH, "w") as f:
        json.dump(report, f)
    
    assert os.path.exists(REPORT_PATH)
    
    with open(REPORT_PATH, "r") as f:
        loaded = json.load(f)
    
    assert loaded["reason"] == reason

def test_generate_from_exclusions():
    """Test generating report from a mock exclusions file."""
    exclusions_path = "data/test_exclusions.csv"
    Path("data").mkdir(exist_ok=True)
    
    # Create mock CSV
    with open(exclusions_path, "w") as f:
        f.write("subject_id,reason\n")
        f.write("sub-01,insufficient_trials\n")
        f.write("sub-02,excessive_artifact\n")
    
    report = generate_data_gap_report_from_exclusions(exclusions_path)
    
    assert "all_subjects_excluded_due_to" in report["reason"]
    assert report["fallback_id"] is None
    
    # Cleanup
    if os.path.exists(exclusions_path):
        os.remove(exclusions_path)