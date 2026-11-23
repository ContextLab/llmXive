import os
import json
import tempfile
import pytest
from pathlib import Path
import yaml

# We need to import the module functions. 
# Since the file is in code/, we need to ensure the path is correct or mock the import.
# For unit tests, we will mock the file system or use temporary files.

# Add parent directory to path to import code modules
import sys
code_dir = Path(__file__).resolve().parent.parent.parent / "code"
if str(code_dir) not in sys.path:
    sys.path.insert(0, str(code_dir))

from validate_json_schema import load_schema, validate_json_against_schema
import logging

@pytest.fixture
def temp_dir():
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

def test_load_schema_valid_yaml(temp_dir):
    """Test loading a valid YAML schema."""
    schema_content = {
        "type": "object",
        "properties": {
            "scenario": {"type": "string"},
            "r_value": {"type": "number"}
        },
        "required": ["scenario", "r_value"]
    }
    
    schema_file = temp_dir / "test_schema.yaml"
    with open(schema_file, 'w') as f:
        yaml.dump(schema_content, f)
    
    loaded = load_schema(schema_file)
    assert loaded["type"] == "object"
    assert "scenario" in loaded["properties"]

def test_load_schema_missing_file():
    """Test loading a non-existent schema file."""
    with pytest.raises(FileNotFoundError):
        load_schema(Path("/non/existent/path/schema.yaml"))

def test_validate_json_valid(temp_dir):
    """Test validation of a valid JSON against a schema."""
    schema_content = {
        "type": "object",
        "properties": {
            "name": {"type": "string"},
            "value": {"type": "number"}
        },
        "required": ["name", "value"]
    }
    
    json_content = {
        "name": "test_case",
        "value": 42.5
    }
    
    schema_file = temp_dir / "schema.yaml"
    json_file = temp_dir / "data.json"
    
    with open(schema_file, 'w') as f:
        yaml.dump(schema_content, f)
    with open(json_file, 'w') as f:
        json.dump(json_content, f)
    
    logger = logging.getLogger("test")
    logger.setLevel(logging.INFO)
    # Add a null handler to avoid "No handler found" warnings
    logger.addHandler(logging.NullHandler())
    
    assert validate_json_against_schema(json_file, schema_file, logger) is True

def test_validate_json_invalid_missing_required(temp_dir):
    """Test validation fails when required field is missing."""
    schema_content = {
        "type": "object",
        "properties": {
            "name": {"type": "string"},
            "value": {"type": "number"}
        },
        "required": ["name", "value"]
    }
    
    json_content = {
        "name": "test_case"
        # "value" is missing
    }
    
    schema_file = temp_dir / "schema.yaml"
    json_file = temp_dir / "data.json"
    
    with open(schema_file, 'w') as f:
        yaml.dump(schema_content, f)
    with open(json_file, 'w') as f:
        json.dump(json_content, f)
    
    logger = logging.getLogger("test")
    logger.setLevel(logging.INFO)
    logger.addHandler(logging.NullHandler())
    
    assert validate_json_against_schema(json_file, schema_file, logger) is False

def test_validate_json_invalid_type(temp_dir):
    """Test validation fails when type is wrong."""
    schema_content = {
        "type": "object",
        "properties": {
            "count": {"type": "integer"}
        }
    }
    
    json_content = {
        "count": "not_an_integer"
    }
    
    schema_file = temp_dir / "schema.yaml"
    json_file = temp_dir / "data.json"
    
    with open(schema_file, 'w') as f:
        yaml.dump(schema_content, f)
    with open(json_file, 'w') as f:
        json.dump(json_content, f)
    
    logger = logging.getLogger("test")
    logger.setLevel(logging.INFO)
    logger.addHandler(logging.NullHandler())
    
    assert validate_json_against_schema(json_file, schema_file, logger) is False