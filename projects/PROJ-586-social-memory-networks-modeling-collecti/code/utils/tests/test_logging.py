"""
Tests for the logging utility module.

These tests verify that logging is properly configured with timestamps
and writes to the expected log file.
"""

import logging
import os
import tempfile
from pathlib import Path
import pytest

from utils.logging import (
    setup_logger,
    get_logger,
    log_experiment_start,
    log_experiment_end,
    info,
    warning,
    error,
    debug,
    critical,
    DEFAULT_LOG_FILE,
    LOG_FORMAT,
)


class TestLoggingSetup:
    """Tests for logger setup and configuration."""

    def test_setup_logger_returns_logger(self):
        """Test that setup_logger returns a valid Logger instance."""
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = setup_logger(
                name="test_logger",
                log_file="test.log",
                output_dir=tmpdir,
            )
            assert isinstance(logger, logging.Logger)
            assert logger.name == "test_logger"

    def test_setup_logger_creates_log_file(self):
        """Test that setup_logger creates the log file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = Path(tmpdir) / DEFAULT_LOG_FILE
            logger = setup_logger(output_dir=tmpdir)

            # Trigger a log write
            logger.info("Test message")

            assert log_path.exists()

    def test_setup_logger_with_timestamp_format(self):
        """Test that log format includes timestamp."""
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = setup_logger(output_dir=tmpdir)
            logger.info("Test message")

            # Read log file and verify format
            log_path = Path(tmpdir) / DEFAULT_LOG_FILE
            with open(log_path, "r") as f:
                log_content = f.read()

            # Verify timestamp is present (YYYY-MM-DD HH:MM:SS format)
            assert "20" in log_content  # Year starts with 20
            assert ":" in log_content  # Time has colons
            assert "INFO" in log_content
            assert "Test message" in log_content

    def test_setup_logger_idempotent(self):
        """Test that calling setup_logger multiple times returns same logger."""
        with tempfile.TemporaryDirectory() as tmpdir:
            logger1 = setup_logger(name="idempotent_test", output_dir=tmpdir)
            logger2 = setup_logger(name="idempotent_test", output_dir=tmpdir)

            assert logger1 is logger2
            # Should only have one file handler
            file_handlers = [h for h in logger1.handlers if isinstance(h, logging.FileHandler)]
            assert len(file_handlers) == 1


class TestGetLogger:
    """Tests for get_logger function."""

    def test_get_logger_creates_new_logger(self):
        """Test that get_logger creates a new logger when none exists."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Remove any existing handler by creating fresh logger
            logger_name = "fresh_logger"
            if logger_name in logging.Logger.manager.loggerDict:
                del logging.Logger.manager.loggerDict[logger_name]

            logger = get_logger(name=logger_name)
            assert isinstance(logger, logging.Logger)

    def test_get_logger_returns_existing(self):
        """Test that get_logger returns existing logger."""
        with tempfile.TemporaryDirectory() as tmpdir:
            logger1 = setup_logger(name="existing_logger", output_dir=tmpdir)
            logger2 = get_logger(name="existing_logger")

            assert logger1 is logger2


class TestLoggingFunctions:
    """Tests for convenience logging functions."""

    def test_info_logs_message(self):
        """Test that info function logs message."""
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = setup_logger(name="info_test", output_dir=tmpdir)

            info("Test info message", logger=logger)

            log_path = Path(tmpdir) / DEFAULT_LOG_FILE
            with open(log_path, "r") as f:
                content = f.read()

            assert "Test info message" in content
            assert "INFO" in content

    def test_warning_logs_message(self):
        """Test that warning function logs message."""
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = setup_logger(name="warning_test", output_dir=tmpdir)

            warning("Test warning message", logger=logger)

            log_path = Path(tmpdir) / DEFAULT_LOG_FILE
            with open(log_path, "r") as f:
                content = f.read()

            assert "Test warning message" in content
            assert "WARNING" in content

    def test_error_logs_message(self):
        """Test that error function logs message."""
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = setup_logger(name="error_test", output_dir=tmpdir)

            error("Test error message", logger=logger)

            log_path = Path(tmpdir) / DEFAULT_LOG_FILE
            with open(log_path, "r") as f:
                content = f.read()

            assert "Test error message" in content
            assert "ERROR" in content

    def test_debug_logs_message(self):
        """Test that debug function logs message."""
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = setup_logger(name="debug_test", output_dir=tmpdir, level=logging.DEBUG)

            debug("Test debug message", logger=logger)

            log_path = Path(tmpdir) / DEFAULT_LOG_FILE
            with open(log_path, "r") as f:
                content = f.read()

            assert "Test debug message" in content
            assert "DEBUG" in content

    def test_critical_logs_message(self):
        """Test that critical function logs message."""
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = setup_logger(name="critical_test", output_dir=tmpdir)

            critical("Test critical message", logger=logger)

            log_path = Path(tmpdir) / DEFAULT_LOG_FILE
            with open(log_path, "r") as f:
                content = f.read()

            assert "Test critical message" in content
            assert "CRITICAL" in content


class TestExperimentLogging:
    """Tests for experiment start/end logging."""

    def test_log_experiment_start(self):
        """Test that log_experiment_start logs experiment start."""
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = setup_logger(name="exp_start_test", output_dir=tmpdir)

            log_experiment_start(
                "test_experiment",
                config={"param1": "value1", "param2": 42},
                logger=logger,
            )

            log_path = Path(tmpdir) / DEFAULT_LOG_FILE
            with open(log_path, "r") as f:
                content = f.read()

            assert "EXPERIMENT START" in content
            assert "test_experiment" in content
            assert "param1" in content
            assert "value1" in content
            assert "param2" in content
            assert "42" in content

    def test_log_experiment_end_success(self):
        """Test that log_experiment_end logs success."""
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = setup_logger(name="exp_end_test", output_dir=tmpdir)

            log_experiment_end("test_experiment", success=True, logger=logger)

            log_path = Path(tmpdir) / DEFAULT_LOG_FILE
            with open(log_path, "r") as f:
                content = f.read()

            assert "EXPERIMENT END" in content
            assert "SUCCESS" in content

    def test_log_experiment_end_failure(self):
        """Test that log_experiment_end logs failure."""
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = setup_logger(name="exp_end_fail_test", output_dir=tmpdir)

            log_experiment_end("test_experiment", success=False, logger=logger)

            log_path = Path(tmpdir) / DEFAULT_LOG_FILE
            with open(log_path, "r") as f:
                content = f.read()

            assert "EXPERIMENT END" in content
            assert "FAILED" in content


class TestLogFilePath:
    """Tests for log file path configuration."""

    def test_custom_log_file_name(self):
        """Test that custom log file name is used."""
        with tempfile.TemporaryDirectory() as tmpdir:
            custom_name = "custom_experiment.log"
            logger = setup_logger(
                name="custom_name_test",
                log_file=custom_name,
                output_dir=tmpdir,
            )
            logger.info("Test")

            log_path = Path(tmpdir) / custom_name
            assert log_path.exists()

    def test_custom_output_directory(self):
        """Test that custom output directory is used."""
        with tempfile.TemporaryDirectory() as tmpdir:
            subdir = Path(tmpdir) / "logs"
            logger = setup_logger(
                name="custom_dir_test",
                output_dir=subdir,
            )
            logger.info("Test")

            log_path = subdir / DEFAULT_LOG_FILE
            assert log_path.exists()

    def test_creates_nested_directories(self):
        """Test that nested directories are created."""
        with tempfile.TemporaryDirectory() as tmpdir:
            nested_dir = Path(tmpdir) / "deep" / "nested" / "logs"
            logger = setup_logger(
                name="nested_dir_test",
                output_dir=nested_dir,
            )
            logger.info("Test")

            log_path = nested_dir / DEFAULT_LOG_FILE
            assert log_path.exists()
