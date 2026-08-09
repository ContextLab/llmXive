"""
Tests for T046: Pipeline Runtime Measurement.
Verifies that the runtime script produces valid output and checks constraints.
"""
import os
import json
import tempfile
import shutil
from pathlib import Path
import pytest
from unittest.mock import patch, MagicMock

# Project root setup
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in os.sys.path:
    os.sys.path.insert(0, str(project_root))

from code.run_pipeline_timing import save_runtime_metrics, MAX_RUNTIME_HOURS, OUTPUT_PATH


class TestRuntimeMetrics:
    """Tests for the runtime metrics generation logic."""

    def test_save_runtime_metrics_creates_file(self, tmp_path):
        """Test that save_runtime_metrics creates the JSON file."""
        # Temporarily override OUTPUT_PATH for this test
        test_output = tmp_path / "runtime_test.json"
        
        with patch('code.run_pipeline_timing.OUTPUT_PATH', test_output):
            start = 1000.0
            end = 1100.0
            save_runtime_metrics(start, end, "SUCCESS", "Test message")
        
        assert test_output.exists()
        
        with open(test_output) as f:
            data = json.load(f)
        
        assert "duration_seconds" in data
        assert "duration_hours" in data
        assert data["duration_seconds"] == 100.0
        assert data["duration_hours"] == 100.0 / 3600.0
        assert data["passed_constraint"] is True  # 100s < 6h
        assert data["status"] == "SUCCESS"
        assert data["message"] == "Test message"

    def test_save_runtime_metrics_detects_timeout(self, tmp_path):
        """Test that save_runtime_metrics correctly flags a timeout."""
        test_output = tmp_path / "runtime_timeout_test.json"
        
        # Simulate a run that took 7 hours
        start = 1000.0
        end = 1000.0 + (7 * 3600)  # 7 hours later
        
        with patch('code.run_pipeline_timing.OUTPUT_PATH', test_output):
            save_runtime_metrics(start, end, "SUCCESS", "Timeout test")
        
        with open(test_output) as f:
            data = json.load(f)
        
        assert data["duration_hours"] == 7.0
        assert data["passed_constraint"] is False
        assert data["status"] == "SUCCESS"

    def test_max_runtime_constant(self):
        """Verify the max runtime constant is set to 6 hours."""
        assert MAX_RUNTIME_HOURS == 6.0

    def test_output_structure(self, tmp_path):
        """Verify the output JSON contains all required fields."""
        test_output = tmp_path / "structure_test.json"
        
        with patch('code.run_pipeline_timing.OUTPUT_PATH', test_output):
            save_runtime_metrics(0, 100, "SUCCESS")
        
        with open(test_output) as f:
            data = json.load(f)
        
        required_keys = [
            "timestamp", "duration_seconds", "duration_hours", 
            "max_allowed_hours", "passed_constraint", "status", "message"
        ]
        
        for key in required_keys:
            assert key in data, f"Missing required key: {key}"