"""
Contract tests for metadata schema validation.
Validates data against the schema defined in tests/contract/schemas/metadata_schema.yaml
"""
import os
import re
import yaml
from pathlib import Path
from typing import Dict, Any, List, Tuple

import pytest

# Import the schema loader if it exists, otherwise define helper here
SCHEMA_PATH = Path(__file__).parent / "schemas" / "metadata_schema.yaml"


def load_schema(schema_path: Path) -> Dict[str, Any]:
    """Load YAML schema from file."""
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    with open(schema_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def validate_record(record: Dict[str, Any], schema: Dict[str, Any]) -> List[str]:
    """
    Validate a single record against the schema.
    Returns a list of error messages.
    """
    errors = []
    properties = schema.get("properties", {})
    required_fields = schema.get("required", [])
    additional_properties = schema.get("additionalProperties", True)

    # Check required fields
    for field in required_fields:
        if field not in record:
            errors.append(f"Missing required field: {field}")

    # Check field types and constraints
    for key, value in record.items():
        if key not in properties:
            if not additional_properties:
                errors.append(f"Unexpected field: {key}")
            continue

        field_def = properties[key]
        expected_type = field_def.get("type")
        
        # Type checking
        if value is None:
            if not field_def.get("nullable", False):
                errors.append(f"Field '{key}' cannot be null")
            continue

        if expected_type == "string":
            if not isinstance(value, str):
                errors.append(f"Field '{key}' must be a string, got {type(value).__name__}")
            else:
                # Min length check
                min_len = field_def.get("minLength")
                if min_len is not None and len(value) < min_len:
                    errors.append(f"Field '{key}' length {len(value)} < minimum {min_len}")
                
                # Pattern check
                pattern = field_def.get("pattern")
                if pattern:
                    if not re.match(pattern, value):
                        errors.append(f"Field '{key}' does not match pattern: {pattern}")

        elif expected_type == "integer":
            if not isinstance(value, int) or isinstance(value, bool):
                errors.append(f"Field '{key}' must be an integer, got {type(value).__name__}")
            else:
                min_val = field_def.get("minimum")
                max_val = field_def.get("maximum")
                if min_val is not None and value < min_val:
                    errors.append(f"Field '{key}' value {value} < minimum {min_val}")
                if max_val is not None and value > max_val:
                    errors.append(f"Field '{key}' value {value} > maximum {max_val}")

        elif expected_type == "number":
            if not isinstance(value, (int, float)) or isinstance(value, bool):
                errors.append(f"Field '{key}' must be a number, got {type(value).__name__}")
            else:
                min_val = field_def.get("minimum")
                max_val = field_def.get("maximum")
                if min_val is not None and value < min_val:
                    errors.append(f"Field '{key}' value {value} < minimum {min_val}")
                if max_val is not None and value > max_val:
                    errors.append(f"Field '{key}' value {value} > maximum {max_val}")

        elif expected_type == "boolean":
            if not isinstance(value, bool):
                errors.append(f"Field '{key}' must be a boolean, got {type(value).__name__}")

    return errors


def test_metadata_schema_validation():
    """
    Contract test for metadata schema validation.
    Validates a set of test records against the schema in metadata_schema.yaml.
    """
    # Load schema
    schema = load_schema(SCHEMA_PATH)
    
    # Define test records (valid and invalid cases)
    valid_record = {
        "track_id": "550e8400-e29b-41d4-a716-446655440000",
        "year": 2020,
        "artist": "Test Artist",
        "title": "Test Title",
        "genre": "Rock",
        "playlist_id": "pl_12345",
        "album": "Test Album",
        "duration_ms": 180000,
        "match_confidence": 0.95
    }

    invalid_record_missing_required = {
        "track_id": "550e8400-e29b-41d4-a716-446655440000",
        "artist": "Test Artist",
        # Missing year, title, genre, playlist_id
    }

    invalid_record_type_error = {
        "track_id": "550e8400-e29b-41d4-a716-446655440000",
        "year": "2020",  # Should be integer
        "artist": "Test Artist",
        "title": "Test Title",
        "genre": "Rock",
        "playlist_id": "pl_12345"
    }

    invalid_record_pattern_error = {
        "track_id": "invalid-uuid",  # Should be UUID format
        "year": 2020,
        "artist": "Test Artist",
        "title": "Test Title",
        "genre": "Rock",
        "playlist_id": "pl_12345"
    }

    invalid_record_out_of_range = {
        "track_id": "550e8400-e29b-41d4-a716-446655440000",
        "year": 1800,  # Out of range (1900-2030)
        "artist": "Test Artist",
        "title": "Test Title",
        "genre": "Rock",
        "playlist_id": "pl_12345"
    }

    test_cases = [
        (valid_record, True, "Valid record should pass"),
        (invalid_record_missing_required, False, "Record missing required fields should fail"),
        (invalid_record_type_error, False, "Record with wrong type should fail"),
        (invalid_record_pattern_error, False, "Record with invalid UUID pattern should fail"),
        (invalid_record_out_of_range, False, "Record with out-of-range year should fail"),
    ]

    all_passed = True
    for record, should_pass, description in test_cases:
        errors = validate_record(record, schema)
        passed = (len(errors) == 0)
        
        if should_pass and not passed:
            all_passed = False
            pytest.fail(f"Test failed: {description}. Errors: {errors}")
        elif not should_pass and passed:
            all_passed = False
            pytest.fail(f"Test failed: {description}. Expected errors but got none.")
        
        # If expected to fail, ensure we have errors
        if not should_pass and len(errors) == 0:
            all_passed = False
            pytest.fail(f"Test failed: {description}. Expected validation errors but got none.")

    assert all_passed, "One or more contract tests failed."