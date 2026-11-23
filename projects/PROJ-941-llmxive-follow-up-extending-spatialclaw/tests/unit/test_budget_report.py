"""
Unit tests for T056: Budget Compliance Report.
"""
import json
import os
import tempfile
import time
from unittest.mock import patch, MagicMock
import pytest

# Import the module to test
# We assume the module is code/utils/budget_report.py
# For testing, we might need to adjust sys.path or import relative to the project root.
# Here we assume the test is run from the project root.
import sys
sys.path.insert(0, 'code')

from utils.budget_report import (
    load_start_time_marker,
    measure_total_runtime,
    load_budget_limit,
    write_report,
    run_budget_report
)
from utils.logging import setup_logging


class TestLoadStartTimeMarker:
    def test_marker_exists_and_valid(self, tmp_path):
        marker_path = tmp_path / "pipeline_start_time.json"
        start_time = time.time()
        with open(marker_path, 'w') as f:
            json.dump({"start_time": start_time}, f)
        
        result = load_start_time_marker(str(marker_path))
        assert result == start_time

    def test_marker_missing(self, tmp_path):
        marker_path = tmp_path / "missing.json"
        result = load_start_time_marker(str(marker_path))
        assert result is None

    def test_marker_invalid_json(self, tmp_path):
        marker_path = tmp_path / "invalid.json"
        with open(marker_path, 'w') as f:
            f.write("not json")
        result = load_start_time_marker(str(marker_path))
        assert result is None

    def test_marker_missing_key(self, tmp_path):
        marker_path = tmp_path / "missing_key.json"
        with open(marker_path, 'w') as f:
            json.dump({"other_key": 123}, f)
        result = load_start_time_marker(str(marker_path))
        assert result is None


class TestMeasureTotalRuntime:
    def test_runtime_calculated(self):
        start = time.time() - 10.0
        duration = measure_total_runtime(start)
        assert 9.0 < duration < 11.0  # Allow small variance

    def test_runtime_none_start(self):
        duration = measure_total_runtime(None)
        assert duration == 0.0


class TestLoadBudgetLimit:
    def test_load_from_config(self, tmp_path):
        config_path = tmp_path / "power_config.yaml"
        with open(config_path, 'w') as f:
            f.write("max_runtime_hours: 2.5\n")
        
        limit = load_budget_limit(str(config_path))
        assert limit == 2.5 * 3600.0

    def test_default_limit(self, tmp_path):
        config_path = tmp_path / "power_config.yaml"
        with open(config_path, 'w') as f:
            f.write("other_key: 100\n")  # No max_runtime_hours
        
        limit = load_budget_limit(str(config_path))
        assert limit == 6.0 * 3600.0  # Default 6 hours


class TestWriteReport:
    def test_write_json(self, tmp_path):
        output_path = tmp_path / "report.json"
        write_report(str(output_path), 100.0, 200.0, "PASS")
        
        assert os.path.exists(output_path)
        with open(output_path, 'r') as f:
            data = json.load(f)
        
        assert data["total_runtime_seconds"] == 100.0
        assert data["budget_limit_seconds"] == 200.0
        assert data["status"] == "PASS"
        assert "generated_at" in data


class TestRunBudgetReport:
    def test_full_flow_pass(self, tmp_path, monkeypatch):
        # Setup temp paths
        marker_path = tmp_path / "start.json"
        config_path = tmp_path / "config.yaml"
        output_path = tmp_path / "report.json"
        
        start_time = time.time() - 5.0
        with open(marker_path, 'w') as f:
            json.dump({"start_time": start_time}, f)
        
        with open(config_path, 'w') as f:
            f.write("max_runtime_hours: 1.0\n")  # 3600s limit
        
        # Mock load_start_time_marker to use our temp path
        def mock_load_marker(path):
            return load_start_time_marker(path)
        
        monkeypatch.setattr("utils.budget_report.load_start_time_marker", mock_load_marker)
        
        result = run_budget_report(
            config_path=str(config_path),
            output_path=str(output_path)
        )
        
        assert result["status"] == "PASS"
        assert result["total_runtime_seconds"] > 0
        assert result["budget_limit_seconds"] == 3600.0
        assert os.path.exists(output_path)

    def test_full_flow_fail(self, tmp_path, monkeypatch):
        # Setup temp paths
        marker_path = tmp_path / "start.json"
        config_path = tmp_path / "config.yaml"
        output_path = tmp_path / "report.json"
        
        start_time = time.time() - 4000.0  # Exceeds 1 hour limit
        with open(marker_path, 'w') as f:
            json.dump({"start_time": start_time}, f)
        
        with open(config_path, 'w') as f:
            f.write("max_runtime_hours: 1.0\n")  # 3600s limit
        
        def mock_load_marker(path):
            return load_start_time_marker(path)
        
        monkeypatch.setattr("utils.budget_report.load_start_time_marker", mock_load_marker)
        
        result = run_budget_report(
            config_path=str(config_path),
            output_path=str(output_path)
        )
        
        assert result["status"] == "FAIL"
        assert os.path.exists(output_path)
