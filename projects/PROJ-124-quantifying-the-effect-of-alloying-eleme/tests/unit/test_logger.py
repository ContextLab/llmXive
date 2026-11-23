"""
Unit tests for the logging infrastructure.
"""
import pytest
import logging
import os
import sys
from pathlib import Path
from datetime import datetime
import yaml

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from utils.logger import (
    PipelineError,
    get_logger,
    log_pipeline_start,
    log_pipeline_end,
    handle_pipeline_error
)


class TestPipelineError:
    """Tests for the PipelineError exception."""

    def test_pipeline_error_basic(self):
        """Test basic PipelineError creation."""
        error = PipelineError("Test message")
        assert str(error) == "Test message"
        assert error.stage is None
        assert error.details == {}

    def test_pipeline_error_with_stage(self):
        """Test PipelineError with stage."""
        error = PipelineError("Test message", stage="data_ingestion")
        assert error.stage == "data_ingestion"

    def test_pipeline_error_with_details(self):
        """Test PipelineError with details."""
        details = {"key": "value", "count": 42}
        error = PipelineError("Test message", details=details)
        assert error.details == details


class TestGetLogger:
    """Tests for the get_logger function."""

    def test_logger_creation(self):
        """Test that a logger is created successfully."""
        logger = get_logger("test_logger_1")
        assert isinstance(logger, logging.Logger)
        assert logger.name == "test_logger_1"
        assert logger.level == logging.INFO

    def test_logger_handlers(self):
        """Test that logger has both console and file handlers."""
        logger = get_logger("test_logger_2")
        handlers = logger.handlers
        assert len(handlers) == 2  # Console and File

    def test_log_directory_creation(self):
        """Test that the logs directory is created."""
        logger = get_logger("test_logger_3")
        log_dir = Path("logs")
        assert log_dir.exists()
        assert log_dir.is_dir()

    def test_log_file_creation(self):
        """Test that a log file is created."""
        logger = get_logger("test_logger_4")
        log_dir = Path("logs")
        log_files = list(log_dir.glob("pipeline_*.log"))
        assert len(log_files) > 0

    def test_logger_reuse(self):
        """Test that calling get_logger twice returns the same logger."""
        logger1 = get_logger("test_logger_5")
        logger2 = get_logger("test_logger_5")
        assert logger1 is logger2


class TestLogPipelineStart:
    """Tests for log_pipeline_start function."""

    def test_log_start_format(self, caplog):
        """Test that pipeline start is logged correctly."""
        logger = get_logger("test_start_logger")
        with caplog.at_level(logging.INFO):
            log_pipeline_start(logger, "T006", "Test task description")

        # Check that the log contains expected elements
        assert "PIPELINE START" in caplog.text
        assert "T006" in caplog.text
        assert "Test task description" in caplog.text


class TestLogPipelineEnd:
    """Tests for log_pipeline_end function."""

    def test_log_end_success(self, caplog):
        """Test that pipeline end success is logged correctly."""
        logger = get_logger("test_end_logger")
        with caplog.at_level(logging.INFO):
            log_pipeline_end(logger, "T006", success=True, duration_seconds=10.5)

        assert "PIPELINE END" in caplog.text
        assert "SUCCESS" in caplog.text
        assert "10.50" in caplog.text

    def test_log_end_failure(self, caplog):
        """Test that pipeline end failure is logged correctly."""
        logger = get_logger("test_end_logger_2")
        with caplog.at_level(logging.INFO):
            log_pipeline_end(logger, "T006", success=False)

        assert "PIPELINE END" in caplog.text
        assert "FAILED" in caplog.text


class TestHandlePipelineError:
    """Tests for handle_pipeline_error function."""

    def test_error_logging(self, caplog):
        """Test that errors are logged correctly."""
        logger = get_logger("test_error_logger")
        try:
            raise ValueError("Test error message")
        except Exception as e:
            with caplog.at_level(logging.ERROR):
                with pytest.raises(ValueError):
                    handle_pipeline_error(logger, e, "T006", "test_stage")

        assert "PIPELINE ERROR" in caplog.text
        assert "ValueError" in caplog.text
        assert "Test error message" in caplog.text

    def test_state_file_update(self):
        """Test that state file is updated on error."""
        logger = get_logger("test_state_logger")
        state_file = Path("state") / "pipeline_status.yaml"

        # Clean up any existing state file
        if state_file.exists():
            state_file.unlink()

        try:
            raise RuntimeError("Test runtime error")
        except Exception as e:
            with pytest.raises(RuntimeError):
                handle_pipeline_error(logger, e, "T006", "test_stage")

        # Verify state file was created and contains expected data
        assert state_file.exists()

        with open(state_file, 'r') as f:
            data = yaml.safe_load(f)

        assert "T006" in data
        assert data["T006"]["status"] == "failed"
        assert data["T006"]["error_type"] == "RuntimeError"
        assert "Test runtime error" in data["T006"]["error_message"]

    def test_exception_re_raised(self):
        """Test that the original exception is re-raised."""
        logger = get_logger("test_reraise_logger")
        original_error = ValueError("Original error")

        with pytest.raises(ValueError) as exc_info:
            handle_pipeline_error(logger, original_error, "T006")

        assert exc_info.value is original_error

    def test_missing_state_directory(self):
        """Test that state directory is created if missing."""
        logger = get_logger("test_missing_dir_logger")
        state_dir = Path("state")

        # Remove state directory if it exists
        if state_dir.exists():
            import shutil
            shutil.rmtree(state_dir)

        try:
            raise KeyError("Test key error")
        except Exception as e:
            with pytest.raises(KeyError):
                handle_pipeline_error(logger, e, "T006")

        assert state_dir.exists()
        assert state_dir.is_dir()