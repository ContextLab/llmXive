"""
Unit tests for schema_validator.py
"""
import pytest
from code.schema_validator import (
    validate_record,
    validate_data,
    validate_date_format,
    SchemaValidationError,
    RAW_NEWS_SCHEMA
)

class TestDateValidation:
    def test_valid_date_format(self):
        assert validate_date_format("2023-01-15") is True
        assert validate_date_format("2023-12-31") is True
        assert validate_date_format("2000-01-01") is True

    def test_invalid_date_format(self):
        assert validate_date_format("2023-1-15") is False  # Single digit month
        assert validate_date_format("2023/01/15") is False  # Wrong separator
        assert validate_date_format("15-01-2023") is False  # Wrong order
        assert validate_date_format("2023-13-01") is False  # Invalid month
        assert validate_date_format("2023-01-32") is False  # Invalid day
        assert validate_date_format("not-a-date") is False
        assert validate_date_format(20230115) is False  # Not a string

class TestRecordValidation:
    def test_valid_record(self):
        record = {
            "date": "2023-01-15",
            "value": -45.5,
            "source": "GDELT"
        }
        errors = validate_record(record, RAW_NEWS_SCHEMA)
        assert len(errors) == 0

    def test_missing_required_field_date(self):
        record = {
            "value": -45.5,
            "source": "GDELT"
        }
        errors = validate_record(record, RAW_NEWS_SCHEMA)
        assert any("date" in e and "Missing required" in e for e in errors)

    def test_missing_required_field_value(self):
        record = {
            "date": "2023-01-15",
            "source": "GDELT"
        }
        errors = validate_record(record, RAW_NEWS_SCHEMA)
        assert any("value" in e and "Missing required" in e for e in errors)

    def test_missing_required_field_source(self):
        record = {
            "date": "2023-01-15",
            "value": -45.5
        }
        errors = validate_record(record, RAW_NEWS_SCHEMA)
        assert any("source" in e and "Missing required" in e for e in errors)

    def test_invalid_date_format_in_record(self):
        record = {
            "date": "2023/01/15",
            "value": -45.5,
            "source": "GDELT"
        }
        errors = validate_record(record, RAW_NEWS_SCHEMA)
        assert any("date" in e and "valid ISO8601" in e for e in errors)

    def test_invalid_value_type(self):
        record = {
            "date": "2023-01-15",
            "value": "not-a-number",
            "source": "GDELT"
        }
        errors = validate_record(record, RAW_NEWS_SCHEMA)
        assert any("value" in e and "number" in e for e in errors)

    def test_invalid_source_type(self):
        record = {
            "date": "2023-01-15",
            "value": -45.5,
            "source": 12345
        }
        errors = validate_record(record, RAW_NEWS_SCHEMA)
        assert any("source" in e and "string" in e for e in errors)

class TestDataValidation:
    def test_validate_data_single_valid_record(self):
        record = {
            "date": "2023-01-15",
            "value": -45.5,
            "source": "GDELT"
        }
        assert validate_data(record) is True

    def test_validate_data_list_valid_records(self):
        records = [
            {"date": "2023-01-15", "value": -45.5, "source": "GDELT"},
            {"date": "2023-01-16", "value": 10.2, "source": "GDELT"}
        ]
        assert validate_data(records) is True

    def test_validate_data_invalid_record_raises(self):
        records = [
            {"date": "2023-01-15", "value": -45.5, "source": "GDELT"},
            {"date": "invalid", "value": 10.2, "source": "GDELT"}
        ]
        with pytest.raises(SchemaValidationError):
            validate_data(records)

    def test_validate_data_non_dict_record_raises(self):
        records = ["not a dict"]
        with pytest.raises(SchemaValidationError):
            validate_data(records)