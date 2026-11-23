import json
import os
import tempfile
import pytest
from code.verify_schemas import verify_file_schema, SCHEMAS

@pytest.fixture
def temp_dir():
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir

def test_verify_schema_missing_file(temp_dir):
    schema = {"required_keys": ["key1"]}
    result = verify_file_schema(os.path.join(temp_dir, "nonexistent.json"), schema)
    assert result is False

def test_verify_schema_invalid_json(temp_dir):
    file_path = os.path.join(temp_dir, "invalid.json")
    with open(file_path, 'w') as f:
        f.write("{ not valid json }")
    schema = {"required_keys": []}
    result = verify_file_schema(file_path, schema)
    assert result is False

def test_verify_schema_missing_keys(temp_dir):
    file_path = os.path.join(temp_dir, "missing_keys.json")
    with open(file_path, 'w') as f:
        json.dump({"key1": 1}, f)
    schema = {"required_keys": ["key1", "key2"]}
    result = verify_file_schema(file_path, schema)
    assert result is False

def test_verify_schema_numeric_type_fail(temp_dir):
    file_path = os.path.join(temp_dir, "numeric_fail.json")
    with open(file_path, 'w') as f:
        json.dump({"slope": "not_a_number"}, f)
    schema = {"required_keys": ["slope"], "numeric_keys": ["slope"]}
    result = verify_file_schema(file_path, schema)
    assert result is False

def test_verify_schema_numeric_type_pass(temp_dir):
    file_path = os.path.join(temp_dir, "numeric_pass.json")
    with open(file_path, 'w') as f:
        json.dump({"slope": 0.5}, f)
    schema = {"required_keys": ["slope"], "numeric_keys": ["slope"]}
    result = verify_file_schema(file_path, schema)
    assert result is True

def test_verify_schema_list_type_fail(temp_dir):
    file_path = os.path.join(temp_dir, "list_fail.json")
    with open(file_path, 'w') as f:
        json.dump({"data": "string"}, f)
    schema = {"required_keys": ["data"], "list_keys": ["data"]}
    result = verify_file_schema(file_path, schema)
    assert result is False

def test_verify_schema_list_type_pass(temp_dir):
    file_path = os.path.join(temp_dir, "list_pass.json")
    with open(file_path, 'w') as f:
        json.dump({"data": [1, 2, 3]}, f)
    schema = {"required_keys": ["data"], "list_keys": ["data"]}
    result = verify_file_schema(file_path, schema)
    assert result is True

def test_verify_schema_status_invalid(temp_dir):
    file_path = os.path.join(temp_dir, "status_invalid.json")
    with open(file_path, 'w') as f:
        json.dump({"status": "unknown"}, f)
    schema = {"required_keys": ["status"], "status_values": ["valid", "invalid"]}
    result = verify_file_schema(file_path, schema)
    assert result is False

def test_verify_schema_status_valid(temp_dir):
    file_path = os.path.join(temp_dir, "status_valid.json")
    with open(file_path, 'w') as f:
        json.dump({"status": "valid"}, f)
    schema = {"required_keys": ["status"], "status_values": ["valid", "invalid"]}
    result = verify_file_schema(file_path, schema)
    assert result is True

def test_verify_schema_structure_nested_fail(temp_dir):
    file_path = os.path.join(temp_dir, "nested_fail.json")
    with open(file_path, 'w') as f:
        json.dump({"field": {"status": 123, "valid_levels": []}}, f)
    schema = {
        "required_keys": ["field"],
        "structure": {
            "field": {"status": str, "valid_levels": list}
        }
    }
    result = verify_file_schema(file_path, schema)
    assert result is False

def test_verify_schema_structure_nested_pass(temp_dir):
    file_path = os.path.join(temp_dir, "nested_pass.json")
    with open(file_path, 'w') as f:
        json.dump({"field": {"status": "valid", "valid_levels": ["A", "B"]}}, f)
    schema = {
        "required_keys": ["field"],
        "structure": {
            "field": {"status": str, "valid_levels": list}
        }
    }
    result = verify_file_schema(file_path, schema)
    assert result is True
