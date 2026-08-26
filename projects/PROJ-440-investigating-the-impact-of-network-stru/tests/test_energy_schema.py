"""
Tests for the energy decay schema.
These tests verify that the schema file exists, is valid YAML, and defines
the expected structure for the energy_decay.csv file.
"""
import os
import sys
import yaml
import pytest
from pathlib import Path

# Add the project root to the path if needed
project_root = Path(__file__).parent.parent
contracts_dir = project_root / "contracts"

@pytest.fixture
def schema():
    """Load the energy schema from the contracts directory."""
    schema_path = contracts_dir / "energy_schema.schema.yaml"
    if not schema_path.exists():
        pytest.fail(f"Schema file not found at {schema_path}")
    
    with open(schema_path, "r") as f:
        return yaml.safe_load(f)

def test_schema_exists():
    """Test that the schema file exists."""
    schema_path = contracts_dir / "energy_schema.schema.yaml"
    assert schema_path.exists(), f"Schema file missing at {schema_path}"

def test_schema_is_valid_yaml(schema):
    """Test that the schema is valid YAML."""
    assert isinstance(schema, dict), "Schema should be a dictionary"

def test_schema_has_required_fields(schema):
    """Test that the schema has the required fields."""
    required_fields = [
        "graph_id", "class", "N", "decay_rate", "r_squared", "status"
    ]
    properties = schema.get("properties", {})
    
    for field in required_fields:
        assert field in properties, f"Missing required field: {field}"

def test_schema_field_types(schema):
    """Test that the schema defines correct types for fields."""
    properties = schema.get("properties", {})
    
    # Check string fields
    string_fields = ["graph_id", "class", "status"]
    for field in string_fields:
        if field in properties:
            assert properties[field]["type"] == "string", f"Field {field} should be string"
    
    # Check integer fields
    integer_fields = ["N", "simulation_seed"]
    for field in integer_fields:
        if field in properties:
            assert properties[field]["type"] == "integer", f"Field {field} should be integer"
    
    # Check number fields
    number_fields = ["decay_rate", "r_squared", "fit_frequency", "fit_amplitude", "fit_phase", "fit_offset"]
    for field in number_fields:
        if field in properties:
            assert properties[field]["type"] == "number", f"Field {field} should be number"

def test_schema_has_required_list(schema):
    """Test that the schema has a required list."""
    assert "required" in schema, "Schema should have a 'required' list"
    assert isinstance(schema["required"], list), "'required' should be a list"

def test_schema_descriptions(schema):
    """Test that all fields have descriptions."""
    properties = schema.get("properties", {})
    for field, details in properties.items():
        assert "description" in details, f"Field {field} missing description"

def test_schema_title_and_description(schema):
    """Test that the schema has title and description."""
    assert "title" in schema, "Schema should have a title"
    assert "description" in schema, "Schema should have a description"
    assert "Energy Decay" in schema["title"], "Title should mention 'Energy Decay'"

def test_schema_additional_properties(schema):
    """Test that additionalProperties is set to false."""
    assert schema.get("additionalProperties") is False, \
        "Schema should not allow additional properties"

def test_schema_matches_csv_columns():
    """
    Verify that the schema columns match the expected CSV columns:
    graph_id, decay_rate, r_squared, status, class, N, and optional fit parameters.
    """
    expected_columns = [
        "graph_id", "decay_rate", "r_squared", "status", "class", "N",
        "fit_frequency", "fit_amplitude", "fit_phase", "fit_offset",
        "simulation_seed", "timestamp"
    ]
    
    schema_path = contracts_dir / "energy_schema.schema.yaml"
    with open(schema_path, "r") as f:
        schema = yaml.safe_load(f)
    
    properties = schema.get("properties", {})
    schema_columns = list(properties.keys())
    
    for col in expected_columns:
        assert col in schema_columns, f"Expected column '{col}' not found in schema"
