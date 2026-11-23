"""
Unit tests for the session schema (T019b).
Verifies that the schema file exists, is valid YAML, and defines the required fields.
"""
import yaml
import os
import json
from pathlib import Path

SCHEMA_PATH = Path("contracts/session.schema.yaml")

def test_schema_file_exists():
    assert SCHEMA_PATH.exists(), f"Schema file not found at {SCHEMA_PATH}"

def test_schema_is_valid_yaml():
    with open(SCHEMA_PATH, "r") as f:
        try:
            schema = yaml.safe_load(f)
            assert schema is not None
        except yaml.YAMLError as e:
            assert False, f"Invalid YAML in schema: {e}"

def test_schema_has_required_fields():
    with open(SCHEMA_PATH, "r") as f:
        schema = yaml.safe_load(f)
    
    required_fields = [
        "participant_id",
        "disability_type",
        "interface_type",
        "sequence",
        "start_time",
        "end_time",
        "error_count",
        "explanation_engagement_time_seconds",
        "sus_score",
        "status",
        "dropout_reason"
    ]
    
    assert "required" in schema, "Schema must have a 'required' list"
    for field in required_fields:
        assert field in schema["required"], f"Missing required field: {field}"

def test_schema_properties_defined():
    with open(SCHEMA_PATH, "r") as f:
        schema = yaml.safe_load(f)
    
    assert "properties" in schema, "Schema must have a 'properties' dict"
    
    expected_properties = {
        "participant_id": {"type": "string"},
        "disability_type": {"type": "string", "enum": ["visual", "motor", "cognitive", "auditory", "none", "other"]},
        "interface_type": {"type": "string", "enum": ["traditional", "explainable"]},
        "sequence": {"type": "array"},
        "start_time": {"type": "string", "format": "date-time"},
        "end_time": {"type": "string", "format": "date-time"},
        "error_count": {"type": "integer", "minimum": 0},
        "explanation_engagement_time_seconds": {"type": "number", "minimum": 0},
        "sus_score": {"type": "integer", "minimum": 0, "maximum": 100},
        "status": {"type": "string", "enum": ["complete", "incomplete"]},
        "dropout_reason": {"type": ["string", "null"]}
    }
    
    for prop, constraints in expected_properties.items():
        assert prop in schema["properties"], f"Missing property: {prop}"
        prop_def = schema["properties"][prop]
        
        # Check type
        if "type" in constraints:
            assert "type" in prop_def, f"Property {prop} missing type"
            assert prop_def["type"] == constraints["type"], f"Property {prop} has wrong type"
        
        # Check enum if present
        if "enum" in constraints:
            assert "enum" in prop_def, f"Property {prop} missing enum"
            assert set(prop_def["enum"]) == set(constraints["enum"]), f"Property {prop} has wrong enum values"

def test_schema_validates_sample_data():
    """
    Simple validation using jsonschema if available, otherwise basic structure check.
    """
    try:
        import jsonschema
    except ImportError:
        # If jsonschema isn't installed, we just verify the schema structure is valid
        # which is covered by other tests.
        return

    with open(SCHEMA_PATH, "r") as f:
        schema = yaml.safe_load(f)
    
    sample_session = {
        "participant_id": "P001",
        "disability_type": "visual",
        "interface_type": "explainable",
        "sequence": [1, 2],
        "start_time": "2023-10-01T10:00:00Z",
        "end_time": "2023-10-01T10:15:00Z",
        "error_count": 2,
        "explanation_engagement_time_seconds": 45.5,
        "sus_score": 85,
        "status": "complete",
        "dropout_reason": None
    }
    
    try:
        jsonschema.validate(instance=sample_session, schema=schema)
    except jsonschema.ValidationError as e:
        assert False, f"Sample session failed schema validation: {e.message}"