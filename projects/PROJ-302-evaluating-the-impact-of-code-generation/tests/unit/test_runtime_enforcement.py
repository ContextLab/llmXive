"""
Unit tests for runtime enforcement functionality.
"""

import os
import sys
import json
import time
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from utils.config import RUNTIME_REPORT_PATH, MAX_RUNTIME_SECONDS
from main import check_runtime_gate, write_runtime_report

class TestRuntimeEnforcement:
    """Test cases for runtime enforcement."""

    def test_write_runtime_report_creates_file(self, tmp_path):
        """Test that write_runtime_report creates the expected file."""
        # Mock the RUNTIME_REPORT_PATH to use a temporary directory
        with patch('main.RUNTIME_REPORT_PATH', tmp_path / "runtime_report.json"):
            start_time = time.time() - 10
            end_time = time.time()
            
            write_runtime_report(start_time, end_time, True)
            
            # Check file exists
            assert (tmp_path / "runtime_report.json").exists()
            
            # Check content
            with open(tmp_path / "runtime_report.json", 'r') as f:
                report = json.load(f)
            
            assert "start_time" in report
            assert "end_time" in report
            assert "elapsed_seconds" in report
            assert "max_allowed_seconds" in report
            assert "within_limit" in report
            assert "success" in report
            assert report["success"] is True
            assert report["within_limit"] is True

    def test_write_runtime_report_within_limit(self, tmp_path):
        """Test runtime report when within limit."""
        with patch('main.RUNTIME_REPORT_PATH', tmp_path / "runtime_report.json"):
            start_time = time.time() - 10
            end_time = time.time()
            
            write_runtime_report(start_time, end_time, True)
            
            with open(tmp_path / "runtime_report.json", 'r') as f:
                report = json.load(f)
            
            assert report["within_limit"] is True

    def test_write_runtime_report_exceeds_limit(self, tmp_path):
        """Test runtime report when exceeding limit."""
        with patch('main.RUNTIME_REPORT_PATH', tmp_path / "runtime_report.json"):
            # Simulate a long runtime
            start_time = time.time() - (MAX_RUNTIME_SECONDS + 100)
            end_time = time.time()
            
            write_runtime_report(start_time, end_time, False)
            
            with open(tmp_path / "runtime_report.json", 'r') as f:
                report = json.load(f)
            
            assert report["within_limit"] is False
            assert report["success"] is False

    def test_check_runtime_gate_within_limit(self):
        """Test check_runtime_gate when within limit."""
        start_time = time.time() - 10
        assert check_runtime_gate(start_time) is True

    def test_check_runtime_gate_exceeds_limit(self):
        """Test check_runtime_gate when exceeding limit."""
        start_time = time.time() - (MAX_RUNTIME_SECONDS + 100)
        assert check_runtime_gate(start_time) is False

    def test_runtime_report_path_is_correct(self):
        """Test that RUNTIME_REPORT_PATH points to the correct location."""
        expected_path = Path(__file__).parent.parent.parent / "code" / ".." / "data" / "processed" / "runtime_report.json"
        # Normalize paths
        assert str(RUNTIME_REPORT_PATH) == str(expected_path.resolve())