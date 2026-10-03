"""
Tests for the memory profiler utility.

These tests validate the functionality of code/lib/memory_profiler.py
including memory profiling, logging, and limit enforcement.
"""

import os
import sys
import json
import tempfile
import pytest
from pathlib import Path
import time

# Add code/lib to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from lib.memory_profiler import (
    get_memory_usage_gb,
    start_profiling,
    stop_profiling,
    load_existing_logs,
    save_log_entry,
    profile_memory,
    check_memory_usage,
    MemoryProfiler,
    DEFAULT_MEMORY_LIMIT_GB,
    OUTPUT_DIR,
    OUTPUT_FILE
)


class TestMemoryProfiler:
    """Test cases for memory profiler functionality."""

    def test_get_memory_usage_returns_positive_value(self):
        """Test that get_memory_usage_gb returns a positive float."""
        usage = get_memory_usage_gb()
        assert isinstance(usage, float)
        assert usage >= 0.0

    def test_start_and_stop_profiling(self):
        """Test that profiling can be started and stopped."""
        start_profiling()
        # Do some work
        data = list(range(1000))
        peak = stop_profiling()
        assert isinstance(peak, float)
        assert peak >= 0.0

    def test_profile_memory_creates_log_entry(self):
        """Test that profile_memory creates a valid log entry."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Temporarily change output directory
            original_output_file = OUTPUT_FILE
            temp_output = Path(tmpdir) / "test_log.json"

            # Mock the OUTPUT_FILE
            import lib.memory_profiler as mp
            mp.OUTPUT_FILE = temp_output

            try:
                result = profile_memory(
                    script_name="test_script",
                    duration_seconds=0.1,
                    memory_limit_gb=7.0
                )

                # Verify result structure
                assert "peak_memory_gb" in result
                assert "timestamp" in result
                assert "script_name" in result
                assert "memory_limit_gb" in result
                assert "duration_seconds" in result
                assert "converged" in result
                assert "error" in result

                # Verify values
                assert result["script_name"] == "test_script"
                assert result["memory_limit_gb"] == 7.0
                assert result["converged"] is True
                assert result["error"] is None

                # Verify file was created
                assert temp_output.exists()

                # Verify JSON content
                with open(temp_output, 'r') as f:
                    logs = json.load(f)
                assert isinstance(logs, list)
                assert len(logs) == 1
                assert logs[0]["script_name"] == "test_script"

            finally:
                # Restore original output file
                mp.OUTPUT_FILE = original_output_file

    def test_profile_memory_exceeds_limit(self):
        """Test that profile_memory raises SystemExit when limit is exceeded."""
        with tempfile.TemporaryDirectory() as tmpdir:
            temp_output = Path(tmpdir) / "test_log.json"

            import lib.memory_profiler as mp
            original_output_file = mp.OUTPUT_FILE
            mp.OUTPUT_FILE = temp_output

            try:
                # Use a very low limit that will be exceeded
                with pytest.raises(SystemExit) as exc_info:
                    profile_memory(
                        script_name="test_exceed",
                        duration_seconds=0.1,
                        memory_limit_gb=0.0001  # Very low limit
                    )

                assert exc_info.value.code == 1

                # Verify log entry shows failure
                with open(temp_output, 'r') as f:
                    logs = json.load(f)
                assert len(logs) == 1
                assert logs[0]["converged"] is False
                assert logs[0]["error"] is not None

            finally:
                mp.OUTPUT_FILE = original_output_file

    def test_memory_profiler_context_manager(self):
        """Test MemoryProfiler context manager."""
        with tempfile.TemporaryDirectory() as tmpdir:
            temp_output = Path(tmpdir) / "test_log.json"

            import lib.memory_profiler as mp
            original_output_file = mp.OUTPUT_FILE
            mp.OUTPUT_FILE = temp_output

            try:
                with MemoryProfiler("test_context", memory_limit_gb=7.0) as profiler:
                    # Do some work
                    data = list(range(10000))
                    _ = sum(data)

                # Verify profiler attributes
                assert profiler.peak_memory_gb >= 0.0
                assert profiler.duration_seconds >= 0.0
                assert profiler.entry["converged"] is True

                # Verify log file
                assert temp_output.exists()

            finally:
                mp.OUTPUT_FILE = original_output_file

    def test_check_memory_usage_within_limit(self):
        """Test check_memory_usage when within limit."""
        result = check_memory_usage(memory_limit_gb=DEFAULT_MEMORY_LIMIT_GB)
        assert result is True

    def test_load_existing_logs_empty_file(self):
        """Test loading logs from non-existent file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            temp_output = Path(tmpdir) / "nonexistent.json"

            import lib.memory_profiler as mp
            original_output_file = mp.OUTPUT_FILE
            mp.OUTPUT_FILE = temp_output

            try:
                logs = load_existing_logs()
                assert logs == []

            finally:
                mp.OUTPUT_FILE = original_output_file

    def test_load_existing_logs_valid_json(self):
        """Test loading logs from valid JSON file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            temp_output = Path(tmpdir) / "test_log.json"

            # Create a valid log file
            test_data = [
                {
                    "peak_memory_gb": 0.5,
                    "timestamp": "2026-01-01T00:00:00",
                    "script_name": "test",
                    "memory_limit_gb": 7.0,
                    "duration_seconds": 1.0,
                    "converged": True,
                    "error": None
                }
            ]

            with open(temp_output, 'w') as f:
                json.dump(test_data, f)

            import lib.memory_profiler as mp
            original_output_file = mp.OUTPUT_FILE
            mp.OUTPUT_FILE = temp_output

            try:
                logs = load_existing_logs()
                assert len(logs) == 1
                assert logs[0]["peak_memory_gb"] == 0.5

            finally:
                mp.OUTPUT_FILE = original_output_file

    def test_save_log_entry_appends_to_existing(self):
        """Test that save_log_entry appends to existing logs."""
        with tempfile.TemporaryDirectory() as tmpdir:
            temp_output = Path(tmpdir) / "test_log.json"

            # Create initial log
            initial_data = [
                {
                    "peak_memory_gb": 0.5,
                    "timestamp": "2026-01-01T00:00:00",
                    "script_name": "test1",
                    "memory_limit_gb": 7.0,
                    "duration_seconds": 1.0,
                    "converged": True,
                    "error": None
                }
            ]

            with open(temp_output, 'w') as f:
                json.dump(initial_data, f)

            import lib.memory_profiler as mp
            original_output_file = mp.OUTPUT_FILE
            mp.OUTPUT_FILE = temp_output

            try:
                # Add new entry
                new_entry = {
                    "peak_memory_gb": 0.6,
                    "timestamp": "2026-01-02T00:00:00",
                    "script_name": "test2",
                    "memory_limit_gb": 7.0,
                    "duration_seconds": 1.0,
                    "converged": True,
                    "error": None
                }
                save_log_entry(new_entry)

                # Verify both entries exist
                with open(temp_output, 'r') as f:
                    logs = json.load(f)
                assert len(logs) == 2
                assert logs[0]["script_name"] == "test1"
                assert logs[1]["script_name"] == "test2"

            finally:
                mp.OUTPUT_FILE = original_output_file

    def test_script_name_extraction(self):
        """Test that script_name is correctly extracted from __file__."""
        with tempfile.TemporaryDirectory() as tmpdir:
            temp_output = Path(tmpdir) / "test_log.json"

            import lib.memory_profiler as mp
            original_output_file = mp.OUTPUT_FILE
            mp.OUTPUT_FILE = temp_output

            try:
                result = profile_memory(duration_seconds=0.1)
                # Should use the module's basename
                assert result["script_name"] == "memory_profiler.py" or \
                       result["script_name"] == "test_memory_profiler"

            finally:
                mp.OUTPUT_FILE = original_output_file


if __name__ == "__main__":
    pytest.main([__file__, "-v"])