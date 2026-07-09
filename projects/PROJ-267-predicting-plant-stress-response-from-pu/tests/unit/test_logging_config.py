import logging
import os
import tempfile
from pathlib import Path

import pytest

# Import the module under test
# We need to mock the config import or ensure the test environment has it
# Since we are implementing T006, we assume config.py is available as per T004
from code.utils.logging_config import setup_logging, get_logger, log_warning
from code.utils.config import LOG_PATH, LOG_LEVEL


class TestLoggingInfrastructure:
    """
    Tests for the logging infrastructure setup (Task T006).

    These tests verify that:
    1. The log directory is created if missing.
    2. The rotating file handler is configured correctly.
    3. Log messages are written to the file.
    4. Console output works as expected.
    5. Sub-logers inherit configuration.
    """

    def test_setup_logging_creates_directory(self, tmp_path):
        """Verify that setup_logging creates the log directory if it doesn't exist."""
        # Arrange
        custom_log_path = tmp_path / "subdir" / "custom.log"
        assert not custom_log_path.parent.exists()

        # Act
        logger = setup_logging(log_file=str(custom_log_path), console=False)

        # Assert
        assert custom_log_path.parent.exists()
        assert isinstance(logger, logging.Logger)
        assert logger.name == "plant_stress_pipeline"

    def test_setup_logging_creates_file_on_write(self, tmp_path):
        """Verify that the log file is created when a message is logged."""
        # Arrange
        custom_log_path = tmp_path / "test.log"
        logger = setup_logging(log_file=str(custom_log_path), console=False)

        # Act
        logger.info("Test initialization message")

        # Assert
        assert custom_log_path.exists()
        assert custom_log_path.stat().st_size > 0

    def test_log_content_contains_expected_message(self, tmp_path):
        """Verify that specific log messages are written correctly."""
        # Arrange
        custom_log_path = tmp_path / "test.log"
        logger = setup_logging(log_file=str(custom_log_path), console=False)
        test_msg = "Warning: Dropped 3 rows due to missing data"

        # Act
        logger.warning(test_msg)

        # Assert
        with open(custom_log_path, "r") as f:
            content = f.read()

        assert test_msg in content
        assert "WARNING" in content

    def test_rotating_file_handler_configured(self, tmp_path):
        """Verify that a RotatingFileHandler is attached."""
        # Arrange
        custom_log_path = tmp_path / "test.log"
        logger = setup_logging(log_file=str(custom_log_path), console=False)

        # Act
        # Get the file handler
        file_handler = None
        for handler in logger.handlers:
            if isinstance(handler, logging.handlers.RotatingFileHandler):
                file_handler = handler
                break

        # Assert
        assert file_handler is not None, "RotatingFileHandler not found"
        assert file_handler.baseFilename == str(custom_log_path)

    def test_get_logger_returns_sublogger(self):
        """Verify that get_logger returns a named sub-logger."""
        # Arrange
        # Ensure main logger is set up first
        with tempfile.TemporaryDirectory() as tmp_dir:
            log_file = os.path.join(tmp_dir, "test.log")
            setup_logging(log_file=log_file, console=False)

            # Act
            sub_logger = get_logger("data_ingestion")

            # Assert
            assert sub_logger.name == "plant_stress_pipeline.data_ingestion"
            assert sub_logger.level == logging.NOTSET  # Inherits from parent
            assert sub_logger.parent.name == "plant_stress_pipeline"

    def test_log_warning_convenience_function(self, tmp_path):
        """Verify the convenience log_warning function works."""
        # Arrange
        custom_log_path = tmp_path / "test.log"
        setup_logging(log_file=str(custom_log_path), console=False)

        # Act
        log_warning("Convenience function test")

        # Assert
        with open(custom_log_path, "r") as f:
            content = f.read()

        assert "Convenience function test" in content

    def test_log_level_respected(self, tmp_path):
        """Verify that log messages below the threshold are not written."""
        # Arrange
        custom_log_path = tmp_path / "test.log"
        # Set level to WARNING, so INFO should be ignored
        logger = setup_logging(log_file=str(custom_log_path), console=False, level=logging.WARNING)

        # Act
        logger.info("This should be ignored")
        logger.warning("This should be logged")

        # Assert
        with open(custom_log_path, "r") as f:
            content = f.read()

        assert "This should be ignored" not in content
        assert "This should be logged" in content