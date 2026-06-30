"""
Tests for custom exceptions defined in code/errors.py.
"""
import pytest
from code.errors import DataMissingCreativityError


def test_data_missing_creativity_error_basic():
    """Test basic instantiation of the custom exception."""
    exc = DataMissingCreativityError("Creativity data missing")
    assert str(exc) == "Creativity data missing"
    assert exc.error_code == "DATA_MISSING_CREATIVITY"
    assert exc.missing_field is None


def test_data_missing_creativity_error_with_field():
    """Test instantiation with a specific missing field."""
    exc = DataMissingCreativityError("CAQ scores not found", missing_field="caq_score")
    assert str(exc) == "CAQ scores not found"
    assert exc.error_code == "DATA_MISSING_CREATIVITY"
    assert exc.missing_field == "caq_score"


def test_data_missing_creativity_error_is_exception():
    """Test that the custom exception is a subclass of Exception."""
    assert issubclass(DataMissingCreativityError, Exception)


def test_data_missing_creativity_error_can_be_raised_and_caught():
    """Test that the exception can be raised and caught properly."""
    with pytest.raises(DataMissingCreativityError) as exc_info:
        raise DataMissingCreativityError("Test error", missing_field="test_field")

    assert exc_info.value.error_code == "DATA_MISSING_CREATIVITY"
    assert exc_info.value.missing_field == "test_field"