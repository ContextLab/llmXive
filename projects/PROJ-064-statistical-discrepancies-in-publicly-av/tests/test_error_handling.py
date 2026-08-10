"""
Tests for error handling utilities.
"""
import pytest
from code.exceptions import MissingDataError
from code.error_handling import validate_required_fields, handle_errors
from code.logger import setup_logging
import logging

# Setup logging for tests
setup_logging(console=True, level=logging.DEBUG)

def test_validate_required_fields_success():
    """Test validation passes when all fields are present."""
    data = {"a": 1, "b": 2}
    # Should not raise
    validate_required_fields(data, ["a", "b"], context="test_success")

def test_validate_required_fields_failure():
    """Test validation raises MissingDataError when fields are missing."""
    data = {"a": 1}
    with pytest.raises(MissingDataError) as exc_info:
        validate_required_fields(data, ["a", "b"], context="test_fail")
    
    assert "b" in str(exc_info.value)
    assert "test_fail" in str(exc_info.value)

def test_handle_errors_decorator_catches():
    """Test that handle_errors catches exceptions and returns fallback."""
    @handle_errors(fallback="default_value", reraise=False)
    def failing_func():
        raise ValueError("Intentional error")

    result = failing_func()
    assert result == "default_value"

def test_handle_errors_decorator_reraises():
    """Test that handle_errors re-raises if configured."""
    @handle_errors(reraise=True)
    def failing_func():
        raise ValueError("Intentional error")

    with pytest.raises(ValueError):
        failing_func()

def test_handle_errors_specific_exception():
    """Test handling of specific DiscrepancyError subclass."""
    @handle_errors(fallback="caught", reraise=False)
    def specific_fail():
        raise MissingDataError("Missing data")

    result = specific_fail()
    assert result == "caught"
