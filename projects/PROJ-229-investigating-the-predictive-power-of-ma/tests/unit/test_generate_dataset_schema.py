"""
Unit tests for the dataset schema generation utility.
"""

import json
import yaml
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from code.utils.generate_dataset_schema import (
    load_target_decision,
    generate_schema,
    validate_schema,
    save_schema
)

@pytest.fixture
def temp_decision_file(tmp_path):
    """Create a temporary target decision file."""
    decision_data = {
        "target": "melting_point",
        "correlation_coefficient": 0.85,
        "p_value": 0.001,
        "threshold_used": 0.7,
        "decision_reason": "Selected based on high correlation",
        "note": "Test data"
    }
    decision_path = tmp_path / "target_decision.json"
    with open(decision_path, 'w') as f:
        json.dump(decision_data, f)
    return decision_path

@pytest.fixture
def temp_output_path(tmp_path):
    """Create a temporary output path for schema."""
    return tmp_path / "test_schema.yaml"

def test_load_target_decision(temp_decision_file):
    """Test loading target decision from JSON file."""
    decision = load_target_decision(temp_decision_file)
    
    assert decision["target"] == "melting_point"
    assert decision["correlation_coefficient"] == 0.85
    assert decision["p_value"] == 0.001
    assert "decision_reason" in decision

def test_load_target_decision_file_not_found():
    """Test that FileNotFoundError is raised for missing file."""
    with pytest.raises(FileNotFoundError):
        load_target_decision(Path("/nonexistent/path.json"))

def test_generate_schema_melting_point():
    """Test schema generation with melting_point as target."""
    decision = {
        "target": "melting_point",
        "correlation_coefficient": 0.85,
        "p_value": 0.001,
        "threshold_used": 0.7,
        "decision_reason": "Test reason"
    }
    
    schema = generate_schema(decision)
    
    assert schema["properties"]["metadata"]["properties"]["target_variable"]["const"] == "melting_point"
    assert "data" in schema["properties"]
    assert schema["type"] == "object"

def test_generate_schema_latent_heat():
    """Test schema generation with latent_heat as target."""
    decision = {
        "target": "latent_heat",
        "correlation_coefficient": 0.65,
        "p_value": 0.05,
        "threshold_used": 0.7,
        "decision_reason": "Test reason"
    }
    
    schema = generate_schema(decision)
    
    assert schema["properties"]["metadata"]["properties"]["target_variable"]["const"] == "latent_heat"

def test_validate_schema_valid():
    """Test validation of a valid schema."""
    decision = {"target": "melting_point"}
    schema = generate_schema(decision)
    
    assert validate_schema(schema) is True

def test_validate_schema_empty():
    """Test validation fails for empty schema."""
    with pytest.raises(ValueError, match="Generated schema is empty"):
        validate_schema({})

def test_validate_schema_missing_required_keys():
    """Test validation fails for schema missing required keys."""
    schema = {"properties": {}}
    
    with pytest.raises(ValueError, match="Schema missing required key"):
        validate_schema(schema)

def test_validate_schema_missing_target_variable():
    """Test validation fails when target_variable is missing."""
    schema = {
        "$schema": "test",
        "title": "test",
        "description": "test",
        "type": "object",
        "properties": {
            "data": {"type": "array"}
        }
    }
    
    with pytest.raises(ValueError, match="Schema missing 'metadata' property"):
        validate_schema(schema)

def test_save_schema(temp_output_path):
    """Test saving schema to YAML file."""
    decision = {"target": "melting_point"}
    schema = generate_schema(decision)
    
    save_schema(schema, temp_output_path)
    
    assert temp_output_path.exists()
    
    # Verify the saved file is valid YAML
    with open(temp_output_path, 'r') as f:
        loaded_schema = yaml.safe_load(f)
    
    assert loaded_schema["properties"]["metadata"]["properties"]["target_variable"]["const"] == "melting_point"
