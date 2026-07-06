"""
Unit tests for the ResourceLogger and logging utilities.
"""
import json
import os
import tempfile
from pathlib import Path
import pytest
import sys

# Ensure the code directory is in the path for imports if running from root
# In the actual project structure, this would be handled by the runner
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from src.utils.logging import ensure_log_dir, ResourceLogger


class TestLogging:
    """Tests for logging functionality."""

    def test_ensure_log_dir_creates_directory(self, tmp_path):
        """Test that ensure_log_dir creates the directory if it doesn't exist."""
        log_dir = tmp_path / "new_logs"
        assert not log_dir.exists()

        result = ensure_log_dir(log_dir)

        assert result.exists()
        assert result.is_dir()

    def test_ensure_log_dir_uses_existing_directory(self, tmp_path):
        """Test that ensure_log_dir returns the existing directory."""
        log_dir = tmp_path / "existing_logs"
        log_dir.mkdir()
        assert log_dir.exists()

        result = ensure_log_dir(log_dir)

        assert result == log_dir

    def test_resource_logger_initialization(self, tmp_path):
        """Test ResourceLogger initialization."""
        logger = ResourceLogger(log_dir=tmp_path, session_id="test_session")
        assert logger.log_dir == tmp_path
        assert logger.session_id == "test_session"
        assert logger._start_time is None
        assert len(logger._logs) == 0

    def test_log_event_adds_entry(self, tmp_path):
        """Test that log_event adds an entry to the internal list."""
        logger = ResourceLogger(log_dir=tmp_path, session_id="test_session")
        entry = logger.log_event("TEST", "Test message", {"key": "value"})

        assert len(logger._logs) == 1
        assert entry["event_type"] == "TEST"
        assert entry["message"] == "Test message"
        assert entry["data"]["key"] == "value"
        assert "resource_snapshot" in entry
        assert "timestamp" in entry
        assert "session_id" in entry

    def test_start_session(self, tmp_path):
        """Test start_session sets start time and logs event."""
        logger = ResourceLogger(log_dir=tmp_path, session_id="test_session")
        entry = logger.start_session(context="unit_test")

        assert logger._start_time is not None
        assert entry["event_type"] == "SESSION_START"
        assert entry["data"]["context"] == "unit_test"

    def test_end_session_fails_without_start(self, tmp_path):
        """Test that end_session raises error if session not started."""
        logger = ResourceLogger(log_dir=tmp_path, session_id="test_session")
        with pytest.raises(RuntimeError, match="Session not started"):
            logger.end_session()

    def test_end_session_writes_file(self, tmp_path):
        """Test that end_session writes logs to a file."""
        logger = ResourceLogger(log_dir=tmp_path, session_id="test_session")
        logger.start_session()
        logger.log_event("MID", "Mid session")
        entry = logger.end_session()

        # Check file exists
        expected_file = tmp_path / "test_session_logs.json"
        assert expected_file.exists()

        # Check content
        with open(expected_file, 'r') as f:
            data = json.load(f)
        assert len(data) == 2 # Start and End events (MID was not flushed separately but included in list)
        # Actually, the list contains Start, MID, End. The write_logs dumps the whole list.
        assert len(data) == 3
        assert data[-1]["event_type"] == "SESSION_END"

    def test_log_metric(self, tmp_path):
        """Test logging a metric."""
        logger = ResourceLogger(log_dir=tmp_path, session_id="test_session")
        entry = logger.log_metric("accuracy", 0.95, unit="%", tags={"model": "test"})

        assert entry["event_type"] == "METRIC"
        assert entry["data"]["metric_name"] == "accuracy"
        assert entry["data"]["metric_value"] == 0.95
        assert entry["data"]["tags"]["model"] == "test"

    def test_log_error(self, tmp_path):
        """Test logging an error."""
        logger = ResourceLogger(log_dir=tmp_path, session_id="test_session")
        entry = logger.log_error("ValueError", "Invalid value", traceback_str="Traceback...")

        assert entry["event_type"] == "ERROR"
        assert entry["data"]["error_type"] == "ValueError"
        assert entry["data"]["traceback"] == "Traceback..."
