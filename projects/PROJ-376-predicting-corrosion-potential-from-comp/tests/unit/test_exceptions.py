"""
Unit tests for custom exceptions in code/utils/exceptions.py.
"""

import pytest
from code.utils.exceptions import (
    CorrosionPipelineError,
    DataInsufficientError,
    SchemaMismatchError,
)


class TestCorrosionPipelineError:
    def test_base_exception_creation(self):
        """Test base exception can be created with a message."""
        exc = CorrosionPipelineError("Generic error")
        assert str(exc) == "Generic error"
        assert exc.message == "Generic error"
        assert exc.details == {}

    def test_base_exception_with_details(self):
        """Test base exception includes details in string representation."""
        exc = CorrosionPipelineError("Error occurred", details={"code": 500})
        assert "code=500" in str(exc)
        assert exc.details == {"code": 500}


class TestDataInsufficientError:
    def test_basic_creation(self):
        """Test creation with just a message."""
        exc = DataInsufficientError("Not enough data")
        assert "Not enough data" in str(exc)
        assert exc.details == {}

    def test_creation_with_record_count(self):
        """Test creation with record count and threshold."""
        exc = DataInsufficientError(
            "Insufficient records", record_count=400, threshold=500
        )
        assert "record_count=400" in str(exc)
        assert "threshold=500" in str(exc)
        assert exc.details["record_count"] == 400
        assert exc.details["threshold"] == 500

    def test_creation_with_missing_fields(self):
        """Test creation with missing fields list."""
        exc = DataInsufficientError(
            "Missing critical fields", missing_fields=["pH", "temp"]
        )
        assert "missing_fields=['pH', 'temp']" in str(exc)
        assert exc.details["missing_fields"] == ["pH", "temp"]

    def test_creation_with_source(self):
        """Test creation with source information."""
        exc = DataInsufficientError(
            "Source unavailable", source="NIST-IR-8200"
        )
        assert "source=NIST-IR-8200" in str(exc)
        assert exc.details["source"] == "NIST-IR-8200"

    def test_is_subclass_of_base(self):
        """Ensure DataInsufficientError inherits from CorrosionPipelineError."""
        assert issubclass(DataInsufficientError, CorrosionPipelineError)
        assert isinstance(DataInsufficientError("test"), CorrosionPipelineError)


class TestSchemaMismatchError:
    def test_basic_creation(self):
        """Test creation with just a message."""
        exc = SchemaMismatchError("Schema validation failed")
        assert "Schema validation failed" in str(exc)

    def test_creation_with_field_and_types(self):
        """Test creation with field name and type mismatch details."""
        exc = SchemaMismatchError(
            "Type mismatch",
            field_name="corrosion_rate",
            expected_type="float",
            actual_type="object",
        )
        assert "field=corrosion_rate" in str(exc)
        assert "expected_type=float" in str(exc)
        assert "actual_type=object" in str(exc)

    def test_creation_with_missing_columns(self):
        """Test creation with list of missing columns."""
        exc = SchemaMismatchError(
            "Missing required columns", missing_columns=["alloy_id", "date"]
        )
        assert "missing_columns=['alloy_id', 'date']" in str(exc)

    def test_creation_with_invalid_values(self):
        """Test creation with list of invalid values."""
        exc = SchemaMismatchError(
            "Invalid enum values", invalid_values=["invalid_ph", "NaN"]
        )
        assert "invalid_values=['invalid_ph', 'NaN']" in str(exc)

    def test_is_subclass_of_base(self):
        """Ensure SchemaMismatchError inherits from CorrosionPipelineError."""
        assert issubclass(SchemaMismatchError, CorrosionPipelineError)
        assert isinstance(SchemaMismatchError("test"), CorrosionPipelineError)


class TestExceptionRaising:
    """Test that exceptions can be raised and caught correctly."""

    def test_raise_and_catch_data_insufficient(self):
        """Test raising and catching DataInsufficientError."""
        with pytest.raises(DataInsufficientError) as exc_info:
            raise DataInsufficientError("Too few records", record_count=10)

        assert exc_info.value.record_count == 10
        assert "Too few records" in str(exc_info.value)

    def test_raise_and_catch_schema_mismatch(self):
        """Test raising and catching SchemaMismatchError."""
        with pytest.raises(SchemaMismatchError) as exc_info:
            raise SchemaMismatchError(
                "Bad schema", field_name="x", expected_type="int", actual_type="str"
            )

        assert exc_info.value.details["field"] == "x"
        assert "Bad schema" in str(exc_info.value)

    def test_catch_as_base_exception(self):
        """Test that specific exceptions can be caught as base exception."""
        with pytest.raises(CorrosionPipelineError):
            raise DataInsufficientError("Test", threshold=100)

        with pytest.raises(CorrosionPipelineError):
            raise SchemaMismatchError("Test", field_name="y")