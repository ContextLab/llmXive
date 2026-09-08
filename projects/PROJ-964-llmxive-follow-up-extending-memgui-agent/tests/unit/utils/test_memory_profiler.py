"""
Unit tests for the memory_profiler module.
"""
import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.utils.memory_profiler import (
    log_metrics,
    profile_memory_latency,
    get_current_memory_usage,
    get_peak_memory_usage,
    clear_logs,
    read_logs,
    _load_existing_logs,
    _append_log,
    LOG_FILE
)

class TestLogMetrics:
    def test_log_metrics_creates_file_and_writes_entry(self, tmp_path):
        """Test that log_metrics creates the log file and writes an entry."""
        # Mock the LOG_FILE path to use a temporary directory
        with patch('code.utils.memory_profiler.LOG_FILE', tmp_path / "test_memory_profile.json"):
            log_metrics(
                peak_memory_mb=123.45,
                latency_ms=50.0,
                agent_type="test_agent",
                metadata={"test_key": "test_value"}
            )
            
            log_file = tmp_path / "test_memory_profile.json"
            assert log_file.exists()
            
            with open(log_file, 'r') as f:
                content = f.read().strip()
                entry = json.loads(content)
                
            assert entry["peak_memory_mb"] == 123.45
            assert entry["latency_ms"] == 50.0
            assert entry["agent_type"] == "test_agent"
            assert entry["test_key"] == "test_value"
            assert "timestamp" in entry

    def test_log_metrics_appends_to_existing_file(self, tmp_path):
        """Test that log_metrics appends to an existing log file."""
        log_file = tmp_path / "test_memory_profile.json"
        
        # Write an initial entry
        with open(log_file, 'w') as f:
            f.write(json.dumps({"initial": True}) + '\n')
        
        with patch('code.utils.memory_profiler.LOG_FILE', log_file):
            log_metrics(
                peak_memory_mb=200.0,
                latency_ms=100.0,
                agent_type="second_agent"
            )
            
            with open(log_file, 'r') as f:
                lines = f.readlines()
            
            assert len(lines) == 2
            second_entry = json.loads(lines[1])
            assert second_entry["peak_memory_mb"] == 200.0
            assert second_entry["agent_type"] == "second_agent"

class TestProfileMemoryLatency:
    def test_profile_memory_latency_context_manager(self, tmp_path):
        """Test that the context manager profiles and logs correctly."""
        log_file = tmp_path / "test_memory_profile.json"
        
        with patch('code.utils.memory_profiler.LOG_FILE', log_file):
            with profile_memory_latency("test_agent", {"step": 1}) as results:
                # Simulate some work
                _ = [i * i for i in range(1000)]
            
            # Check that the file was created
            assert log_file.exists()
            
            with open(log_file, 'r') as f:
                entry = json.loads(f.read().strip())
            
            assert entry["agent_type"] == "test_agent"
            assert entry["step"] == 1
            assert entry["peak_memory_mb"] > 0
            assert entry["latency_ms"] > 0
            assert "timestamp" in entry

    def test_profile_memory_latency_rounds_values(self, tmp_path):
        """Test that the context manager rounds values to 2 decimal places."""
        log_file = tmp_path / "test_memory_profile.json"
        
        with patch('code.utils.memory_profiler.LOG_FILE', log_file):
            with profile_memory_latency("test_agent"):
                pass
            
            with open(log_file, 'r') as f:
                entry = json.loads(f.read().strip())
            
            # Check that values are rounded to 2 decimal places
            assert isinstance(entry["peak_memory_mb"], float)
            assert isinstance(entry["latency_ms"], float)
            # The values should not have more than 2 decimal places
            assert str(entry["peak_memory_mb"]).split('.')[-1][:2] == str(entry["peak_memory_mb"])[:len(str(entry["peak_memory_mb"]).split('.')[-1])]

class TestGetMemoryUsage:
    def test_get_current_memory_usage_returns_positive(self):
        """Test that get_current_memory_usage returns a positive value."""
        # Start tracemalloc if not already started
        import tracemalloc
        if not tracemalloc.is_tracing():
            tracemalloc.start()
        
        usage = get_current_memory_usage()
        assert usage >= 0

    def test_get_peak_memory_usage_returns_positive(self):
        """Test that get_peak_memory_usage returns a positive value."""
        import tracemalloc
        if not tracemalloc.is_tracing():
            tracemalloc.start()
        
        # Do some memory allocation
        _ = [i * i for i in range(10000)]
        
        peak = get_peak_memory_usage()
        assert peak >= 0

class TestClearAndReadLogs:
    def test_clear_logs_removes_file(self, tmp_path):
        """Test that clear_logs removes the log file."""
        log_file = tmp_path / "test_memory_profile.json"
        log_file.write_text('{"test": true}\n')
        
        with patch('code.utils.memory_profiler.LOG_FILE', log_file):
            clear_logs()
            assert not log_file.exists()

    def test_read_logs_returns_empty_list_when_no_file(self, tmp_path):
        """Test that read_logs returns empty list when no file exists."""
        with patch('code.utils.memory_profiler.LOG_FILE', tmp_path / "nonexistent.json"):
            logs = read_logs()
            assert logs == []

    def test_read_logs_returns_entries(self, tmp_path):
        """Test that read_logs returns all entries from the file."""
        log_file = tmp_path / "test_memory_profile.json"
        log_file.write_text('{"entry": 1}\n{"entry": 2}\n')
        
        with patch('code.utils.memory_profiler.LOG_FILE', log_file):
            logs = read_logs()
            assert len(logs) == 2
            assert logs[0]["entry"] == 1
            assert logs[1]["entry"] == 2
