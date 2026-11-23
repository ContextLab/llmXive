"""
Unit tests for the logging infrastructure (T017).
"""

import pytest
import logging
import os
import tempfile
from pathlib import Path

# Import the logger module
from code.utils.logger import setup_logging, get_logger


class TestLoggerInitialization:
    """Tests for logger initialization and configuration."""

    def test_setup_logging_creates_file(self, tmp_path):
        """Test that setup_logging creates the log file."""
        log_file = tmp_path / "test_pipeline.log"
        logger = setup_logging(str(log_file))

        assert logger is not None
        assert log_file.exists()

    def test_setup_logging_returns_logger(self, tmp_path):
        """Test that setup_logging returns a valid logger instance."""
        log_file = tmp_path / "test_pipeline.log"
        logger = setup_logging(str(log_file))

        assert isinstance(logger, logging.Logger)
        assert logger.name == "pipeline"

    def test_setup_logging_sets_level(self, tmp_path):
        """Test that setup_logging respects the level parameter."""
        log_file = tmp_path / "test_pipeline.log"

        # Test with DEBUG level
        logger_debug = setup_logging(str(log_file), level=logging.DEBUG)
        assert logger_debug.level == logging.DEBUG

    def test_get_logger_raises_before_init(self):
        """Test that get_logger raises RuntimeError if not initialized."""
        # Reset the global logger
        import code.utils.logger as logger_module
        original_logger = logger_module._logger
        logger_module._logger = None

        try:
            with pytest.raises(RuntimeError) as exc_info:
                get_logger()
            assert "Logger not initialized" in str(exc_info.value)
        finally:
            # Restore original state
            logger_module._logger = original_logger

    def test_get_logger_returns_initialized_logger(self, tmp_path):
        """Test that get_logger returns the initialized logger."""
        log_file = tmp_path / "test_pipeline.log"
        setup_logging(str(log_file))

        logger = get_logger()
        assert logger is not None
        assert isinstance(logger, logging.Logger)

    def test_logging_writes_to_file(self, tmp_path):
        """Test that log messages are written to the file."""
        log_file = tmp_path / "test_pipeline.log"
        logger = setup_logging(str(log_file))

        # Log a message
        test_message = "Test log message"
        logger.info(test_message)

        # Check file exists and contains the message
        assert log_file.exists()
        content = log_file.read_text()
        assert test_message in content

    def test_logging_writes_to_console(self, tmp_path, caplog):
        """Test that log messages are written to console."""
        log_file = tmp_path / "test_pipeline.log"
        logger = setup_logging(str(log_file))

        # Capture console output
        with caplog.at_level(logging.INFO):
            logger.info("Console test message")

        assert "Console test message" in caplog.text

    def test_multiple_calls_return_same_logger(self, tmp_path):
        """Test that multiple calls to setup_logging return the same logger."""
        log_file = tmp_path / "test_pipeline.log"
        logger1 = setup_logging(str(log_file))
        logger2 = setup_logging(str(log_file))

        assert logger1 is logger2

    def test_default_log_path(self, tmp_path, monkeypatch):
        """Test that default log path is used when no path is provided."""
        # Mock the project root
        project_root = tmp_path / "project"
        project_root.mkdir()
        data_results = project_root / "data" / "results"
        data_results.mkdir(parents=True)

        # Change working directory to project root
        monkeypatch.chdir(project_root)

        # Mock __file__ to point to code/utils/logger.py
        original_file = __file__ if '__file__' in globals() else str(Path.cwd() / "test.py")

        # Reset logger state
        import code.utils.logger as logger_module
        logger_module._logger = None

        # Call setup_logging without path
        logger = setup_logging()

        # Verify log file was created in default location
        expected_log = data_results / "pipeline_run.log"
        assert expected_log.exists()
