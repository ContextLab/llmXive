"""Contract tests for logging interface."""
import logging
import tempfile
from pathlib import Path

import pytest

from code.utils.logger import setup_logger, log_negation_exclusion, log_abort_condition, get_logger


class TestLoggerContract:
    """Test suite for logging contract."""

    def test_setup_logger_produces_valid_logger(self):
        """Test that setup_logger produces a valid logger with handlers."""
        logger = setup_logger("contract_test_logger")

        # Must be a Logger instance
        assert isinstance(logger, logging.Logger)

        # Must have at least one handler
        assert len(logger.handlers) > 0, "Logger must have at least one handler"

        # Must have a name
        assert logger.name == "contract_test_logger"

    def test_get_logger_returns_singleton(self):
        """Test that get_logger returns the same instance for same name."""
        logger1 = get_logger("singleton_test")
        logger2 = get_logger("singleton_test")

        assert logger1 is logger2, "get_logger should return the same instance"

    def test_log_negation_exclusion_signature(self):
        """Test that log_negation_exclusion has the expected signature."""
        # Should accept logger, comment_id, keyword, window_size
        with tempfile.TemporaryDirectory() as tmp_dir:
            log_file = Path(tmp_dir) / "test.log"
            logger = setup_logger("sig_test", log_file=str(log_file))

            # This should not raise
            log_negation_exclusion(logger, "comment_123", "help", 5)

            # Verify it logged something
            assert log_file.exists()
            content = log_file.read_text()
            assert len(content) > 0

    def test_log_abort_condition_signature(self):
        """Test that log_abort_condition has the expected signature."""
        # Should accept logger, reason, task_id
        with tempfile.TemporaryDirectory() as tmp_dir:
            log_file = Path(tmp_dir) / "test.log"
            logger = setup_logger("abort_sig_test", log_file=str(log_file))

            # This should not raise
            log_abort_condition(logger, "Test abort reason", "T001")

            # Verify it logged something
            assert log_file.exists()
            content = log_file.read_text()
            assert "ABORT CONDITION" in content
            assert "Test abort reason" in content
            assert "T001" in content
