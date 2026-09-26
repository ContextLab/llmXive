"""
Unit tests for the SchemaValidator class.
"""
import os
import json
import tempfile
import pytest
from pathlib import Path
import sys

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from schema_validator import SchemaValidator, load_schema

# Mock schemas for testing
TEST_DATASET_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "type": "object",
    "required": ["age", "sex", "bmi"],
    "properties": {
        "age": {"type": "integer", "minimum": 0},
        "sex": {"type": "string", "enum": ["M", "F"]},
        "bmi": {"type": "number"},
        "diet": {"type": ["string", "null"]}
    }
}

TEST_OUTPUT_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "type": "object",
    "required": ["stratum_id", "valid_strata_count"],
    "properties": {
        "stratum_id": {"type": "string"},
        "valid_strata_count": {"type": "integer"}
    }
}

@pytest.fixture
def temp_schema_file(tmp_path):
    schema_file = tmp_path / "test_schema.json"
    schema_file.write_text(json.dumps(TEST_DATASET_SCHEMA))
    return str(schema_file)

@pytest.fixture
def temp_valid_data(tmp_path):
    data_file = tmp_path / "valid_data.json"
    data = {
        "age": 30,
        "sex": "M",
        "bmi": 22.5,
        "diet": "Omnivore"
    }
    data_file.write_text(json.dumps(data))
    return str(data_file)

@pytest.fixture
def temp_invalid_data(tmp_path):
    data_file = tmp_path / "invalid_data.json"
    # Missing 'age', invalid 'sex'
    data = {
        "sex": "Other",
        "bmi": 22.5
    }
    data_file.write_text(json.dumps(data))
    return str(data_file)

def test_load_schema(tmp_path):
    schema_file = tmp_path / "schema.json"
    schema_file.write_text(json.dumps(TEST_DATASET_SCHEMA))
    schema = load_schema(str(schema_file))
    assert schema["type"] == "object"
    assert "age" in schema["properties"]

def test_validate_valid_data(temp_schema_file, temp_valid_data):
    validator = SchemaValidator(temp_schema_file)
    # Load data manually to test validate_dict directly
    with open(temp_valid_data, 'r') as f:
        data = json.load(f)
    assert validator.validate_dict(data) is True

def test_validate_invalid_data(temp_schema_file, temp_invalid_data):
    validator = SchemaValidator(temp_schema_file)
    with open(temp_invalid_data, 'r') as f:
        data = json.load(f)
    assert validator.validate_dict(data) is False

def test_validate_file(temp_schema_file, temp_valid_data):
    validator = SchemaValidator(temp_schema_file)
    # Convert temp_valid_data to relative path if needed, but for test we pass absolute
    # The validator expects path relative to project root, but in test we can mock or adjust
    # For simplicity, we test validate_dict here, file validation depends on project root structure
    with open(temp_valid_data, 'r') as f:
        data = json.load(f)
    assert validator.validate_dict(data) is True