"""Unit tests for logging utilities."""
import logging
import tempfile
from pathlib import Path

import pytest

from code.utils.logger import setup_logger, log_negation_exclusion, log_abort_condition, get_logger


class TestLogger:
    """Test suite for code/utils/logger.py."""

    def test_setup_logger_returns_logger(self):
        """Test that setup_logger returns a configured logger."""
        logger = setup_logger("test_logger")
        assert isinstance(logger, logging.Logger)
        assert logger.name == "test_logger"
        assert len(logger.handlers) > 0

    def test_get_logger_returns_existing_logger(self):
        """Test that get_logger returns the same logger instance."""
        logger1 = get_logger("shared_logger")
        logger2 = get_logger("shared_logger")
        assert logger1 is logger2

    def test_log_negation_exclusion(self, tmp_path):
        """Test that negation exclusion logging works."""
        # Create a temporary log file
        log_file = tmp_path / "test.log"
        logger = setup_logger("test_negation", log_file=str(log_file))

        # Log a negation exclusion
        log_negation_exclusion(logger, "test_comment", "test_word", 10)

        # Verify log file exists and has content
        assert log_file.exists()
        content = log_file.read_text()
        assert "Negation Exclusion" in content
        assert "test_comment" in content
        assert "test_word" in content

    def test_log_abort_condition(self, tmp_path):
        """Test that abort condition logging works."""
        # Create a temporary log file
        log_file = tmp_path / "test.log"
        logger = setup_logger("test_abort", log_file=str(log_file))

        # Log an abort condition
        log_abort_condition(logger, "Test abort reason", "T001")

        # Verify log file exists and has content
        assert log_file.exists()
        content = log_file.read_text()
        assert "ABORT CONDITION" in content
        assert "Test abort reason" in content
        assert "T001" in content
