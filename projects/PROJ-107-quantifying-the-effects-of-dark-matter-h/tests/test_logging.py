"""
Unit tests for the logging infrastructure.
Tests verify that the logger initializes correctly, writes to file,
and logs messages at various levels.
"""
import os
import sys
import tempfile
import shutil
from pathlib import Path
import logging
import pytest

# Ensure code/ is in path
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from utils.logging import (
    get_pipeline_logger,
    log_pipeline_start,
    log_pipeline_end,
    log_error,
    log_metric,
    get_log_file_path,
    _logger as global_logger
)
from utils.config import get_project_root

class TestLoggingInfrastructure:
    """Tests for the base logging infrastructure."""

    @pytest.fixture(autouse=True)
    def setup_and_teardown(self):
        """Setup and teardown for each test to avoid logger state conflicts."""
        # Save original state
        original_logger = global_logger
        original_handlers = []
        if original_logger:
            original_handlers = original_logger.handlers.copy()
            original_logger.handlers.clear()

        yield

        # Restore state
        if original_logger:
            original_logger.handlers.clear()
            original_logger.handlers.extend(original_handlers)
        # Reset module-level globals if needed (handled by fixture logic in real scenario)
        # For this test, we rely on the fixture to clear handlers

    def test_logger_initialization(self):
        """Test that the logger initializes with correct settings."""
        logger = get_pipeline_logger(name="test_logger", level="INFO", console=False)
        
        assert logger is not None
        assert logger.name == "test_logger"
        assert logger.level == logging.INFO
        
        # Should have at least one handler (file)
        assert len(logger.handlers) >= 1

    def test_console_and_file_handlers(self):
        """Test that logger has both console and file handlers when requested."""
        logger = get_pipeline_logger(name="test_both", level="DEBUG", console=True)
        
        handler_types = [type(h).__name__ for h in logger.handlers]
        assert "StreamHandler" in handler_types
        assert "FileHandler" in handler_types

    def test_log_file_creation(self):
        """Test that the log file is created on disk."""
        logger = get_pipeline_logger(name="test_file", level="INFO", console=False)
        log_path = get_log_file_path()
        
        assert log_path is not None
        assert log_path.exists()
        assert log_path.suffix == ".log"

    def test_log_message_content(self, caplog):
        """Test that log messages contain expected content."""
        logger = get_pipeline_logger(name="test_content", level="INFO", console=True)
        
        with caplog.at_level(logging.INFO):
            logger.info("Test message")
        
        assert "Test message" in caplog.text

    def test_log_pipeline_start(self, caplog):
        """Test the log_pipeline_start utility function."""
        with caplog.at_level(logging.INFO):
            log_pipeline_start("T006", {"key": "value"})
        
        assert "TASK START: T006" in caplog.text
        assert "key" in caplog.text

    def test_log_pipeline_end(self, caplog):
        """Test the log_pipeline_end utility function."""
        with caplog.at_level(logging.INFO):
            log_pipeline_end("T006", "SUCCESS", duration_seconds=10.5)
        
        assert "TASK END: T006" in caplog.text
        assert "SUCCESS" in caplog.text
        assert "10.50s" in caplog.text

    def test_log_error(self, caplog):
        """Test the log_error utility function."""
        test_error = ValueError("Test error")
        
        with caplog.at_level(logging.ERROR):
            log_error("T006", test_error, context={"step": "init"})
        
        assert "ERROR in T006" in caplog.text
        assert "ValueError" in caplog.text
        assert "Test error" in caplog.text
        assert "step" in caplog.text

    def test_log_metric(self, caplog):
        """Test the log_metric utility function."""
        with caplog.at_level(logging.INFO):
            log_metric("T006", "accuracy", 0.95, unit="ratio")
        
        assert "Metric: accuracy = 0.95" in caplog.text
        assert "(ratio)" in caplog.text

    def test_log_metric_no_unit(self, caplog):
        """Test log_metric without a unit."""
        with caplog.at_level(logging.INFO):
            log_metric("T006", "count", 100)
        
        assert "Metric: count = 100" in caplog.text
        assert "()" not in caplog.text

    def test_different_log_levels(self, caplog):
        """Test that different log levels are respected."""
        logger = get_pipeline_logger(name="test_levels", level="WARNING", console=True)
        
        with caplog.at_level(logging.DEBUG):
            logger.debug("Debug message")
            logger.info("Info message")
            logger.warning("Warning message")
            logger.error("Error message")
        
        # Only WARNING and ERROR should appear
        assert "Debug message" not in caplog.text
        assert "Info message" not in caplog.text
        assert "Warning message" in caplog.text
        assert "Error message" in caplog.text

    def test_singleton_behavior(self):
        """Test that get_pipeline_logger returns the same instance."""
        logger1 = get_pipeline_logger(name="test_singleton", level="INFO", console=False)
        logger2 = get_pipeline_logger(name="test_singleton", level="DEBUG", console=False)
        
        # Should be the same instance
        assert logger1 is logger2
        # Level should remain as first set (INFO), not changed by second call
        assert logger1.level == logging.INFO
