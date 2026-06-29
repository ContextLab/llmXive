"""
Unit tests for data validation utilities.

These tests verify that the validation functions correctly load schemas,
validate records, and handle errors as expected.
"""
import pytest
import json
import yaml
import tempfile
import os
from pathlib import Path
import pandas as pd
from jsonschema import ValidationError
from analysis.validation_utils import (
    load_schema,
    validate_record,
    validate_dataframe_records,
    validate_file_against_schema
)


# Fixtures
@pytest.fixture
def sample_schema():
    """A simple schema for testing."""
    return {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "type": "object",
        "properties": {
            "id": {"type": "integer"},
            "name": {"type": "string"},
            "value": {"type": "number"}
        },
        "required": ["id", "name"]
    }


@pytest.fixture
def valid_record():
    """A valid record matching the sample schema."""
    return {"id": 1, "name": "Test", "value": 10.5}


@pytest.fixture
def invalid_record():
    """An invalid record (missing required 'name')."""
    return {"id": 1, "value": 10.5}


@pytest.fixture
def schema_file(sample_schema):
    """Creates a temporary YAML schema file."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        yaml.dump(sample_schema, f)
        path = f.name
    yield path
    os.unlink(path)


@pytest.fixture
def csv_file(valid_record):
    """Creates a temporary CSV file with valid data."""
    df = pd.DataFrame([valid_record, {"id": 2, "name": "Test2", "value": 20.0}])
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        df.to_csv(f, index=False)
        path = f.name
    yield path
    os.unlink(path)


# Tests
def test_load_schema_yaml(schema_file, sample_schema):
    """Test loading a schema from a YAML file."""
    loaded = load_schema(schema_file)
    assert loaded == sample_schema


def test_load_schema_nonexistent_file():
    """Test that loading a nonexistent file raises FileNotFoundError."""
    with pytest.raises(FileNotFoundError):
        load_schema("/path/that/does/not/exist.yaml")


def test_validate_record_valid(valid_record, sample_schema):
    """Test validating a valid record returns True."""
    assert validate_record(valid_record, sample_schema) is True


def test_validate_record_invalid(invalid_record, sample_schema):
    """Test validating an invalid record returns False."""
    assert validate_record(invalid_record, sample_schema) is False


def test_validate_dataframe_records_valid(csv_file, schema_file):
    """Test validating a DataFrame with valid records."""
    schema = load_schema(schema_file)
    df = pd.read_csv(csv_file)
    
    results = validate_dataframe_records(df, schema, "test_schema", strict=False)
    
    assert all(r["valid"] for r in results)
    assert len(results) == 2


def test_validate_dataframe_records_invalid(tmp_path):
    """Test validating a DataFrame with invalid records."""
    # Create a CSV with an invalid row (missing 'name')
    df = pd.DataFrame([
        {"id": 1, "name": "Valid", "value": 10},
        {"id": 2, "value": 20}  # Missing 'name'
    ])
    csv_path = tmp_path / "invalid.csv"
    df.to_csv(csv_path, index=False)
    
    schema = {
        "type": "object",
        "properties": {
            "id": {"type": "integer"},
            "name": {"type": "string"},
            "value": {"type": "number"}
        },
        "required": ["id", "name"]
    }
    
    # In non-strict mode, it should return results with errors
    results = validate_dataframe_records(df, schema, "test", strict=False)
    assert len(results) == 2
    assert results[0]["valid"] is True
    assert results[1]["valid"] is False
    assert results[1]["error"] is not None


def test_validate_dataframe_records_strict_mode(tmp_path):
    """Test that strict mode raises ValidationError on invalid data."""
    df = pd.DataFrame([
        {"id": 1, "name": "Valid"},
        {"id": 2}  # Missing 'name'
    ])
    
    schema = {
        "type": "object",
        "properties": {
            "id": {"type": "integer"},
            "name": {"type": "string"}
        },
        "required": ["id", "name"]
    }
    
    with pytest.raises(ValidationError):
        validate_dataframe_records(df, schema, "test", strict=True)


def test_validate_file_against_schema(csv_file, schema_file):
    """Test end-to-end validation of a CSV file against a schema."""
    assert validate_file_against_schema(csv_file, schema_file, "test_schema") is True


def test_validate_file_against_schema_invalid(tmp_path):
    """Test validation of a file with invalid data."""
    # Create schema
    schema = {
        "type": "object",
        "properties": {
            "id": {"type": "integer"},
            "name": {"type": "string"}
        },
        "required": ["id", "name"]
    }
    schema_path = tmp_path / "schema.yaml"
    with open(schema_path, 'w') as f:
        yaml.dump(schema, f)
        
    # Create invalid CSV
    df = pd.DataFrame([{"id": 1}])
    csv_path = tmp_path / "data.csv"
    df.to_csv(csv_path, index=False)
    
    assert validate_file_against_schema(csv_path, schema_path, "test") is False
