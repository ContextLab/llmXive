"""
Unit tests for the timeout wrapper module.
"""
import os
import sys
import time
import logging
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest

# Add the project root to the path to allow imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.src.utils.timeout_wrapper import (
    set_global_timeout,
    check_timeout,
    get_remaining_time_seconds,
    TimeoutExceeded,
    TimeoutContext,
    setup_timeout_logging,
    _log_timeout_warning
)

class TestTimeoutWrapper:
    """Test suite for timeout_wrapper functionality."""

    def test_setup_timeout_logging_creates_logger(self):
        """Test that setup_timeout_logging creates a logger and handlers."""
        logger = setup_timeout_logging()
        assert logger is not None
        assert logger.name == "llmXive.timeout"
        assert len(logger.handlers) > 0

    @patch('time.time')
    def test_set_global_timeout_sets_start_time(self, mock_time):
        """Test that set_global_timeout initializes start time and limit."""
        mock_time.return_value = 1000.0
        set_global_timeout(3600)

        # We can't easily access global _start_time directly without importing it again or mocking,
        # but we can verify the behavior via check_timeout
        assert get_remaining_time_seconds() is not None
        assert get_remaining_time_seconds() == 3600.0

    @patch('time.time')
    def test_check_timeout_returns_false_when_within_limit(self, mock_time):
        """Test that check_timeout returns False when time is within limit."""
        mock_time.return_value = 1000.0
        set_global_timeout(100) # Limit 100s

        mock_time.return_value = 1050.0 # Elapsed 50s
        assert check_timeout() is False

    @patch('time.time')
    def test_check_timeout_returns_true_when_exceeded(self, mock_time, caplog):
        """Test that check_timeout returns True when time is exceeded."""
        mock_time.return_value = 1000.0
        set_global_timeout(100) # Limit 100s

        mock_time.return_value = 1101.0 # Elapsed 101s
        with caplog.at_level(logging.WARNING):
            assert check_timeout() is True
            assert "Global timeout exceeded" in caplog.text

    @patch('time.time')
    def test_get_remaining_time_seconds(self, mock_time):
        """Test calculation of remaining time."""
        mock_time.return_value = 1000.0
        set_global_timeout(100)

        mock_time.return_value = 1080.0 # Elapsed 80s
        remaining = get_remaining_time_seconds()
        assert remaining == 20.0

        mock_time.return_value = 1100.0 # Elapsed 100s
        remaining = get_remaining_time_seconds()
        assert remaining == 0.0

        mock_time.return_value = 1150.0 # Elapsed 150s
        remaining = get_remaining_time_seconds()
        assert remaining == 0.0

    def test_timeout_context_exceeds(self):
        """Test that TimeoutContext raises TimeoutExceeded when limit is passed."""
        # We need to mock time to simulate the passage of time
        with patch('time.time') as mock_time:
            mock_time.return_value = 0.0
            ctx = TimeoutContext(5.0)

            # Check at t=0
            assert ctx.check() is False

            # Check at t=4
            mock_time.return_value = 4.0
            assert ctx.check() is False

            # Check at t=6 (should raise)
            mock_time.return_value = 6.0
            with pytest.raises(TimeoutExceeded):
                ctx.check()

    def test_timeout_context_within_limit(self):
        """Test that TimeoutContext does not raise when within limit."""
        with patch('time.time') as mock_time:
            mock_time.return_value = 0.0
            ctx = TimeoutContext(10.0)

            mock_time.return_value = 5.0
            assert ctx.check() is False
            assert ctx.expired is False

    def test_timeout_context_exited_properly(self):
        """Test that TimeoutContext context manager works correctly."""
        with patch('time.time') as mock_time:
            mock_time.return_value = 0.0
            try:
                with TimeoutContext(5.0) as ctx:
                    mock_time.return_value = 2.0
                    ctx.check()
            except TimeoutExceeded:
                assert False, "Should not have raised"

            # Now force a timeout inside the context
            mock_time.return_value = 6.0
            with pytest.raises(TimeoutExceeded):
                with TimeoutContext(5.0) as ctx:
                    ctx.check()

    @patch('code.src.utils.timeout_wrapper._log_timeout_warning')
    def test_log_timeout_warning_calls_logger(self, mock_log):
        """Test that internal logging function works."""
        _log_timeout_warning("Test message")
        mock_log.assert_called_once_with("Test message")