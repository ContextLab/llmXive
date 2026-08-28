"""
Unit tests for the logging infrastructure (T006).

Tests verify:
- Logging configuration creates the correct directory and file.
- Log messages contain expected formatted strings.
- Subject exclusion and processing step loggers work as intended.
"""
import os
import logging
import tempfile
from pathlib import Path
import pytest

# Import the functions to test
# Note: We mock get_project_root to use a temporary directory for testing
from config.logging_config import (
    setup_logging,
    get_logger,
    log_subject_exclusion,
    log_processing_step,
)
from unittest.mock import patch


class TestLoggingInfrastructure:
    @pytest.fixture
    def temp_project_root(self):
        """Create a temporary directory to act as project root."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @patch("config.logging_config.get_project_root")
    def test_setup_logging_creates_log_file(
        self, mock_get_root, temp_project_root, caplog
    ):
        """Test that setup_logging creates the log directory and file."""
        mock_get_root.return_value = temp_project_root

        # Clear handlers to ensure clean state
        logging.getLogger().handlers.clear()

        logger = setup_logging(console_output=False)

        log_dir = temp_project_root / "data" / "logs"
        assert log_dir.exists(), "Log directory should be created"

        log_file = log_dir / "pipeline.log"
        assert log_file.exists(), "Log file should be created"

    @patch("config.logging_config.get_project_root")
    def test_log_subject_exclusion_format(
        self, mock_get_root, temp_project_root, caplog
    ):
        """Test that subject exclusion logs are formatted correctly."""
        mock_get_root.return_value = temp_project_root
        logging.getLogger().handlers.clear()
        logger = setup_logging(console_output=False)

        subject_id = "123456"
        reason = "High motion"

        log_subject_exclusion(subject_id, reason, logger)

        # Check if the log message contains expected parts
        # caplog.text contains all logs in the current context
        assert f"SUBJECT_EXCLUDED" in caplog.text
        assert f"ID: {subject_id}" in caplog.text
        assert f"Reason: {reason}" in caplog.text
        assert "WARNING" in caplog.text

    @patch("config.logging_config.get_project_root")
    def test_log_processing_step_success(
        self, mock_get_root, temp_project_root, caplog
    ):
        """Test that processing step success logs are formatted correctly."""
        mock_get_root.return_value = temp_project_root
        logging.getLogger().handlers.clear()
        logger = setup_logging(console_output=False)

        step_name = "data_validation"
        status = "SUCCESS"
        details = "All checks passed"

        log_processing_step(step_name, status, details, logger)

        assert f"PROCESSING_STEP" in caplog.text
        assert step_name in caplog.text
        assert f"Status: {status}" in caplog.text
        assert f"Details: {details}" in caplog.text
        assert "INFO" in caplog.text

    @patch("config.logging_config.get_project_root")
    def test_log_processing_step_failure(
        self, mock_get_root, temp_project_root, caplog
    ):
        """Test that processing step failure logs are formatted correctly."""
        mock_get_root.return_value = temp_project_root
        logging.getLogger().handlers.clear()
        logger = setup_logging(console_output=False)

        step_name = "download_hcp"
        status = "FAILED"
        details = "Connection timeout"

        log_processing_step(step_name, status, details, logger)

        assert f"PROCESSING_STEP" in caplog.text
        assert step_name in caplog.text
        assert f"Status: {status}" in caplog.text
        assert "ERROR" in caplog.text

    @patch("config.logging_config.get_project_root")
    def test_get_logger_returns_configured_instance(
        self, mock_get_root, temp_project_root
    ):
        """Test that get_logger returns a valid logger instance."""
        mock_get_root.return_value = temp_project_root
        logging.getLogger().handlers.clear()
        setup_logging(console_output=False)

        logger = get_logger("test_module")
        assert isinstance(logger, logging.Logger)
        assert logger.name == "test_module"

        # Root logger
        root_logger = get_logger()
        assert isinstance(root_logger, logging.Logger)
        assert root_logger.name == "root"
