"""
Unit tests for contract validation utility.
"""
import json
import yaml
import tempfile
import os
from pathlib import Path
import pytest
import sys

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from utils.validate_contracts import (
    load_yaml_schema,
    load_json_output,
    validate_against_schema,
    validate_all_contracts
)

@pytest.fixture
def temp_schema():
    schema_content = {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "type": "object",
        "required": ["name", "age"],
        "properties": {
            "name": {"type": "string"},
            "age": {"type": "integer", "minimum": 0}
        }
    }
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        yaml.dump(schema_content, f)
        yield Path(f.name)
    os.unlink(f.name)

@pytest.fixture
def temp_valid_json():
    data = {"name": "Alice", "age": 30}
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(data, f)
        yield Path(f.name)
    os.unlink(f.name)

@pytest.fixture
def temp_invalid_json():
    data = {"name": "Bob"}  # Missing required 'age'
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(data, f)
        yield Path(f.name)
    os.unlink(f.name)

def test_load_yaml_schema(temp_schema):
    schema = load_yaml_schema(temp_schema)
    assert schema["type"] == "object"
    assert "name" in schema["properties"]

def test_load_json_output_valid(temp_valid_json):
    data = load_json_output(temp_valid_json)
    assert data["name"] == "Alice"
    assert data["age"] == 30

def test_load_json_output_invalid(temp_invalid_json):
    with pytest.raises(ValueError):
        load_json_output(temp_invalid_json)

def test_validate_against_schema_valid(temp_schema, temp_valid_json):
    schema = load_yaml_schema(temp_schema)
    data = load_json_output(temp_valid_json)
    is_valid, message = validate_against_schema(data, schema, temp_schema)
    assert is_valid
    assert "successful" in message.lower()

def test_validate_against_schema_invalid(temp_schema, temp_invalid_json):
    schema = load_yaml_schema(temp_schema)
    data = load_json_output(temp_invalid_json)
    is_valid, message = validate_against_schema(data, schema, temp_schema)
    assert not is_valid
    assert "failed" in message.lower()

def test_validate_all_contracts():
    """
    Integration test for full contract validation flow.
    Creates a temporary project structure with schemas and outputs.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        project_root = Path(tmpdir)
        
        # Create contracts directory
        contracts_dir = project_root / "contracts"
        contracts_dir.mkdir()
        
        # Create a simple schema
        schema_data = {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "type": "object",
            "properties": {
                "test_field": {"type": "string"}
            }
        }
        schema_path = contracts_dir / "test.schema.yaml"
        with open(schema_path, 'w') as f:
            yaml.dump(schema_data, f)
        
        # Create valid output
        valid_output = {"test_field": "hello"}
        valid_path = project_root / "data" / "processed" / "test_output.json"
        valid_path.parent.mkdir(parents=True)
        with open(valid_path, 'w') as f:
            json.dump(valid_output, f)
        
        # Run validation
        report = validate_all_contracts(project_root)
        
        assert report["total_schemas"] == 1
        assert report["total_outputs"] == 1
        assert report["summary"]["passed"] == 1
        assert report["summary"]["failed"] == 0