"""
Tests for custom exceptions.
"""
import pytest
from code.exceptions import (
    DiscrepancyError,
    DataAcquisitionError,
    MissingDataError,
    ValidationFailureError,
    StatisticalModelError,
    ConfigurationError
)

def test_base_exception():
    """Test that base exception can be raised and caught."""
    with pytest.raises(DiscrepancyError):
        raise DiscrepancyError("Base error")

def test_subclass_inheritance():
    """Test that all custom exceptions inherit from DiscrepancyError."""
    exceptions = [
        DataAcquisitionError,
        MissingDataError,
        ValidationFailureError,
        StatisticalModelError,
        ConfigurationError
    ]
    for exc_class in exceptions:
        with pytest.raises(DiscrepancyError):
            raise exc_class("Specific error")

def test_exception_messages():
    """Test that exceptions preserve error messages."""
    msg = "Custom error message"
    try:
        raise MissingDataError(msg)
    except MissingDataError as e:
        assert str(e) == msg
