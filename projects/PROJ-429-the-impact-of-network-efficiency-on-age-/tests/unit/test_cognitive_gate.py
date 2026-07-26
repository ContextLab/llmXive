"""
Unit tests for code/stats/cognitive_gate.py (T023a).
"""
import json
import tempfile
from pathlib import Path

import pytest

from stats.cognitive_gate import (
    check_cognitive_availability,
    load_download_report,
    write_status_file,
)

def test_check_cognitive_availability_blocked():
    """Test that full missing cognitive count results in BLOCKED status."""
    report = {
        "total_count": 100,
        "missing_cognitive_count": 100,
        "valid_count": 0,
        "invalid_instrument_count": 0,
        "records": [],
    }
    is_available, reason = check_cognitive_availability(report)
    assert is_available is False
    assert "No linked cognitive data" in reason

def test_check_cognitive_availability_available():
    """Test that partial missing cognitive count results in AVAILABLE status."""
    report = {
        "total_count": 100,
        "missing_cognitive_count": 80,
        "valid_count": 20,
        "invalid_instrument_count": 0,
        "records": [],
    }
    is_available, reason = check_cognitive_availability(report)
    assert is_available is True
    assert "available" in reason.lower()

def test_check_cognitive_availability_zero_total():
    """Test behavior when total_count is 0."""
    report = {
        "total_count": 0,
        "missing_cognitive_count": 0,
        "valid_count": 0,
        "invalid_instrument_count": 0,
        "records": [],
    }
    is_available, reason = check_cognitive_availability(report)
    assert is_available is False
    assert "zero" in reason.lower()

def test_load_download_report_valid(tmp_path):
    """Test loading a valid JSON report."""
    report_data = {"total_count": 10, "missing_cognitive_count": 0}
    report_file = tmp_path / "download_report.json"
    report_file.write_text(json.dumps(report_data))

    loaded = load_download_report(report_file)
    assert loaded == report_data

def test_load_download_report_missing(tmp_path):
    """Test loading a non-existent file raises FileNotFoundError."""
    with pytest.raises(FileNotFoundError):
        load_download_report(tmp_path / "non_existent.json")

def test_write_status_file(tmp_path):
    """Test writing status file creates correct JSON."""
    status_file = tmp_path / "cognitive_status.json"
    write_status_file(status_file, "BLOCKED", "Test reason")

    assert status_file.exists()
    with open(status_file, "r") as f:
        data = json.load(f)

    assert data["status"] == "BLOCKED"
    assert data["reason"] == "Test reason"
