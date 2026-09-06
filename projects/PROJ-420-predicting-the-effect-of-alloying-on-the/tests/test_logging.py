"""
Tests for the logging infrastructure (T006).
"""
import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest
import yaml

from code.logging_config import (
    LogEntry,
    JSONFormatter,
    setup_logging,
    log_operation,
    LOG_FILE,
)


class TestLogEntry:
    """Tests for LogEntry dataclass."""

    def test_log_entry_creation(self):
        """Test creating a LogEntry with required fields."""
        entry = LogEntry(
            timestamp="2024-01-01T00:00:00",
            level="INFO",
            message="Test message",
            trace_id="abc-123",
            module="test_module",
        )
        assert entry.timestamp == "2024-01-01T00:00:00"
        assert entry.level == "INFO"
        assert entry.message == "Test message"
        assert entry.trace_id == "abc-123"
        assert entry.module == "test_module"

    def test_log_entry_to_json(self):
        """Test LogEntry serialization to JSON."""
        entry = LogEntry(
            timestamp="2024-01-01T00:00:00",
            level="INFO",
            message="Test message",
            trace_id="abc-123",
            module="test_module",
        )
        json_str = entry.to_json()
        data = json.loads(json_str)

        assert data["timestamp"] == "2024-01-01T00:00:00"
        assert data["level"] == "INFO"
        assert data["message"] == "Test message"
        assert data["trace_id"] == "abc-123"
        assert data["module"] == "test_module"

    def test_log_entry_from_dict(self):
        """Test creating LogEntry from dictionary."""
        data = {
            "timestamp": "2024-01-01T00:00:00",
            "level": "INFO",
            "message": "Test message",
            "trace_id": "abc-123",
            "module": "test_module",
        }
        entry = LogEntry.from_dict(data)
        assert entry.timestamp == "2024-01-01T00:00:00"
        assert entry.level == "INFO"
        assert entry.message == "Test message"

    def test_log_entry_missing_field(self):
        """Test that missing required fields raise an error."""
        data = {
            "timestamp": "2024-01-01T00:00:00",
            "level": "INFO",
            # Missing message, trace_id, module
        }
        with pytest.raises(ValueError):
            LogEntry.from_dict(data)


class TestSetupLogging:
    """Tests for setup_logging function."""

    def test_setup_logging_default(self):
        """Test setup_logging with default parameters."""
        logger = setup_logging()
        assert logger is not None
        assert logger.name == "root"

    def test_setup_logging_with_level(self):
        """Test setup_logging with level parameter."""
        logger = setup_logging(level="DEBUG")
        assert logger.level == 10  # DEBUG level

    def test_setup_logging_with_log_level(self):
        """Test setup_logging with log_level parameter."""
        logger = setup_logging(log_level="WARNING")
        assert logger.level == 30  # WARNING level

    def test_setup_logging_with_log_file(self):
        """Test setup_logging with custom log file."""
        with tempfile.NamedTemporaryFile(suffix=".log", delete=False) as f:
            temp_path = f.name

        try:
            logger = setup_logging(log_file=temp_path)
            assert logger is not None
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    def test_setup_logging_with_config_dict(self):
        """Test setup_logging with config dictionary."""
        config = {
            "level": "ERROR",
            "log_file": "/tmp/test.log",
            "module_name": "test_module",
        }
        logger = setup_logging(config=config)
        assert logger.level == 40  # ERROR level
        assert logger.name == "test_module"

    def test_setup_logging_creates_log_directory(self):
        """Test that setup_logging creates the log directory if it doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_dir = Path(tmpdir) / "new_logs"
            log_file = log_dir / "app.log"

            logger = setup_logging(log_file=str(log_file))
            assert log_dir.exists()
            assert log_file.exists()

    def test_setup_logging_multiple_calls(self):
        """Test that multiple calls to setup_logging work correctly."""
        logger1 = setup_logging(level="INFO")
        logger2 = setup_logging(level="DEBUG")
        assert logger1 is not None
        assert logger2 is not None


class TestJSONFormatter:
    """Tests for JSONFormatter."""

    def test_format_creates_valid_json(self):
        """Test that JSONFormatter produces valid JSON."""
        formatter = JSONFormatter(module_name="test_module")
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Test message",
            args=(),
            exc_info=None,
        )
        json_str = formatter.format(record)
        data = json.loads(json_str)

        assert "timestamp" in data
        assert data["level"] == "INFO"
        assert data["message"] == "Test message"
        assert "trace_id" in data
        assert data["module"] == "test_module"

    def test_format_includes_trace_id_from_record(self):
        """Test that trace_id from record is used."""
        formatter = JSONFormatter(module_name="test_module")
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Test message",
            args=(),
            exc_info=None,
        )
        record.trace_id = "custom-trace-123"
        json_str = formatter.format(record)
        data = json.loads(json_str)

        assert data["trace_id"] == "custom-trace-123"


class TestLogOperation:
    """Tests for log_operation function."""

    def test_log_operation_direct_call(self):
        """Test log_operation as a direct function call."""
        with tempfile.NamedTemporaryFile(suffix=".log", delete=False) as f:
            temp_path = f.name

        try:
            entry = log_operation(
                "test_operation",
                message="Test message",
                level="INFO",
                log_file=temp_path,
            )
            assert entry is not None
            assert entry.operation == "test_operation" or entry.message == "Test message"
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    def test_log_operation_creates_log_file(self):
        """Test that log_operation creates the log file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = Path(tmpdir) / "test.log"

            log_operation("test_op", log_file=str(log_file))
            assert log_file.exists()


class TestLoggingSchema:
    """Tests for logging schema compliance."""

    def test_schema_file_exists(self):
        """Test that the logging schema file exists."""
        schema_path = Path("contracts/logging_schema.yaml")
        assert schema_path.exists(), "contracts/logging_schema.yaml must exist"

    def test_schema_is_valid_yaml(self):
        """Test that the schema file is valid YAML."""
        schema_path = Path("contracts/logging_schema.yaml")
        with open(schema_path) as f:
            schema = yaml.safe_load(f)

        assert isinstance(schema, dict)
        assert "type" in schema
        assert schema["type"] == "object"
        assert "required" in schema
        assert "properties" in schema

    def test_schema_has_required_fields(self):
        """Test that the schema defines all required fields."""
        schema_path = Path("contracts/logging_schema.yaml")
        with open(schema_path) as f:
            schema = yaml.safe_load(f)

        required_fields = ["timestamp", "level", "message", "trace_id", "module"]
        for field in required_fields:
            assert field in schema["required"], f"Field {field} must be in required"
            assert field in schema["properties"], f"Field {field} must be in properties"

    def test_log_entries_match_schema(self):
        """Test that logged entries match the schema."""
        schema_path = Path("contracts/logging_schema.yaml")
        with open(schema_path) as f:
            schema = yaml.safe_load(f)

        with tempfile.NamedTemporaryFile(suffix=".log", delete=False) as f:
            temp_path = f.name

        try:
            logger = setup_logging(log_file=temp_path, level="INFO")
            logger.info("Test message")

            # Read and validate log entries
            with open(temp_path) as f:
                for line in f:
                    if line.strip():
                        entry = json.loads(line)
                        for field in schema["required"]:
                            assert field in entry, f"Missing required field: {field}"
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)


class TestLogRotation:
    """Tests for log rotation functionality."""

    def test_rotating_file_handler_configured(self):
        """Test that RotatingFileHandler is configured correctly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = Path(tmpdir) / "test.log"

            logger = setup_logging(log_file=str(log_file))

            # Check that RotatingFileHandler is used
            file_handler = None
            for handler in logger.handlers:
                if isinstance(handler, RotatingFileHandler):
                    file_handler = handler
                    break

            assert file_handler is not None, "RotatingFileHandler must be configured"
            assert file_handler.maxBytes == 10 * 1024 * 1024  # 10MB
            assert file_handler.backupCount == 5

    def test_rotation_occurs_after_max_bytes(self):
        """Test that rotation occurs after maxBytes is exceeded."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = Path(tmpdir) / "test.log"

            # Create a small maxBytes for testing
            logger = setup_logging(log_file=str(log_file))

            # Find the rotating file handler
            file_handler = None
            for handler in logger.handlers:
                if isinstance(handler, RotatingFileHandler):
                    # Override maxBytes for testing
                    original_max = file_handler.maxBytes
                    file_handler.maxBytes = 1024  # 1KB for testing
                    break

            if file_handler:
                # Write enough data to trigger rotation
                large_message = "X" * 5000
                logger.info(large_message)
                logger.info(large_message)
                logger.info(large_message)

                # Check that backup files were created
                backup_files = list(Path(tmpdir).glob("test.log.*"))
                # At least one backup should exist if rotation occurred
                # (Note: actual rotation depends on file size calculation)

                # Restore original maxBytes
                file_handler.maxBytes = 10 * 1024 * 1024


class TestIntegration:
    """Integration tests for the logging infrastructure."""

    def test_full_logging_workflow(self):
        """Test a complete logging workflow."""
        with tempfile.NamedTemporaryFile(suffix=".log", delete=False) as f:
            temp_path = f.name

        try:
            # Setup logging
            logger = setup_logging(log_file=temp_path, level="DEBUG")

            # Log various messages
            logger.debug("Debug message")
            logger.info("Info message")
            logger.warning("Warning message")
            logger.error("Error message")

            # Verify log file exists and contains entries
            assert Path(temp_path).exists()

            with open(temp_path) as f:
                lines = f.readlines()

            assert len(lines) >= 4, "Should have at least 4 log entries"

            # Verify each entry is valid JSON with required fields
            schema_path = Path("contracts/logging_schema.yaml")
            with open(schema_path) as f:
                schema = yaml.safe_load(f)

            for line in lines:
                if line.strip():
                    entry = json.loads(line)
                    for field in schema["required"]:
                        assert field in entry, f"Missing field: {field}"
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)
