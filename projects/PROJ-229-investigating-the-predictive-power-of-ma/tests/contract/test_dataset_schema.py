"""
Contract test for the dataset schema (T007).
Verifies that the schema file exists, is valid YAML, and conforms to the expected structure.
"""
import yaml
import json
import pytest
from pathlib import Path

SCHEMA_PATH = Path("contracts/dataset.schema.yaml")

def test_schema_file_exists():
    """Verify that the dataset schema file exists."""
    assert SCHEMA_PATH.exists(), f"Schema file not found at {SCHEMA_PATH}"

def test_schema_is_valid_yaml():
    """Verify that the schema file is valid YAML."""
    try:
        with open(SCHEMA_PATH, 'r') as f:
            schema = yaml.safe_load(f)
        assert isinstance(schema, dict), "Schema root must be a dictionary."
    except yaml.YAMLError as e:
        pytest.fail(f"Invalid YAML in schema file: {e}")

def test_schema_has_required_top_level_keys():
    """Verify the schema contains required JSON Schema keys."""
    with open(SCHEMA_PATH, 'r') as f:
        schema = yaml.safe_load(f)
    
    required_keys = ["type", "required", "properties"]
    for key in required_keys:
        assert key in schema, f"Schema missing required key: {key}"

def test_schema_type_is_object():
    """Verify the schema type is 'object'."""
    with open(SCHEMA_PATH, 'r') as f:
        schema = yaml.safe_load(f)
    
    assert schema["type"] == "object", "Schema type must be 'object'."

def test_schema_properties_defined():
    """Verify that expected properties are defined in the schema."""
    with open(SCHEMA_PATH, 'r') as f:
        schema = yaml.safe_load(f)
    
    expected_static_props = [
        "material_id",
        "composition",
        "elemental_count",
        "formation_energy",
        "density",
        "elemental_features",
        "graph_features"
    ]
    
    for prop in expected_static_props:
        assert prop in schema["properties"], f"Missing property: {prop}"
        assert "type" in schema["properties"][prop], f"Property {prop} missing 'type' definition."

def test_schema_additional_properties_false():
    """Verify that additionalProperties is set to false."""
    with open(SCHEMA_PATH, 'r') as f:
        schema = yaml.safe_load(f)
    
    assert schema.get("additionalProperties") is False, "additionalProperties must be False."

def test_schema_metadata_present():
    """Verify that metadata about the target decision is present."""
    with open(SCHEMA_PATH, 'r') as f:
        schema = yaml.safe_load(f)
    
    assert "metadata" in schema, "Schema must include 'metadata' section."
    assert "target_field" in schema["metadata"], "Metadata must include 'target_field'."
    assert "decision_rationale" in schema["metadata"], "Metadata must include 'decision_rationale'."