import os
import tempfile
import json
import pytest
from validation import validate_data_file, load_schema_from_file, validate_json_schema

def test_validate_json_schema_valid():
    data = {"name": "test", "count": 10, "active": True}
    schema = {
        "required": ["name", "count"],
        "properties": {
            "name": {"type": "string"},
            "count": {"type": "number"},
            "active": {"type": "boolean"}
        }
    }
    is_valid, errors = validate_json_schema(data, schema)
    assert is_valid is True
    assert len(errors) == 0

def test_validate_json_schema_missing_required():
    data = {"name": "test"}
    schema = {
        "required": ["name", "count"],
        "properties": {
            "name": {"type": "string"},
            "count": {"type": "number"}
        }
    }
    is_valid, errors = validate_json_schema(data, schema)
    assert is_valid is False
    assert "Missing required field: count" in errors

def test_validate_json_schema_wrong_type():
    data = {"name": 123}
    schema = {
        "required": ["name"],
        "properties": {
            "name": {"type": "string"}
        }
    }
    is_valid, errors = validate_json_schema(data, schema)
    assert is_valid is False
    assert "Field 'name' must be string" in errors[0]

def test_validate_data_file_valid():
    with tempfile.TemporaryDirectory() as tmpdir:
        data_path = os.path.join(tmpdir, 'data.json')
        schema_path = os.path.join(tmpdir, 'schema.json')
        
        data = {"name": "test", "count": 10}
        schema = {
            "required": ["name"],
            "properties": {
                "name": {"type": "string"},
                "count": {"type": "number"}
            }
        }
        
        with open(data_path, 'w') as f:
            json.dump(data, f)
        with open(schema_path, 'w') as f:
            json.dump(schema, f)
        
        result = validate_data_file(data_path, schema_path)
        assert result['valid'] is True
        assert len(result['errors']) == 0

def test_validate_data_file_invalid():
    with tempfile.TemporaryDirectory() as tmpdir:
        data_path = os.path.join(tmpdir, 'data.json')
        schema_path = os.path.join(tmpdir, 'schema.json')
        
        data = {"name": 123}
        schema = {
            "required": ["name"],
            "properties": {
                "name": {"type": "string"}
            }
        }
        
        with open(data_path, 'w') as f:
            json.dump(data, f)
        with open(schema_path, 'w') as f:
            json.dump(schema, f)
        
        result = validate_data_file(data_path, schema_path)
        assert result['valid'] is False
        assert len(result['errors']) > 0

def test_validate_data_file_not_found():
    with tempfile.TemporaryDirectory() as tmpdir:
        data_path = os.path.join(tmpdir, 'nonexistent.json')
        schema_path = os.path.join(tmpdir, 'schema.json')
        
        schema = {"required": []}
        with open(schema_path, 'w') as f:
            json.dump(schema, f)
        
        result = validate_data_file(data_path, schema_path)
        assert result['valid'] is False
        assert "File not found" in str(result['errors'])