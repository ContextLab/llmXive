"""
Unit tests for the interaction schema validation logic.
Verifies that the schema file is valid and can be loaded.
"""
import os
import yaml
import jsonschema
import pytest
from pathlib import Path

# Path to the schema file relative to project root
SCHEMA_PATH = Path(__file__).parent.parent / "contracts" / "interaction_schema.schema.yaml"

@pytest.fixture
def schema():
    """Load the interaction schema."""
    if not SCHEMA_PATH.exists():
        pytest.fail(f"Schema file not found at {SCHEMA_PATH}")
    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def test_schema_is_valid_yaml(schema):
    """Ensure the schema is valid YAML."""
    assert schema is not None
    assert isinstance(schema, dict)

def test_schema_has_required_fields(schema):
    """Ensure the schema defines the required fields."""
    required_fields = {"post_text", "reply_text", "timestamp", "user_id"}
    assert "required" in schema
    assert set(schema["required"]) == required_fields

def test_schema_properties_exist(schema):
    """Ensure all required properties are defined in properties."""
    required_fields = {"post_text", "reply_text", "timestamp", "user_id"}
    assert "properties" in schema
    for field in required_fields:
        assert field in schema["properties"], f"Missing property definition for {field}"

def test_schema_types_are_correct(schema):
    """Ensure all required fields are typed as string."""
    for field in ["post_text", "reply_text", "timestamp", "user_id"]:
        assert schema["properties"][field]["type"] == "string"

def test_schema_timestamp_pattern(schema):
    """Ensure timestamp has a pattern constraint."""
    assert "pattern" in schema["properties"]["timestamp"]

def test_schema_validates_correct_data(schema):
    """Test that valid data passes validation."""
    valid_data = {
        "post_text": "Hello world",
        "reply_text": "Hi there!",
        "timestamp": "2023-10-27T10:00:00Z",
        "user_id": "user_123"
    }
    jsonschema.validate(instance=valid_data, schema=schema)

def test_schema_rejects_missing_required_field(schema):
    """Test that missing a required field raises an error."""
    invalid_data = {
        "post_text": "Hello",
        "reply_text": "Hi",
        # Missing timestamp and user_id
    }
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(instance=invalid_data, schema=schema)

def test_schema_rejects_wrong_type(schema):
    """Test that wrong data types raise an error."""
    invalid_data = {
        "post_text": "Hello",
        "reply_text": "Hi",
        "timestamp": "2023-10-27",
        "user_id": 12345  # Should be string
    }
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(instance=invalid_data, schema=schema)

def test_schema_rejects_extra_properties(schema):
    """Test that additional properties are rejected (additionalProperties: false)."""
    invalid_data = {
        "post_text": "Hello",
        "reply_text": "Hi",
        "timestamp": "2023-10-27T10:00:00Z",
        "user_id": "user_123",
        "extra_field": "should fail"
    }
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(instance=invalid_data, schema=schema)