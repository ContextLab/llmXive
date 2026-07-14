"""
Unit tests for schema validation utilities.
"""
import pytest
from dataclasses import dataclass
from typing import Optional
from code.utils.validation import validate_non_nulls, validate_schema_structure, filter_null_records
from code.utils.exceptions import SchemaMismatchError, DataInsufficientError


@dataclass
class MockRecord:
    """Mock dataclass for testing validation."""
    id: int
    value: Optional[float] = None
    name: Optional[str] = None


class TestValidateNonNulls:
    """Tests for validate_non_nulls function."""

    def test_all_valid_records(self):
        """Test validation with all records having non-null values."""
        records = [
            MockRecord(id=1, value=1.0, name="test1"),
            MockRecord(id=2, value=2.0, name="test2"),
        ]
        result = validate_non_nulls(records)
        assert result == 2

    def test_some_null_records(self):
        """Test validation with some records having null values."""
        records = [
            MockRecord(id=1, value=1.0, name="test1"),
            MockRecord(id=2, value=None, name="test2"),
            MockRecord(id=3, value=3.0, name="test3"),
        ]
        with pytest.raises(SchemaMismatchError):
            validate_non_nulls(records)

    def test_empty_records_list(self):
        """Test validation with empty list raises DataInsufficientError."""
        with pytest.raises(DataInsufficientError):
            validate_non_nulls([])

    def test_dict_records(self):
        """Test validation with dictionary records."""
        records = [
            {"id": 1, "value": 1.0, "name": "test1"},
            {"id": 2, "value": 2.0, "name": "test2"},
        ]
        result = validate_non_nulls(records)
        assert result == 2

    def test_dict_with_nulls(self):
        """Test validation with dictionary records containing nulls."""
        records = [
            {"id": 1, "value": 1.0, "name": "test1"},
            {"id": 2, "value": None, "name": "test2"},
        ]
        with pytest.raises(SchemaMismatchError):
            validate_non_nulls(records)


class TestValidateSchemaStructure:
    """Tests for validate_schema_structure function."""

    def test_valid_structure(self):
        """Test schema structure validation with correct fields."""
        records = [
            MockRecord(id=1, value=1.0, name="test1"),
        ]
        validate_schema_structure(records, required_fields={"id", "value", "name"})

    def test_missing_fields(self):
        """Test schema structure validation with missing fields."""
        records = [
            MockRecord(id=1, value=1.0),  # Missing 'name'
        ]
        with pytest.raises(SchemaMismatchError):
            validate_schema_structure(records, required_fields={"id", "value", "name"})

    def test_empty_records(self):
        """Test schema structure validation with empty list."""
        validate_schema_structure([], required_fields={"id"})


class TestFilterNullRecords:
    """Tests for filter_null_records function."""

    def test_filter_valid_only(self):
        """Test filtering keeps only valid records."""
        records = [
            MockRecord(id=1, value=1.0, name="test1"),
            MockRecord(id=2, value=None, name="test2"),
            MockRecord(id=3, value=3.0, name="test3"),
        ]
        filtered = filter_null_records(records)
        assert len(filtered) == 2
        assert filtered[0].id == 1
        assert filtered[1].id == 3

    def test_filter_all_valid(self):
        """Test filtering when all records are valid."""
        records = [
            MockRecord(id=1, value=1.0, name="test1"),
            MockRecord(id=2, value=2.0, name="test2"),
        ]
        filtered = filter_null_records(records)
        assert len(filtered) == 2

    def test_filter_all_invalid(self):
        """Test filtering when all records have nulls."""
        records = [
            MockRecord(id=1, value=None, name=None),
            MockRecord(id=2, value=None, name=None),
        ]
        filtered = filter_null_records(records)
        assert len(filtered) == 0

    def test_filter_empty_list(self):
        """Test filtering empty list."""
        filtered = filter_null_records([])
        assert filtered == []