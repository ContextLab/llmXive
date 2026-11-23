"""
Unit tests for logging utilities.
"""
import json
import os
import tempfile
from pathlib import Path
import pytest

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from simulation.logging_utils import ensure_log_directory, log_simulation_run, get_log_entries


class TestLoggingUtils:
    """Test cases for logging utilities."""

    def test_ensure_log_directory_creates_directory(self):
        """Test that ensure_log_directory creates the directory if it doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_dir = Path(tmpdir) / "test_logs"
            result = ensure_log_directory(str(log_dir))
            
            assert result.exists()
            assert result.is_dir()
            assert result == log_dir

    def test_ensure_log_directory_existing_directory(self):
        """Test that ensure_log_directory works with existing directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_dir = Path(tmpdir) / "existing_logs"
            log_dir.mkdir()
            
            result = ensure_log_directory(str(log_dir))
            
            assert result.exists()
            assert result.is_dir()

    def test_log_simulation_run_creates_file(self):
        """Test that log_simulation_run creates the log file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = Path(tmpdir) / "test.log"
            
            log_entry = {"test": "data", "value": 123}
            log_simulation_run(log_entry, str(log_file))
            
            assert log_file.exists()
            assert log_file.stat().st_size > 0

    def test_log_simulation_run_json_format(self):
        """Test that log entries are written in valid JSON format."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = Path(tmpdir) / "test.log"
            
            log_entry = {"seed": 42, "N": 30, "rho": 0.5, "duration": 1.23}
            log_simulation_run(log_entry, str(log_file))
            
            # Read and verify JSON format
            with open(log_file, 'r') as f:
                line = f.readline().strip()
                parsed = json.loads(line)
                
                assert parsed["seed"] == 42
                assert parsed["N"] == 30
                assert parsed["rho"] == 0.5
                assert "duration" in parsed

    def test_log_simulation_run_adds_timestamp(self):
        """Test that log entries include a timestamp."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = Path(tmpdir) / "test.log"
            
            log_entry = {"test": "data"}
            log_simulation_run(log_entry, str(log_file))
            
            entries = get_log_entries(str(log_file))
            assert len(entries) == 1
            assert "timestamp" in entries[0]

    def test_get_log_entries_empty_file(self):
        """Test get_log_entries with non-existent file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = Path(tmpdir) / "nonexistent.log"
            
            entries = get_log_entries(str(log_file))
            assert entries == []

    def test_get_log_entries_multiple_entries(self):
        """Test get_log_entries with multiple log entries."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = Path(tmpdir) / "test.log"
            
            # Write multiple entries
            for i in range(5):
                log_entry = {"seed": i, "value": i * 10}
                log_simulation_run(log_entry, str(log_file))
            
            entries = get_log_entries(str(log_file))
            assert len(entries) == 5
            
            for i, entry in enumerate(entries):
                assert entry["seed"] == i
                assert entry["value"] == i * 10

    def test_log_simulation_run_append_mode(self):
        """Test that log entries are appended, not overwritten."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = Path(tmpdir) / "test.log"
            
            # Write first entry
            log_simulation_run({"first": True}, str(log_file))
            # Write second entry
            log_simulation_run({"second": True}, str(log_file))
            
            entries = get_log_entries(str(log_file))
            assert len(entries) == 2
            
            assert entries[0]["first"] is True
            assert entries[1]["second"] is True