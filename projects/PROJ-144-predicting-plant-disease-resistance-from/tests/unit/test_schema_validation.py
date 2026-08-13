"""
Unit tests for schema validation logic.
"""
import pytest
import json
import yaml
import tempfile
from pathlib import Path
import sys

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from research.validate_schema import (
    load_yaml_schema,
    validate_schema_structure,
    validate_with_jsonschema
)

def test_load_yaml_schema_valid():
    schema_content = {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "type": "object",
        "properties": {
            "test_field": {"type": "string"}
        }
    }
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        yaml.dump(schema_content, f)
        temp_path = f.name

    try:
        result = load_yaml_schema(temp_path)
        assert result == schema_content
    finally:
        Path(temp_path).unlink()

def test_load_yaml_schema_missing_file():
    with pytest.raises(FileNotFoundError):
        load_yaml_schema("non_existent_file.yaml")

def test_validate_schema_structure_valid():
    schema = {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "type": "object",
        "properties": {"a": {"type": "string"}}
    }
    assert validate_schema_structure(schema) is True

def test_validate_schema_structure_missing_schema_key():
    schema = {
        "type": "object",
        "properties": {"a": {"type": "string"}}
    }
    with pytest.raises(ValueError, match="missing.*\\$schema"):
        validate_schema_structure(schema)

def test_validate_schema_structure_missing_type():
    schema = {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "properties": {"a": {"type": "string"}}
    }
    with pytest.raises(ValueError, match="missing.*type"):
        validate_schema_structure(schema)

def test_validate_schema_structure_missing_properties():
    schema = {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "type": "object"
    }
    with pytest.raises(ValueError, match="missing.*properties"):
        validate_schema_structure(schema)

def test_validate_with_jsonschema_valid():
    schema = {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "type": "object",
        "properties": {
            "name": {"type": "string"},
            "age": {"type": "number"}
        },
        "required": ["name"]
    }
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        yaml.dump(schema, f)
        temp_path = f.name

    try:
        # Test schema validity only
        assert validate_with_jsonschema(temp_path) is True
        
        # Test with valid sample
        valid_sample = {"name": "Plant A", "age": 10}
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as sf:
            json.dump(valid_sample, sf)
            sample_path = sf.name
        
        try:
            assert validate_with_jsonschema(temp_path, sample_path) is True
        finally:
            Path(sample_path).unlink()

        # Test with invalid sample (missing required)
        invalid_sample = {"age": 10}
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as sf:
            json.dump(invalid_sample, sf)
            sample_path = sf.name
        
        try:
            # Should return False for invalid sample
            assert validate_with_jsonschema(temp_path, sample_path) is False
        finally:
            Path(sample_path).unlink()

    finally:
        Path(temp_path).unlink()
