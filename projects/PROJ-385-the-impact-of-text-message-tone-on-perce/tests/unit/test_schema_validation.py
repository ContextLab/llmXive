"""
Unit tests for schema validation logic.
"""
import pytest
import json
import csv
import yaml
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

# Import the module to test
# Note: Assuming validate_schemas.py is in code/ and added to path or installed
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from validate_schemas import load_schema, validate_json_against_schema, validate_csv_against_schema

@pytest.fixture
def sample_stimulus_schema():
    return {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "title": "Test Schema",
        "type": "object",
        "required": ["id", "value"],
        "properties": {
            "id": {"type": "string", "pattern": "^ID[0-9]+$"},
            "value": {"type": "integer", "minimum": 0, "maximum": 100},
            "label": {"type": "string", "enum": ["A", "B", "C"]}
        },
        "additionalProperties": False
    }

@pytest.fixture
def valid_stimulus_json():
    return {
        "id": "ID123",
        "value": 50,
        "label": "A"
    }

@pytest.fixture
def invalid_stimulus_json_missing_field():
    return {
        "id": "ID123",
        "label": "A"
    }

@pytest.fixture
def invalid_stimulus_json_bad_pattern():
    return {
        "id": "BAD_ID",
        "value": 50,
        "label": "A"
    }

@pytest.fixture
def invalid_stimulus_json_bad_enum():
    return {
        "id": "ID123",
        "value": 50,
        "label": "X"
    }

@pytest.fixture
def invalid_stimulus_json_bad_range():
    return {
        "id": "ID123",
        "value": 150,
        "label": "A"
    }

def test_load_schema_success(tmp_path, sample_stimulus_schema):
    schema_file = tmp_path / "test.schema.yaml"
    with open(schema_file, 'w') as f:
        yaml.dump(sample_stimulus_schema, f)

    with patch('validate_schemas.get_contracts_dir', return_value=tmp_path):
        schema = load_schema("test.schema.yaml")
        assert schema["type"] == "object"
        assert "id" in schema["required"]

def test_load_schema_not_found(tmp_path):
    with patch('validate_schemas.get_contracts_dir', return_value=tmp_path):
        with pytest.raises(FileNotFoundError):
            load_schema("non_existent.schema.yaml")

def test_validate_json_valid(valid_stimulus_json, sample_stimulus_schema):
    errors = validate_json_against_schema(valid_stimulus_json, sample_stimulus_schema)
    assert len(errors) == 0

def test_validate_json_missing_field(invalid_stimulus_json_missing_field, sample_stimulus_schema):
    errors = validate_json_against_schema(invalid_stimulus_json_missing_field, sample_stimulus_schema)
    assert len(errors) > 0
    assert any("required" in err.lower() for err in errors)

def test_validate_json_bad_pattern(invalid_stimulus_json_bad_pattern, sample_stimulus_schema):
    errors = validate_json_against_schema(invalid_stimulus_json_bad_pattern, sample_stimulus_schema)
    assert len(errors) > 0
    assert any("pattern" in err.lower() for err in errors)

def test_validate_json_bad_enum(invalid_stimulus_json_bad_enum, sample_stimulus_schema):
    errors = validate_json_against_schema(invalid_stimulus_json_bad_enum, sample_stimulus_schema)
    assert len(errors) > 0
    assert any("enum" in err.lower() for err in errors)

def test_validate_json_bad_range(invalid_stimulus_json_bad_range, sample_stimulus_schema):
    errors = validate_json_against_schema(invalid_stimulus_json_bad_range, sample_stimulus_schema)
    assert len(errors) > 0
    assert any("minimum" in err.lower() or "maximum" in err.lower() for err in errors)

def test_validate_csv_valid(tmp_path, sample_stimulus_schema):
    csv_file = tmp_path / "valid.csv"
    with open(csv_file, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=["id", "value", "label"])
        writer.writeheader()
        writer.writerow({"id": "ID123", "value": "50", "label": "A"})
        writer.writerow({"id": "ID456", "value": "0", "label": "C"})

    with patch('validate_schemas.get_contracts_dir', return_value=tmp_path):
        errors = validate_csv_against_schema(csv_file, "test.schema.yaml")
        assert len(errors) == 0

def test_validate_csv_missing_header(tmp_path, sample_stimulus_schema):
    csv_file = tmp_path / "missing.csv"
    with open(csv_file, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=["id", "label"])
        writer.writeheader()
        writer.writerow({"id": "ID123", "label": "A"})

    with patch('validate_schemas.get_contracts_dir', return_value=tmp_path):
        errors = validate_csv_against_schema(csv_file, "test.schema.yaml")
        assert len(errors) > 0
        assert any("Missing required columns" in err for err in errors)

def test_validate_csv_bad_pattern(tmp_path, sample_stimulus_schema):
    csv_file = tmp_path / "bad.csv"
    with open(csv_file, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=["id", "value", "label"])
        writer.writeheader()
        writer.writerow({"id": "BAD_ID", "value": "50", "label": "A"})

    with patch('validate_schemas.get_contracts_dir', return_value=tmp_path):
        errors = validate_csv_against_schema(csv_file, "test.schema.yaml")
        assert len(errors) > 0
        assert any("pattern" in err.lower() for err in errors)

def test_validate_csv_bad_enum(tmp_path, sample_stimulus_schema):
    csv_file = tmp_path / "bad.csv"
    with open(csv_file, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=["id", "value", "label"])
        writer.writeheader()
        writer.writerow({"id": "ID123", "value": "50", "label": "X"})

    with patch('validate_schemas.get_contracts_dir', return_value=tmp_path):
        errors = validate_csv_against_schema(csv_file, "test.schema.yaml")
        assert len(errors) > 0
        assert any("enum" in err.lower() for err in errors)

def test_validate_csv_bad_range(tmp_path, sample_stimulus_schema):
    csv_file = tmp_path / "bad.csv"
    with open(csv_file, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=["id", "value", "label"])
        writer.writeheader()
        writer.writerow({"id": "ID123", "value": "150", "label": "A"})

    with patch('validate_schemas.get_contracts_dir', return_value=tmp_path):
        errors = validate_csv_against_schema(csv_file, "test.schema.yaml")
        assert len(errors) > 0
        assert any("minimum" in err.lower() or "maximum" in err.lower() for err in errors)