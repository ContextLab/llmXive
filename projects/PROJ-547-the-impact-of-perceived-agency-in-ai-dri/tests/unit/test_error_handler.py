"""
Unit tests for the error handling utilities.
"""
import sys
from unittest.mock import patch

import pytest

from utils.error_handler import PipelineError, handle_error, log_and_exit


def test_pipeline_error_init():
    """Test that PipelineError initializes correctly."""
    error = PipelineError("Test error", code=42)
    assert error.message == "Test error"
    assert error.code == 42
    assert str(error) == "Test error"


def test_handle_error_logs():
    """Test that handle_error logs the error message."""
    error = PipelineError("Test error", code=42)
    with patch("utils.error_handler.logger") as mock_logger:
        handle_error(error)
        mock_logger.error.assert_called_once()
        call_args = mock_logger.error.call_args[0][0]
        assert "Test error" in call_args
        assert "42" in call_args


def test_log_and_exit_exits():
    """Test that log_and_exit calls sys.exit."""
    error = PipelineError("Fatal error", code=99)
    with patch("utils.error_handler.logger") as mock_logger:
        with patch("utils.error_handler.sys.exit") as mock_exit:
            log_and_exit(error, exit_code=99)
            mock_logger.critical.assert_called()
            mock_exit.assert_called_once_with(99)
