"""
Unit tests for check_pipeline_runtime module.
"""
import os
import json
import tempfile
from datetime import datetime
from pathlib import Path
import pytest

from code.check_pipeline_runtime import parse_log_timestamps, calculate_runtime_hours, run_runtime_check, main

class TestParseLogTimestamps:
    def test_valid_log_file(self, tmp_path):
        log_content = """2023-10-27 10:00:00,123 - INFO - Starting data ingestion
        2023-10-27 10:05:00,456 - INFO - Processing data
        2023-10-27 14:30:00,789 - INFO - Pipeline execution completed (US1)
        """
        log_file = tmp_path / "pipeline.log"
        log_file.write_text(log_content)
        
        start, end = parse_log_timestamps(log_file)
        
        assert start is not None
        assert end is not None
        assert start.hour == 10
        assert start.minute == 0
        assert end.hour == 14
        assert end.minute == 30

    def test_missing_start_marker(self, tmp_path):
        log_content = """2023-10-27 10:05:00,456 - INFO - Processing data
        2023-10-27 14:30:00,789 - INFO - Pipeline execution completed (US1)
        """
        log_file = tmp_path / "pipeline.log"
        log_file.write_text(log_content)
        
        start, end = parse_log_timestamps(log_file)
        
        assert start is None
        assert end is not None

    def test_missing_end_marker(self, tmp_path):
        log_content = """2023-10-27 10:00:00,123 - INFO - Starting data ingestion
        2023-10-27 10:05:00,456 - INFO - Processing data
        """
        log_file = tmp_path / "pipeline.log"
        log_file.write_text(log_content)
        
        start, end = parse_log_timestamps(log_file)
        
        assert start is not None
        assert end is None

    def test_file_not_found(self):
        start, end = parse_log_timestamps(Path("nonexistent.log"))
        assert start is None
        assert end is None

class TestCalculateRuntimeHours:
    def test_valid_times(self):
        start = datetime(2023, 10, 27, 10, 0, 0)
        end = datetime(2023, 10, 27, 14, 30, 0)
        
        hours = calculate_runtime_hours(start, end)
        
        assert hours == 4.5

    def test_missing_start(self):
        hours = calculate_runtime_hours(None, datetime.now())
        assert hours is None

    def test_missing_end(self):
        hours = calculate_runtime_hours(datetime.now(), None)
        assert hours is None

    def test_zero_duration(self):
        now = datetime.now()
        hours = calculate_runtime_hours(now, now)
        assert hours == 0.0

class TestRunRuntimeCheck:
    def test_successful_run(self, tmp_path, monkeypatch):
        # Create a mock log file
        log_dir = tmp_path / "logs"
        log_dir.mkdir()
        log_file = log_dir / "pipeline.log"
        
        log_content = """2023-10-27 10:00:00,123 - INFO - Starting data ingestion
        2023-10-27 12:00:00,456 - INFO - Pipeline execution completed (US1)
        """
        log_file.write_text(log_content)
        
        # Change working directory to tmp_path
        monkeypatch.chdir(tmp_path)
        
        # Mock the output path logic if necessary, but run_runtime_check uses relative paths
        # We need to ensure the logs directory exists relative to where the function runs
        # The function looks for "logs/pipeline.log"
        
        results = run_runtime_check()
        
        assert "total_runtime_hours" in results
        assert results["total_runtime_hours"] == 2.0
        assert results["passed"] is True
        assert results["threshold_hours"] == 4.0

    def test_runtime_exceeds_threshold(self, tmp_path, monkeypatch):
        log_dir = tmp_path / "logs"
        log_dir.mkdir()
        log_file = log_dir / "pipeline.log"
        
        log_content = """2023-10-27 08:00:00,123 - INFO - Starting data ingestion
        2023-10-27 13:00:00,456 - INFO - Pipeline execution completed (US1)
        """
        log_file.write_text(log_content)
        
        monkeypatch.chdir(tmp_path)
        
        results = run_runtime_check()
        
        assert results["total_runtime_hours"] == 5.0
        assert results["passed"] is False

    def test_missing_log_file(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        
        results = run_runtime_check()
        
        assert results["total_runtime_hours"] is None
        assert results["passed"] is False