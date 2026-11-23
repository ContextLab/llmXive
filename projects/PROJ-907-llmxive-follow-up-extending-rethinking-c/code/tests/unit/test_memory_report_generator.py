"""
Unit tests for the memory report generator (T039).
"""
import json
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

# Add code/src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code" / "src"))

from memory_report_generator import load_memory_profile, generate_markdown_report

class TestMemoryReportGenerator:
    """Tests for memory report generation logic."""

    def test_load_memory_profile_success(self, tmp_path):
        """Test loading a valid memory profile JSON."""
        profile_data = {
            "status": "PASS",
            "within_limit": True,
            "peak_memory_gb": 5.2,
            "average_memory_gb": 4.8
        }
        profile_file = tmp_path / "memory_profile.json"
        with open(profile_file, 'w') as f:
            json.dump(profile_data, f)

        result = load_memory_profile(profile_file)
        assert result is not None
        assert result["status"] == "PASS"
        assert result["within_limit"] is True
        assert result["peak_memory_gb"] == 5.2

    def test_load_memory_profile_missing_file(self, tmp_path):
        """Test loading a non-existent file returns None."""
        fake_path = tmp_path / "non_existent.json"
        result = load_memory_profile(fake_path)
        assert result is None

    def test_load_memory_profile_invalid_json(self, tmp_path):
        """Test loading a file with invalid JSON returns None."""
        profile_file = tmp_path / "invalid.json"
        with open(profile_file, 'w') as f:
            f.write("not valid json {")
        
        result = load_memory_profile(profile_file)
        assert result is None

    def test_generate_report_pass_status(self):
        """Test report generation for PASS status."""
        profile = {
            "status": "PASS",
            "within_limit": True,
            "peak_memory_gb": 6.5,
            "average_memory_gb": 5.0
        }
        report = generate_markdown_report(profile)
        
        assert "Status" in report
        assert "PASS" in report
        assert "6.5" in report
        assert "OOM prevention" in report
        assert "successfully prevented" in report

    def test_generate_report_fail_status(self):
        """Test report generation for FAIL status."""
        profile = {
            "status": "FAIL",
            "within_limit": False,
            "peak_memory_gb": 7.5
        }
        report = generate_markdown_report(profile)
        
        assert "FAIL" in report
        assert "exceeded" in report
        assert "Recommendations" in report

    def test_generate_report_missing_metrics(self):
        """Test report generation when metrics are missing."""
        profile = {
            "status": "UNKNOWN",
            "within_limit": False
        }
        report = generate_markdown_report(profile)
        
        assert "UNKNOWN" in report
        assert "N/A" in report
        assert "Peak Memory Usage" in report