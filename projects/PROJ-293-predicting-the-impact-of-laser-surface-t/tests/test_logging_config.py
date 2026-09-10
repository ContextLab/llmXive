"""
Tests for the logging configuration module.
"""
import os
import logging
import pytest
from pathlib import Path
import tempfile
import shutil

# Import the module functions
from code.logging_config import (
    setup_logging,
    get_logger,
    raise_on_missing_data,
    LOG_DIR,
    LOG_FILE
)

class TestLoggingSetup:
    """Tests for basic logging setup and configuration."""

    def test_setup_logging_creates_file(self, tmp_path):
        """Verify that setup_logging creates the log file and directory."""
        # Create a temporary directory for logs
        temp_log_dir = tmp_path / "logs"
        temp_log_file = temp_log_dir / "test_pipeline.log"

        # Setup logging to the temp location
        logger = setup_logging(log_file=temp_log_file)

        # Verify directory exists
        assert temp_log_dir.exists()
        assert temp_log_dir.is_dir()

        # Verify file exists after a log action
        logger.info("Test message")
        assert temp_log_file.exists()
        assert temp_log_file.stat().st_size > 0

    def test_setup_logging_sets_level(self):
        """Verify that the logger is set to INFO level."""
        logger = setup_logging(level=logging.WARNING)
        assert logger.level == logging.WARNING

    def test_get_logger_returns_configured_logger(self):
        """Verify get_logger returns the same instance."""
        logger1 = setup_logging()
        logger2 = get_logger()
        assert logger1 is logger2

    def test_log_file_in_correct_directory(self):
        """Verify default log file is in 'logs/' directory."""
        # This test assumes the project root is the current working directory
        # or that the test runner handles paths correctly.
        assert LOG_FILE.parent == Path("logs")
        assert LOG_FILE.name == "pipeline.log"

class TestRaiseOnMissingData:
    """Tests for the fail-loudly data validation."""

    def test_raise_on_missing_data_raises_value_error(self):
        """Verify that raise_on_missing_data raises ValueError."""
        with pytest.raises(ValueError) as excinfo:
            raise_on_missing_data(
                source_name="TestSource",
                source_identifier="ID_123"
            )
        
        assert "CRITICAL DATA MISSING" in str(excinfo.value)
        assert "TestSource" in str(excinfo.value)
        assert "ID_123" in str(excinfo.value)

    def test_raise_on_missing_data_logs_error(self, caplog):
        """Verify that the error is logged before raising."""
        logger = setup_logging()
        with caplog.at_level(logging.ERROR):
            with pytest.raises(ValueError):
                raise_on_missing_data(
                    source_name="TestSource",
                    source_identifier="ID_456"
                )
        
        assert "CRITICAL DATA MISSING" in caplog.text
        assert "TestSource" in caplog.text
        assert "ID_456" in caplog.text

    def test_raise_on_missing_data_custom_message(self):
        """Verify custom message overrides default."""
        custom_msg = "Specific custom error message"
        with pytest.raises(ValueError) as excinfo:
            raise_on_missing_data(
                source_name="TestSource",
                source_identifier="ID_789",
                message=custom_msg
            )
        
        assert custom_msg in str(excinfo.value)
        # Default message parts should not be present if custom is used
        assert "CRITICAL DATA MISSING" not in str(excinfo.value)