"""
Unit tests for validation.py utilities.
"""

import json
import os
import tempfile
from pathlib import Path

import pytest

from utils.validation import (
    validate_field_type,
    validate_record_against_schema,
    validate_jsonl_against_schema,
    validate_dataset_artifact,
    generate_validation_report,
)


class TestValidateFieldType:
    def test_string_type(self):
        assert validate_field_type("hello", "string") is True
        assert validate_field_type(123, "string") is False

    def test_integer_type(self):
        assert validate_field_type(42, "integer") is True
        assert validate_field_type(3.14, "integer") is False
        assert validate_field_type("42", "integer") is False

    def test_number_type(self):
        assert validate_field_type(42, "number") is True
        assert validate_field_type(3.14, "number") is True
        assert validate_field_type("42", "number") is False

    def test_boolean_type(self):
        assert validate_field_type(True, "boolean") is True
        assert validate_field_type(False, "boolean") is True
        assert validate_field_type(1, "boolean") is False

    def test_array_type(self):
        assert validate_field_type([1, 2, 3], "array") is True
        assert validate_field_type("array", "array") is False

    def test_object_type(self):
        assert validate_field_type({"key": "value"}, "object") is True
        assert validate_field_type([], "object") is False

    def test_null_type(self):
        assert validate_field_type(None, "null") is True
        assert validate_field_type("", "null") is False


class TestValidateRecordAgainstSchema:
    @pytest.fixture
    def sample_schema(self):
        return {
            "type": "object",
            "properties": {
                "id": {"type": "integer"},
                "name": {"type": "string", "minLength": 1},
                "score": {"type": "number", "minimum": 0, "maximum": 100},
                "tags": {"type": "array", "minItems": 1},
            },
            "required": ["id", "name"],
        }

    def test_valid_record(self, sample_schema):
        record = {"id": 1, "name": "Test", "score": 85.5, "tags": ["a", "b"]}
        errors = validate_record_against_schema(record, sample_schema)
        assert len(errors) == 0

    def test_missing_required_field(self, sample_schema):
        record = {"name": "Test"}
        errors = validate_record_against_schema(record, sample_schema)
        assert any("Missing required field: id" in err for err in errors)

    def test_wrong_type(self, sample_schema):
        record = {"id": "not_an_int", "name": "Test"}
        errors = validate_record_against_schema(record, sample_schema)
        assert any("Field 'id' has type str" in err for err in errors)

    def test_string_too_short(self, sample_schema):
        record = {"id": 1, "name": ""}
        errors = validate_record_against_schema(record, sample_schema)
        assert any("length 0 is less than minLength 1" in err for err in errors)

    def test_number_out_of_range(self, sample_schema):
        record = {"id": 1, "name": "Test", "score": 150}
        errors = validate_record_against_schema(record, sample_schema)
        assert any("exceeds maximum 100" in err for err in errors)

    def test_array_too_short(self, sample_schema):
        record = {"id": 1, "name": "Test", "tags": []}
        errors = validate_record_against_schema(record, sample_schema)
        assert any("less than minItems 1" in err for err in errors)


class TestValidateJsonlAgainstSchema:
    @pytest.fixture
    def temp_jsonl_file(self, tmp_path):
        file_path = tmp_path / "test.jsonl"
        content = """{"id": 1, "name": "First"}
        {"id": 2, "name": "Second"}
        {"id": "invalid", "name": "Third"}
        invalid json line
        {"id": 4, "name": "Fourth"}
        """
        file_path.write_text(content)
        return str(file_path)

    @pytest.fixture
    def mock_schema(self, tmp_path):
        schema_path = tmp_path / "test_schema.yaml"
        schema_content = """
        type: object
        properties:
          id:
            type: integer
          name:
            type: string
        required:
          - id
          - name
        """
        schema_path.write_text(schema_content)
        return schema_path

    def test_valid_jsonl(self, temp_jsonl_file):
        # Note: This test assumes schema loading is mocked or schema exists
        # For actual testing, we'd need to set up the schema properly
        valid, invalid, errors = validate_jsonl_against_schema(
            temp_jsonl_file, "dataset_schema"
        )
        # We expect some invalid records due to the test data
        assert valid + invalid > 0

    def test_file_not_found(self):
        valid, invalid, errors = validate_jsonl_against_schema(
            "/nonexistent/path/file.jsonl", "dataset_schema"
        )
        assert valid == 0
        assert invalid == 0
        assert len(errors) == 1
        assert "not found" in errors[0].lower()


class TestGenerateValidationReport:
    def test_empty_results(self):
        results = {}
        report = generate_validation_report(results)
        assert "# Validation Report" in report
        assert "Total Valid Records: 0" in report

    def test_mixed_results(self):
        results = {
            "file1.jsonl": {
                "status": "PASSED",
                "valid_count": 10,
                "invalid_count": 0,
                "errors": [],
            },
            "file2.jsonl": {
                "status": "FAILED",
                "valid_count": 5,
                "invalid_count": 2,
                "errors": ["Error 1", "Error 2"],
            },
        }
        report = generate_validation_report(results)
        assert "Total Valid Records: 15" in report
        assert "Total Invalid Records: 2" in report
        assert "Artifacts Passed: 1" in report
        assert "Artifacts Failed: 1" in report
        assert "Error 1" in report