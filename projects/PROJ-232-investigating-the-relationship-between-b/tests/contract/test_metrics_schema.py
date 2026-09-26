"""
Contract test for network metrics JSON schema (T016).

Validates that the JSON output from graph metric calculations
conforms to the expected schema defined in contracts/output.schema.yaml.
"""

import json
import os
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

import pytest
import yaml

# Project root is assumed to be the parent of the tests directory
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
CONTRACTS_DIR = PROJECT_ROOT / "contracts"
OUTPUT_SCHEMA_PATH = CONTRACTS_DIR / "output.schema.yaml"


def load_output_schema() -> Dict[str, Any]:
    """Load the output schema definition from YAML."""
    if not OUTPUT_SCHEMA_PATH.exists():
        raise FileNotFoundError(
            f"Output schema file not found at {OUTPUT_SCHEMA_PATH}. "
            "Ensure T007 has created contracts/output.schema.yaml."
        )
    with open(OUTPUT_SCHEMA_PATH, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def validate_type(value: Any, expected_type: str, path: str) -> List[str]:
    """Validate a value against a simple type constraint."""
    errors = []
    type_map = {
        "string": str,
        "integer": int,
        "number": (int, float),
        "boolean": bool,
        "array": list,
        "object": dict,
    }

    if expected_type not in type_map:
        errors.append(f"{path}: Unknown type '{expected_type}' in schema")
        return errors

    expected_python_type = type_map[expected_type]
    if not isinstance(value, expected_python_type):
        # Special case: int is also a number, but if schema says 'integer', float is wrong
        if expected_type == "integer" and isinstance(value, bool):
            # bool is subclass of int in Python, but logically distinct
            errors.append(f"{path}: Expected integer, got boolean")
        elif expected_type == "integer" and isinstance(value, float) and not value.is_integer():
            errors.append(f"{path}: Expected integer, got float with decimal part")
        else:
            errors.append(f"{path}: Expected {expected_type}, got {type(value).__name__}")
    return errors


def validate_value(
    value: Any,
    schema_part: Dict[str, Any],
    path: str,
    required_fields: Optional[Set[str]] = None
) -> List[str]:
    """Recursively validate a value against a schema part."""
    errors = []

    if "type" in schema_part:
        errors.extend(validate_type(value, schema_part["type"], path))
        if errors:
            return errors  # Stop if type is wrong

    if schema_part.get("type") == "object" and isinstance(value, dict):
        # Check required fields
        if "required" in schema_part:
            missing = set(schema_part["required"]) - set(value.keys())
            for field in missing:
                errors.append(f"{path}: Missing required field '{field}'")

        # Validate properties
        properties = schema_part.get("properties", {})
        for key, val in value.items():
            if key in properties:
                errors.extend(
                    validate_value(val, properties[key], f"{path}.{key}")
                )
            else:
                # Optional: could enforce no additional properties, but usually lenient
                pass

    elif schema_part.get("type") == "array" and isinstance(value, list):
        items_schema = schema_part.get("items", {})
        for i, item in enumerate(value):
            errors.extend(
                validate_value(item, items_schema, f"{path}[{i}]")
            )

    return errors


@pytest.fixture
def output_schema():
    """Load the output schema for the test."""
    return load_output_schema()


def test_metrics_schema_structure(output_schema):
    """Test that the metrics schema has the expected root structure."""
    assert "NetworkMetrics" in output_schema, "Schema must define 'NetworkMetrics' root object"
    metrics_schema = output_schema["NetworkMetrics"]
    assert metrics_schema.get("type") == "object", "NetworkMetrics must be an object"


def test_metrics_schema_required_fields(output_schema):
    """Test that the schema enforces required fields for network metrics."""
    metrics_schema = output_schema["NetworkMetrics"]
    required_fields = set(metrics_schema.get("required", []))

    expected_required = {
        "global_efficiency",
        "modularity",
        "participation_coefficient",
        "network_efficiency",
        "edge_strength"
    }

    # Check that the schema declares these as required
    missing_in_schema = expected_required - required_fields
    assert not missing_in_schema, (
        f"Schema missing 'required' declaration for: {missing_in_schema}"
    )


def test_valid_metrics_json(output_schema):
    """Test validation of a correctly formatted metrics JSON."""
    valid_metrics = {
        "subject_id": "sub-01",
        "global_efficiency": 0.452,
        "modularity": 0.38,
        "participation_coefficient": 0.72,
        "network_efficiency": {
            "DMN": 0.41,
            "Salience": 0.39,
            "Visual": 0.44
        },
        "edge_strength": [0.12, -0.05, 0.88]  # Simplified list for schema test
    }

    errors = validate_value(valid_metrics, output_schema["NetworkMetrics"], "root")
    assert not errors, f"Valid metrics failed schema validation: {errors}"


def test_missing_required_field(output_schema):
    """Test that missing required fields are detected."""
    invalid_metrics = {
        "subject_id": "sub-01",
        "global_efficiency": 0.452,
        # Missing modularity, participation_coefficient, etc.
        "network_efficiency": {"DMN": 0.41},
        "edge_strength": [0.12]
    }

    errors = validate_value(invalid_metrics, output_schema["NetworkMetrics"], "root")
    assert errors, "Should detect missing required fields"
    assert any("Missing required field" in e for e in errors), (
        f"Errors should mention missing fields: {errors}"
    )


def test_wrong_type_field(output_schema):
    """Test that wrong data types are detected."""
    invalid_metrics = {
        "subject_id": "sub-01",
        "global_efficiency": "not_a_number",  # Should be number
        "modularity": 0.38,
        "participation_coefficient": 0.72,
        "network_efficiency": {"DMN": 0.41},
        "edge_strength": [0.12]
    }

    errors = validate_value(invalid_metrics, output_schema["NetworkMetrics"], "root")
    assert errors, "Should detect type mismatch"
    assert any("Expected number" in e for e in errors), (
        f"Errors should mention type mismatch for global_efficiency: {errors}"
    )


def test_invalid_network_efficiency_structure(output_schema):
    """Test that invalid network_efficiency structure is detected."""
    invalid_metrics = {
        "subject_id": "sub-01",
        "global_efficiency": 0.452,
        "modularity": 0.38,
        "participation_coefficient": 0.72,
        "network_efficiency": "string_instead_of_object",  # Should be object
        "edge_strength": [0.12]
    }

    errors = validate_value(invalid_metrics, output_schema["NetworkMetrics"], "root")
    assert errors, "Should detect invalid network_efficiency structure"
    assert any("Expected object" in e for e in errors), (
        f"Errors should mention type mismatch for network_efficiency: {errors}"
    )


def test_load_from_temp_file(output_schema):
    """Test that a valid JSON file can be loaded and validated from disk."""
    valid_metrics = {
        "subject_id": "sub-01",
        "global_efficiency": 0.452,
        "modularity": 0.38,
        "participation_coefficient": 0.72,
        "network_efficiency": {
            "DMN": 0.41,
            "Salience": 0.39,
            "Visual": 0.44
        },
        "edge_strength": [0.12, -0.05, 0.88]
    }

    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".json", delete=False, encoding="utf-8"
    ) as f:
        json.dump(valid_metrics, f)
        temp_path = f.name

    try:
        with open(temp_path, "r", encoding="utf-8") as f:
            loaded_data = json.load(f)

        errors = validate_value(loaded_data, output_schema["NetworkMetrics"], "root")
        assert not errors, f"Loaded valid JSON failed validation: {errors}"
    finally:
        os.unlink(temp_path)