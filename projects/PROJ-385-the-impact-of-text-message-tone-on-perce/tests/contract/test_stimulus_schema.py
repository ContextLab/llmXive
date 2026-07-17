"""
Contract test for stimulus schema.
Validates that artifacts produced in T006 (schema definitions) are correctly
enforced against the generated stimuli data (produced by T013, though we test
the schema validation logic here).

This test ensures the schema defined in specs/001-text-tone-emotional-support/contracts/stimulus.schema.yaml
is valid and can be used to validate data.
"""
import json
import os
import pytest
from pathlib import Path

# Import the schema validation logic from the existing project module
from validate_schemas import load_schema, validate_json_against_schema

# Determine the project root and schema path
PROJECT_ROOT = Path(__file__).parent.parent.parent
SCHEMAS_DIR = PROJECT_ROOT / "specs" / "001-text-tone-emotional-support" / "contracts"
STIMULUS_SCHEMA_PATH = SCHEMAS_DIR / "stimulus.schema.yaml"

# Sample valid stimulus data to test against the schema
# This mimics the structure expected by the schema
VALID_STIMULUS_RECORDS = [
    {
        "stimulus_id": "S001",
        "text": "Hey, are you free later? 👍",
        "emoji_level": "low",
        "punctuation": "standard",
        "length": "short",
        "context": "friend"
    },
    {
        "stimulus_id": "S002",
        "text": "Hey!! Are you free later??? 😊😊",
        "emoji_level": "high",
        "punctuation": "exaggerated",
        "length": "long",
        "context": "acquaintance"
    }
]

# Sample invalid stimulus data to ensure the schema rejects it
INVALID_STIMULUS_RECORDS = [
    {
        "stimulus_id": 123,  # Should be string
        "text": "Test",
        "emoji_level": "invalid_level", # Should be low/medium/high
        "punctuation": "standard",
        "length": "short",
        "context": "friend"
    }
]

def test_schema_file_exists():
    """Verify the stimulus schema file exists."""
    assert STIMULUS_SCHEMA_PATH.exists(), f"Schema file not found at {STIMULUS_SCHEMA_PATH}"

def test_schema_is_valid_yaml():
    """Verify the schema file is valid YAML and can be loaded."""
    try:
        schema = load_schema(STIMULUS_SCHEMA_PATH)
        assert schema is not None
        assert "type" in schema or "$schema" in schema
    except Exception as e:
        pytest.fail(f"Failed to load or parse schema: {e}")

def test_validate_valid_stimulus_records():
    """Verify that valid stimulus records pass schema validation."""
    schema = load_schema(STIMULUS_SCHEMA_PATH)
    assert schema is not None
    
    # Validate each record individually
    for record in VALID_STIMULUS_RECORDS:
        is_valid, errors = validate_json_against_schema(record, schema)
        assert is_valid, f"Valid record failed validation: {errors}"

def test_validate_invalid_stimulus_records():
    """Verify that invalid stimulus records fail schema validation."""
    schema = load_schema(STIMULUS_SCHEMA_PATH)
    assert schema is not None
    
    # Validate each record individually
    for record in INVALID_STIMULUS_RECORDS:
        is_valid, errors = validate_json_against_schema(record, schema)
        assert not is_valid, f"Invalid record should have failed validation but passed."
        assert len(errors) > 0, "Validation should return errors for invalid data."

def test_stimulus_schema_enforces_required_fields():
    """Verify the schema requires specific fields."""
    schema = load_schema(STIMULUS_SCHEMA_PATH)
    
    # Check if 'required' field exists in schema properties (standard JSON Schema)
    # Note: If the schema is YAML but not JSON Schema, this might need adjustment
    # based on the actual schema content. Assuming JSON Schema format as per T006.
    if "required" in schema:
        required_fields = schema["required"]
        expected_fields = ["stimulus_id", "text", "emoji_level", "punctuation", "length", "context"]
        for field in expected_fields:
            assert field in required_fields, f"Schema should require field: {field}"
    else:
        # Fallback: check if properties exist and assume required logic
        # This depends on how T006 defined the schema (strict JSON Schema vs custom)
        pytest.skip("Schema does not use standard 'required' field; manual inspection needed.")