"""
Tests for the feasibility verification script (T037).
"""
import os
import json
import tempfile
from pathlib import Path
import pytest

# Mock the run_pipeline_subset import to avoid heavy dependencies in unit tests
import sys
from unittest.mock import patch, MagicMock

# We will test the logic of verify_feasibility_report directly by importing it
# We need to mock the imports that verify_feasibility.py expects if we run it standalone
# But here we test the core logic by importing the function after mocking dependencies

def test_verify_feasibility_report_missing_file():
    """Test that verify returns False when report file is missing."""
    from code.verify_feasibility import verify_feasibility_report
    
    with tempfile.TemporaryDirectory() as tmpdir:
        fake_path = Path(tmpdir) / "missing_report.json"
        result = verify_feasibility_report(fake_path)
        assert result is False

def test_verify_feasibility_report_invalid_json():
    """Test that verify returns False when JSON is invalid."""
    from code.verify_feasibility import verify_feasibility_report
    
    with tempfile.TemporaryDirectory() as tmpdir:
        fake_path = Path(tmpdir) / "invalid.json"
        fake_path.write_text("not valid json {{{")
        result = verify_feasibility_report(fake_path)
        assert result is False

def test_verify_feasibility_report_missing_key():
    """Test that verify returns False when peak_memory_mb is missing."""
    from code.verify_feasibility import verify_feasibility_report
    
    with tempfile.TemporaryDirectory() as tmpdir:
        fake_path = Path(tmpdir) / "missing_key.json"
        fake_path.write_text(json.dumps({"other_key": 123}))
        result = verify_feasibility_report(fake_path)
        assert result is False

def test_verify_feasibility_report_success():
    """Test that verify returns True when memory is under limit."""
    from code.verify_feasibility import verify_feasibility_report
    
    with tempfile.TemporaryDirectory() as tmpdir:
        fake_path = Path(tmpdir) / "success.json"
        # 6000 MB is < 7168 MB
        fake_path.write_text(json.dumps({"peak_memory_mb": 6000.5, "runtime_seconds": 100}))
        result = verify_feasibility_report(fake_path)
        assert result is True

def test_verify_feasibility_report_failure():
    """Test that verify returns False when memory exceeds limit."""
    from code.verify_feasibility import verify_feasibility_report
    
    with tempfile.TemporaryDirectory() as tmpdir:
        fake_path = Path(tmpdir) / "failure.json"
        # 8000 MB is > 7168 MB
        fake_path.write_text(json.dumps({"peak_memory_mb": 8000.0, "runtime_seconds": 100}))
        result = verify_feasibility_report(fake_path)
        assert result is False

def test_verify_feasibility_report_exact_boundary():
    """Test behavior at exactly 7168 MB (should fail as it must be < 7GB)."""
    from code.verify_feasibility import verify_feasibility_report
    
    with tempfile.TemporaryDirectory() as tmpdir:
        fake_path = Path(tmpdir) / "boundary.json"
        fake_path.write_text(json.dumps({"peak_memory_mb": 7168.0}))
        result = verify_feasibility_report(fake_path)
        # The condition is peak_memory_mb < RAM_THRESHOLD_MB
        # 7168.0 < 7168 is False
        assert result is False

def test_verify_feasibility_report_just_under_boundary():
    """Test behavior just under 7168 MB."""
    from code.verify_feasibility import verify_feasibility_report
    
    with tempfile.TemporaryDirectory() as tmpdir:
        fake_path = Path(tmpdir) / "under.json"
        fake_path.write_text(json.dumps({"peak_memory_mb": 7167.9}))
        result = verify_feasibility_report(fake_path)
        assert result is True