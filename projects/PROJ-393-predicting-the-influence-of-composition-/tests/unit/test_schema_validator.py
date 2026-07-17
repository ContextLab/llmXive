"""
Unit tests for schema_validator module (T011).
"""

import json
import tempfile
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

import sys
import os

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.utils.schema_validator import (
    load_schema,
    validate_type,
    validate_pattern,
    validate_range,
    validate_field,
    validate_record,
    validate_dataset,
    validate_json_file,
    validate_csv_file
)


@pytest.fixture
def sample_schema():
    return {
        "name": "test_schema",
        "fields": [
            {"name": "id", "type": "integer", "required": True},
            {"name": "name", "type": "string", "required": True, "pattern": "^[A-Za-z]+$"},
            {"name": "value", "type": "number", "required": False, "min": 0, "max": 100},
            {"name": "active", "type": "boolean", "required": False},
            {"name": "category", "type": "string", "required": False, "enum": ["A", "B", "C"]}
        ]
    }


@pytest.fixture
def valid_record():
    return {
        "id": 1,
        "name": "TestItem",
        "value": 50.5,
        "active": True,
        "category": "A"
    }


@pytest.fixture
def invalid_record():
    return {
        "id": "not_an_int",
        "name": "Invalid-Name",
        "value": 150,
        "active": "not_bool",
        "category": "D"
    }


def test_validate_type_string():
    assert validate_type("hello", "string") is True
    assert validate_type(123, "string") is False
    assert validate_type(None, "string") is False


def test_validate_type_integer():
    assert validate_type(123, "integer") is True
    assert validate_type(123.5, "integer") is False
    assert validate_type(True, "integer") is False  # bool is subclass of int, but we reject it
    assert validate_type("123", "integer") is False


def test_validate_type_number():
    assert validate_type(123, "number") is True
    assert validate_type(123.5, "number") is True
    assert validate_type("123", "number") is False


def test_validate_type_boolean():
    assert validate_type(True, "boolean") is True
    assert validate_type(False, "boolean") is True
    assert validate_type(1, "boolean") is False
    assert validate_type("true", "boolean") is False


def test_validate_pattern():
    assert validate_pattern("Hello", "^[A-Za-z]+$") is True
    assert validate_pattern("Hello123", "^[A-Za-z]+$") is False
    assert validate_pattern(123, "^[A-Za-z]+$") is False


def test_validate_range():
    assert validate_range(50, 0, 100) is True
    assert validate_range(-1, 0, 100) is False
    assert validate_range(101, 0, 100) is False
    assert validate_range(50, None, 100) is True
    assert validate_range(50, 0, None) is True


def test_validate_field_valid(sample_schema):
    field_def = sample_schema["fields"][0]
    is_valid, errors = validate_field(1, field_def)
    assert is_valid is True
    assert len(errors) == 0


def test_validate_field_missing_required(sample_schema):
    field_def = sample_schema["fields"][0]
    is_valid, errors = validate_field(None, field_def)
    assert is_valid is False
    assert "required" in errors[0]


def test_validate_field_type_mismatch(sample_schema):
    field_def = sample_schema["fields"][0]
    is_valid, errors = validate_field("not_int", field_def)
    assert is_valid is False
    assert "wrong type" in errors[0]


def test_validate_field_pattern_mismatch(sample_schema):
    field_def = sample_schema["fields"][1]
    is_valid, errors = validate_field("Invalid-123", field_def)
    assert is_valid is False
    assert "pattern" in errors[0]


def test_validate_field_range_mismatch(sample_schema):
    field_def = sample_schema["fields"][2]
    is_valid, errors = validate_field(150, field_def)
    assert is_valid is False
    assert "out of range" in errors[0]


def test_validate_field_enum_mismatch(sample_schema):
    field_def = sample_schema["fields"][4]
    is_valid, errors = validate_field("D", field_def)
    assert is_valid is False
    assert "not in allowed values" in errors[0]


def test_validate_record_valid(valid_record, sample_schema):
    is_valid, errors = validate_record(valid_record, sample_schema)
    assert is_valid is True
    assert len(errors) == 0


def test_validate_record_invalid(invalid_record, sample_schema):
    is_valid, errors = validate_record(invalid_record, sample_schema)
    assert is_valid is False
    assert len(errors) > 0


def test_validate_dataset_valid(sample_schema):
    data = [
        {"id": 1, "name": "Item1", "value": 10},
        {"id": 2, "name": "Item2", "value": 20}
    ]
    is_valid, report = validate_dataset(data, sample_schema)
    assert is_valid is True
    assert report["valid_records"] == 2
    assert report["invalid_records"] == 0


def test_validate_dataset_mixed(sample_schema):
    data = [
        {"id": 1, "name": "Item1", "value": 10},
        {"id": "bad", "name": "Item2", "value": 20}
    ]
    is_valid, report = validate_dataset(data, sample_schema)
    assert is_valid is False
    assert report["valid_records"] == 1
    assert report["invalid_records"] == 1
    assert len(report["errors"]) > 0


def test_load_schema(tmp_path):
    schema_content = {
        "name": "test",
        "fields": [{"name": "id", "type": "integer", "required": True}]
    }
    schema_file = tmp_path / "test_schema.yaml"
    import yaml
    with open(schema_file, 'w') as f:
        yaml.dump(schema_content, f)

    loaded = load_schema(schema_file)
    assert loaded["name"] == "test"
    assert len(loaded["fields"]) == 1


def test_validate_json_file(tmp_path, sample_schema):
    data = [
        {"id": 1, "name": "Valid", "value": 50},
        {"id": 2, "name": "AlsoValid", "value": 60}
    ]
    data_file = tmp_path / "data.json"
    with open(data_file, 'w') as f:
        json.dump(data, f)

    schema_file = tmp_path / "schema.yaml"
    import yaml
    with open(schema_file, 'w') as f:
        yaml.dump(sample_schema, f)

    is_valid, report = validate_json_file(data_file, schema_file)
    assert is_valid is True
    assert report["valid_records"] == 2


def test_validate_csv_file(tmp_path, sample_schema):
    data = [
        {"id": "1", "name": "Valid", "value": "50.5"},
        {"id": "2", "name": "Valid2", "value": "60.5"}
    ]
    data_file = tmp_path / "data.csv"
    import csv
    with open(data_file, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=data[0].keys())
        writer.writeheader()
        writer.writerows(data)

    schema_file = tmp_path / "schema.yaml"
    import yaml
    with open(schema_file, 'w') as f:
        yaml.dump(sample_schema, f)

    is_valid, report = validate_csv_file(data_file, schema_file)
    assert is_valid is True
    assert report["valid_records"] == 2


def test_validate_csv_file_invalid(tmp_path, sample_schema):
    data = [
        {"id": "bad_id", "name": "Valid", "value": "50.5"}
    ]
    data_file = tmp_path / "data.csv"
    import csv
    with open(data_file, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=data[0].keys())
        writer.writeheader()
        writer.writerows(data)

    schema_file = tmp_path / "schema.yaml"
    import yaml
    with open(schema_file, 'w') as f:
        yaml.dump(sample_schema, f)

    is_valid, report = validate_csv_file(data_file, schema_file)
    assert is_valid is False
    assert report["invalid_records"] == 1
    assert len(report["errors"]) > 0


def test_validate_dataset_empty(sample_schema):
    is_valid, report = validate_dataset([], sample_schema)
    assert is_valid is True
    assert report["total_records"] == 0
    assert report["valid_records"] == 0
    assert report["invalid_records"] == 0


def test_validate_dataset_non_list(sample_schema):
    is_valid, report = validate_dataset("not a list", sample_schema)
    assert is_valid is False
    assert "must be a list" in report["errors"][0]