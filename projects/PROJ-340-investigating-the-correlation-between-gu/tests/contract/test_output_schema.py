"""
Contract test for correlation output schema (T018).

This test validates the existence and structure of the output schema file
defined in specs/001-gut-microbiome-sleep-architecture/contracts/output.schema.yaml.
It ensures the schema matches the expected CorrelationResult structure.

This task validates the schema definition (T005a), NOT the analysis logic.
"""

import os
import yaml
import pytest
from pathlib import Path


# Project root relative to this file
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
SCHEMA_PATH = (
    PROJECT_ROOT
    / "specs"
    / "001-gut-microbiome-sleep-architecture"
    / "contracts"
    / "output.schema.yaml"
)


@pytest.fixture
def schema():
    """Load the output schema YAML file."""
    if not SCHEMA_PATH.exists():
        pytest.fail(f"Output schema file not found at {SCHEMA_PATH}")

    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        try:
            return yaml.safe_load(f)
        except yaml.YAMLError as e:
            pytest.fail(f"Invalid YAML in output schema: {e}")


def test_schema_file_exists(schema):
    """Assert the schema file is loadable and non-empty."""
    assert schema is not None
    assert isinstance(schema, dict)
    assert len(schema) > 0


def test_schema_has_required_top_level_keys(schema):
    """Assert the schema contains required top-level keys."""
    required_keys = {"$schema", "title", "type", "properties"}
    missing = required_keys - set(schema.keys())
    assert not missing, f"Missing required top-level keys: {missing}"


def test_schema_type_is_object(schema):
    """Assert the root type is 'object'."""
    assert schema.get("type") == "object", "Root schema type must be 'object'"


def test_schema_has_properties_section(schema):
    """Assert the schema has a 'properties' section."""
    assert "properties" in schema
    assert isinstance(schema["properties"], dict)
    assert len(schema["properties"]) > 0


def test_schema_properties_match_expected_correlation_result(schema):
    """
    Assert the schema properties match the expected CorrelationResult structure.

    Expected fields based on T005a and US2 requirements:
    - pair_id (string)
    - predictor (string)
    - outcome (string)
    - method (string)
    - correlation_coefficient (number)
    - p_value (number)
    - q_value (number)  # BH-adjusted p-value
    - significance (boolean)
    - confidence_interval (object with lower/upper)
    """
    properties = schema["properties"]
    expected_fields = {
        "pair_id",
        "predictor",
        "outcome",
        "method",
        "correlation_coefficient",
        "p_value",
        "q_value",
        "significance",
        "confidence_interval",
    }

    missing_fields = expected_fields - set(properties.keys())
    assert not missing_fields, f"Missing expected fields in properties: {missing_fields}"


def test_schema_field_types(schema):
    """Assert specific fields have correct types defined."""
    properties = schema["properties"]

    # String fields
    string_fields = ["pair_id", "predictor", "outcome", "method"]
    for field in string_fields:
        if field in properties:
            assert properties[field].get("type") == "string", (
                f"Field '{field}' should be type 'string'"
            )

    # Number fields
    number_fields = ["correlation_coefficient", "p_value", "q_value"]
    for field in number_fields:
        if field in properties:
            assert properties[field].get("type") == "number", (
                f"Field '{field}' should be type 'number'"
            )

    # Boolean field
    if "significance" in properties:
        assert properties["significance"].get("type") == "boolean", (
            "Field 'significance' should be type 'boolean'"
        )

    # Object field for confidence_interval
    if "confidence_interval" in properties:
        ci_prop = properties["confidence_interval"]
        assert ci_prop.get("type") == "object", (
            "Field 'confidence_interval' should be type 'object'"
        )
        # Check for lower/upper sub-fields if defined
        ci_props = ci_prop.get("properties", {})
        if ci_props:
            assert "lower" in ci_props and "upper" in ci_props, (
                "confidence_interval should have 'lower' and 'upper' properties"
            )


def test_schema_has_required_fields(schema):
    """Assert the schema defines required fields."""
    required = schema.get("required", [])
    expected_required = [
        "pair_id",
        "predictor",
        "outcome",
        "method",
        "correlation_coefficient",
        "p_value",
        "significance",
    ]
    missing_required = set(expected_required) - set(required)
    assert not missing_required, f"Missing required fields in schema: {missing_required}"