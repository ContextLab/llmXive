"""
Unit tests for the error_handler module.
"""

import pytest

from utils.error_handler import PipelineError, handle_error, log_and_exit


def test_pipeline_error_initialization():
    """Test that PipelineError initializes correctly."""
    error = PipelineError("Test error", code=5)
    assert error.message == "Test error"
    assert error.code == 5
    assert str(error) == "Test error"


def test_handle_error():
    """Test that handle_error logs and raises PipelineError."""
    original_error = ValueError("Original")
    with pytest.raises(PipelineError) as exc_info:
        handle_error(original_error, "Custom message", code=2)

    assert exc_info.value.message == "Custom message"
    assert exc_info.value.code == 2
    assert exc_info.value.__cause__ is original_error


def test_handle_error_default_message():
    """Test that handle_error uses exception message if none provided."""
    original_error = ValueError("Original error message")
    with pytest.raises(PipelineError) as exc_info:
        handle_error(original_error)

    assert exc_info.value.message == "Original error message"
    assert exc_info.value.__cause__ is original_error
