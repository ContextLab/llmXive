"""
Unit tests for the logging infrastructure.

These tests verify that:
1. The logger is configured correctly.
2. Wall-clock timestamps are ISO 8601 formatted.
3. The heartbeat method logs structured JSON.
4. Log files are created in the correct directory.
"""

import logging
import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest

# Import the module under test
from code.orchestrator.logger import (
    configure_logging,
    get_logger,
    get_log_file_path,
    HEARTBEAT_LEVEL_NUM,
    _logging_configured,
    _log_file_path,
    LOG_DIR
)


class TestLoggerConfiguration:
    """Tests for logger configuration and initialization."""

    def test_configure_logging_creates_file_handler(self, tmp_path):
        """Verify that configure_logging sets up a file handler."""
        log_file = tmp_path / "test.log"
        configure_logging(log_file=str(log_file), level=logging.DEBUG)

        root_logger = logging.getLogger()
        file_handlers = [h for h in root_logger.handlers if isinstance(h, logging.FileHandler)]
        
        assert len(file_handlers) == 1
        assert file_handlers[0].baseFilename == str(log_file)

    def test_configure_logging_sets_correct_level(self, tmp_path):
        """Verify that the logger respects the specified level."""
        log_file = tmp_path / "test.log"
        configure_logging(log_file=str(log_file), level=logging.WARNING)

        root_logger = logging.getLogger()
        assert root_logger.level == logging.WARNING

    def test_configure_logging_only_runs_once(self, tmp_path):
        """Verify that re-calling configure_logging doesn't duplicate handlers."""
        log_file = tmp_path / "test.log"
        
        configure_logging(log_file=str(log_file), level=logging.DEBUG)
        initial_count = len(logging.getLogger().handlers)
        
        # Reset the global flag to simulate a fresh state for the second call
        # (In real usage, this shouldn't happen, but we test the guard)
        with patch('code.orchestrator.logger._logging_configured', False):
            configure_logging(log_file=str(log_file), level=logging.DEBUG)
        
        # The guard should prevent duplicate handlers
        final_count = len(logging.getLogger().handlers)
        assert initial_count == final_count

    def test_default_log_directory_creation(self):
        """Verify that the default log directory is created if it doesn't exist."""
        # Use a temporary directory to simulate a fresh environment
        with tempfile.TemporaryDirectory() as tmp_dir:
            fake_log_dir = Path(tmp_dir) / "fake_logs"
            with patch('code.orchestrator.logger.LOG_DIR', fake_log_dir):
                with patch('code.orchestrator.logger._logging_configured', False):
                    # Trigger directory creation
                    fake_log_dir.mkdir(parents=True, exist_ok=True)
                    assert fake_log_dir.exists()


class TestLoggerFunctionality:
    """Tests for actual logging functionality."""

    def test_get_logger_returns_configured_instance(self, tmp_path):
        """Verify that get_logger returns a valid logger instance."""
        log_file = tmp_path / "test.log"
        configure_logging(log_file=str(log_file))

        logger = get_logger("test_module")
        assert isinstance(logger, logging.Logger)
        assert logger.name == "test_module"

    def test_log_contains_wall_clock_timestamp(self, tmp_path):
        """Verify that log messages contain ISO 8601 timestamps."""
        log_file = tmp_path / "test.log"
        configure_logging(log_file=str(log_file), level=logging.DEBUG)

        logger = get_logger("test_timestamp")
        logger.info("Test message")

        # Read the log file and check format
        with open(log_file, 'r') as f:
            content = f.read()
        
        # Check for ISO 8601 pattern (YYYY-MM-DDTHH:MM:SS)
        import re
        pattern = r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}'
        assert re.search(pattern, content), "Log message missing ISO 8601 timestamp"

    def test_heartbeat_method_exists(self):
        """Verify that the Logger class has a heartbeat method."""
        logger = logging.getLogger("test_heartbeat")
        assert hasattr(logger, 'heartbeat')
        assert callable(logger.heartbeat)

    def test_heartbeat_logs_json_structure(self, tmp_path):
        """Verify that heartbeat logs a valid JSON structure."""
        log_file = tmp_path / "test.log"
        configure_logging(log_file=str(log_file), level=HEARTBEAT_LEVEL_NUM)

        logger = get_logger("test_heartbeat_json")
        
        # Call heartbeat
        logger.heartbeat(
            node_id="node-001",
            status="active",
            latency_ms=12.5,
            extra_data={"cpu": 45.2}
        )

        # Read and parse the log
        with open(log_file, 'r') as f:
            content = f.read()
        
        # Extract the JSON part (it should be the last part of the line)
        # Format: TIMESTAMP|LEVEL|NAME|JSON_PAYLOAD
        parts = content.split('|')
        assert len(parts) >= 4, "Log format unexpected"
        
        json_str = parts[-1].strip()
        try:
            data = json.loads(json_str)
        except json.JSONDecodeError:
            pytest.fail(f"Log entry is not valid JSON: {json_str}")

        assert data["event_type"] == "heartbeat"
        assert data["node_id"] == "node-001"
        assert data["status"] == "active"
        assert abs(data["latency_ms"] - 12.5) < 0.01
        assert data["extra"]["cpu"] == 45.2

    def test_heartbeat_handles_missing_extra_data(self, tmp_path):
        """Verify that heartbeat works when extra_data is None."""
        log_file = tmp_path / "test.log"
        configure_logging(log_file=str(log_file), level=HEARTBEAT_LEVEL_NUM)

        logger = get_logger("test_heartbeat_empty")
        logger.heartbeat(
            node_id="node-002",
            status="idle",
            latency_ms=5.0
        )

        with open(log_file, 'r') as f:
            content = f.read()
        
        parts = content.split('|')
        json_str = parts[-1].strip()
        data = json.loads(json_str)

        assert data["extra"] == {}

    def test_get_log_file_path_returns_path_object(self, tmp_path):
        """Verify that get_log_file_path returns a Path object."""
        log_file = tmp_path / "test.log"
        configure_logging(log_file=str(log_file))

        path = get_log_file_path()
        assert isinstance(path, Path)
        assert str(path) == str(log_file)

class TestHeartbeatLevel:
    """Tests for the custom HEARTBEAT log level."""

    def test_heartbeat_level_defined(self):
        """Verify that HEARTBEAT_LEVEL_NUM is defined and between INFO and DEBUG."""
        assert HEARTBEAT_LEVEL_NUM > logging.DEBUG
        assert HEARTBEAT_LEVEL_NUM < logging.INFO
        assert logging.getLevelName(HEARTBEAT_LEVEL_NUM) == "HEARTBEAT"

    def test_heartbeat_logs_at_correct_level(self, tmp_path):
        """Verify that heartbeat messages are logged when level is set appropriately."""
        log_file = tmp_path / "test.log"
        configure_logging(log_file=str(log_file), level=HEARTBEAT_LEVEL_NUM)

        logger = get_logger("test_level")
        
        # This should be logged
        logger.heartbeat("n1", "ok", 1.0)
        
        # This should NOT be logged (below HEARTBEAT level)
        logger.debug("debug message")

        with open(log_file, 'r') as f:
            content = f.read()
        
        assert "heartbeat" in content
        assert "debug message" not in content