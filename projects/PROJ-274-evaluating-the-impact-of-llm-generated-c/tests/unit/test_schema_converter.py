import json
import yaml
import os
import tempfile
import pytest
from pathlib import Path

# Import the functions to test
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from code.utils.schema_converter import (
    load_json_schema,
    save_yaml_schema,
    convert_json_to_yaml
)

@pytest.fixture
def sample_json_schema(tmp_path):
    """Create a temporary JSON schema file for testing."""
    schema = {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "type": "object",
        "properties": {
            "participant_id": {
                "type": "string",
                "description": "Unique identifier for the participant"
            },
            "condition": {
                "type": "string",
                "enum": ["llm", "human", "none"]
            },
            "task_time": {
                "type": "number",
                "minimum": 0
            },
            "clarification_count": {
                "type": "integer",
                "minimum": 0
            }
        },
        "required": ["participant_id", "condition", "task_time"]
    }
    
    json_file = tmp_path / "test_schema.json"
    with open(json_file, 'w') as f:
        json.dump(schema, f, indent=2)
    
    return json_file

@pytest.fixture
def yaml_output_path(tmp_path):
    """Create a temporary path for YAML output."""
    return tmp_path / "test_schema.yaml"

def test_load_json_schema(sample_json_schema):
    """Test loading a JSON schema file."""
    data = load_json_schema(str(sample_json_schema))
    assert isinstance(data, dict)
    assert "$schema" in data
    assert data["type"] == "object"
    assert "properties" in data

def test_load_json_schema_not_found():
    """Test loading a non-existent JSON schema file."""
    with pytest.raises(FileNotFoundError):
        load_json_schema("/non/existent/path/schema.json")

def test_save_yaml_schema(sample_json_schema, yaml_output_path):
    """Test saving a dictionary as YAML."""
    data = load_json_schema(str(sample_json_schema))
    save_yaml_schema(data, str(yaml_output_path))
    
    assert os.path.exists(yaml_output_path)
    
    # Verify the YAML file is valid and contains the same data
    with open(yaml_output_path, 'r') as f:
        yaml_data = yaml.safe_load(f)
    
    assert yaml_data == data

def test_convert_json_to_yaml(sample_json_schema, yaml_output_path):
    """Test converting a JSON schema file to YAML."""
    result_path = convert_json_to_yaml(str(sample_json_schema), str(yaml_output_path))
    
    assert result_path == str(yaml_output_path)
    assert os.path.exists(yaml_output_path)
    
    # Verify the content matches
    json_data = load_json_schema(str(sample_json_schema))
    with open(yaml_output_path, 'r') as f:
        yaml_data = yaml.safe_load(f)
    
    assert yaml_data == json_data

def test_convert_json_to_yaml_creates_directory(sample_json_schema, tmp_path):
    """Test that convert_json_to_yaml creates the output directory if it doesn't exist."""
    nested_path = tmp_path / "nested" / "dir" / "output.yaml"
    result_path = convert_json_to_yaml(str(sample_json_schema), str(nested_path))
    
    assert os.path.exists(result_path)
    assert os.path.exists(nested_path)

def test_main_function(monkeypatch, sample_json_schema, yaml_output_path):
    """Test the main function with command-line arguments."""
    # Mock sys.argv
    monkeypatch.setattr('sys.argv', ['script', str(sample_json_schema), str(yaml_output_path)])
    
    # Import and run main
    from code.utils.schema_converter import main
    result = main()
    
    assert result == 0
    assert os.path.exists(yaml_output_path)