"""
Unit tests for schema validation logic.
"""
import os
import sys
import tempfile
import csv
import yaml
from pathlib import Path
import pytest

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from utils.schema_validator import validate_dataset, load_schema, validate_data_types

@pytest.fixture
def valid_schema():
    schema = {
        "properties": {
            "schema_definition": {
                "node_id": {"type": "string"},
                "value": {"type": "integer", "minimum": 0},
                "status": {"type": "integer", "enum": [0, 1, 2]}
            }
        }
    }
    return schema

@pytest.fixture
def valid_csv(valid_schema):
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['node_id', 'value', 'status'])
        writer.writeheader()
        writer.writerow({'node_id': 'n1', 'value': 10, 'status': 0})
        writer.writerow({'node_id': 'n2', 'value': 20, 'status': 1})
        writer.writerow({'node_id': 'n3', 'value': 30, 'status': 2})
        path = f.name
    yield path
    os.unlink(path)

@pytest.fixture
def invalid_csv_type():
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['node_id', 'value', 'status'])
        writer.writeheader()
        writer.writerow({'node_id': 'n1', 'value': 'not_a_number', 'status': 0}) # Invalid type
        path = f.name
    yield path
    os.unlink(path)

@pytest.fixture
def invalid_csv_enum():
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['node_id', 'value', 'status'])
        writer.writeheader()
        writer.writerow({'node_id': 'n1', 'value': 10, 'status': 99}) # Invalid enum
        path = f.name
    yield path
    os.unlink(path)

def test_validate_dataset_passes(valid_csv, valid_schema):
    # Create a temp schema file
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.yaml', newline='') as sf:
        yaml.dump(valid_schema, sf)
        schema_path = sf.name
    
    try:
        is_valid, errors = validate_dataset(valid_csv, schema_path)
        assert is_valid, f"Validation failed with errors: {errors}"
        assert len(errors) == 0
    finally:
        os.unlink(schema_path)

def test_validate_dataset_fails_type(invalid_csv_type, valid_schema):
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.yaml', newline='') as sf:
        yaml.dump(valid_schema, sf)
        schema_path = sf.name
    
    try:
        is_valid, errors = validate_dataset(invalid_csv_type, schema_path)
        assert not is_valid
        assert any("failed type conversion" in str(e) for e in errors)
    finally:
        os.unlink(schema_path)

def test_validate_dataset_fails_enum(invalid_csv_enum, valid_schema):
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.yaml', newline='') as sf:
        yaml.dump(valid_schema, sf)
        schema_path = sf.name
    
    try:
        is_valid, errors = validate_dataset(invalid_csv_enum, schema_path)
        assert not is_valid
        assert any("not in enum" in str(e) for e in errors)
    finally:
        os.unlink(schema_path)

def test_validate_data_types_min_bound():
    schema_def = {"value": {"type": "integer", "minimum": 10}}
    row = {"value": "5"}
    errors = validate_data_types(row, schema_def, 1)
    assert any("below minimum" in e for e in errors)

def test_validate_data_types_null_nullable():
    schema_def = {"value": {"type": "string", "nullable": True}}
    row = {"value": ""}
    errors = validate_data_types(row, schema_def, 1)
    assert len(errors) == 0

def test_validate_data_types_null_not_nullable():
    schema_def = {"value": {"type": "string", "nullable": False}}
    row = {"value": ""}
    errors = validate_data_types(row, schema_def, 1)
    assert any("not marked nullable" in e for e in errors)
