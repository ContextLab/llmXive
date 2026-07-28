"""
Contract test for stimulus schema.
Validates that artifacts produced in T006 (schema definitions) are correctly
enforced against the generated stimuli data (produced by T013).

This test ensures the schema defined in specs/001-text-tone-emotional-support/contracts/stimulus.schema.yaml
is valid and can be used to validate the actual data in data/raw/stimuli.csv.
"""
import csv
import json
import os
import pytest
from pathlib import Path

# Import the schema validation logic from the existing project module
from code.validate_schemas import load_schema, validate_json_against_schema
from code.config import get_raw_data_dir, get_specs_dir

# Determine paths based on project config
SCHEMAS_DIR = get_specs_dir() / "001-text-tone-emotional-support" / "contracts"
STIMULUS_SCHEMA_PATH = SCHEMAS_DIR / "stimulus.schema.yaml"
STIMULI_DATA_PATH = get_raw_data_dir() / "stimuli.csv"

# Sample valid stimulus data to test against the schema (in-memory for unit validation)
# These match the schema fields: id, text, emoji_count, punctuation_type, length_category, scenario_id
VALID_STIMULUS_RECORDS = [
    {
        "id": "S001",
        "text": "Hey, are you free later? 👍",
        "emoji_count": 1,
        "punctuation_type": "standard",
        "length_category": "short",
        "scenario_id": "SC01"
    },
    {
        "id": "S002",
        "text": "Hey!! Are you free later??? 😊😊",
        "emoji_count": 2,
        "punctuation_type": "exaggerated",
        "length_category": "long",
        "scenario_id": "SC01"
    }
]

# Sample invalid stimulus data to ensure the schema rejects it
INVALID_STIMULUS_RECORDS = [
    {
        "id": 123,  # Should be string
        "text": "Test",
        "emoji_count": "low", # Should be integer
        "punctuation_type": "standard",
        "length_category": "short",
        "scenario_id": "SC01"
    },
    {
        "id": "S003",
        "text": "Test",
        "emoji_count": 1,
        "punctuation_type": "invalid_type", # Should be standard/exaggerated
        "length_category": "short",
        "scenario_id": "SC01"
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
    if "required" in schema:
        required_fields = schema["required"]
        # Based on T006 schema definition: id, text, emoji_count, punctuation_type, length_category
        expected_fields = ["id", "text", "emoji_count", "punctuation_type", "length_category", "scenario_id"]
        for field in expected_fields:
            assert field in required_fields, f"Schema should require field: {field}"
    else:
        # Fallback: check if properties exist and assume required logic
        pytest.skip("Schema does not use standard 'required' field; manual inspection needed.")

def test_generated_stimuli_csv_validates_against_schema():
    """
    Integration contract test: Validates the actual generated stimuli.csv file
    against the defined schema.
    """
    assert STIMULI_DATA_PATH.exists(), f"Generated stimuli file not found at {STIMULI_DATA_PATH}"

    schema = load_schema(STIMULUS_SCHEMA_PATH)
    assert schema is not None

    with open(STIMULI_DATA_PATH, mode='r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        row_count = 0
        for row in reader:
            row_count += 1
            # Convert row values to appropriate types if necessary
            # The CSV reader returns strings. The schema expects:
            # id (string), text (string), emoji_count (integer), punctuation_type (string), length_category (string)
            # We must cast emoji_count to int for validation if the schema enforces integer type.
            if "emoji_count" in row:
                try:
                    row["emoji_count"] = int(row["emoji_count"])
                except ValueError:
                    pytest.fail(f"Row {row_count} has non-integer emoji_count: {row['emoji_count']}")

            is_valid, errors = validate_json_against_schema(row, schema)
            assert is_valid, f"Row {row_count} in stimuli.csv failed validation: {errors}. Row: {row}"

    assert row_count > 0, "stimuli.csv is empty."
