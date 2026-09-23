"""
Contract test for the unified dataset schema.
Verifies that the schema file exists, is valid YAML, and defines the required fields.
"""
import os
import yaml
import pytest
from pathlib import Path

SCHEMA_PATH = Path("contracts/unified_dataset.schema.yaml")

@pytest.fixture
def schema():
    if not SCHEMA_PATH.exists():
        pytest.fail(f"Schema file not found at {SCHEMA_PATH}")
    with open(SCHEMA_PATH, "r") as f:
        return yaml.safe_load(f)

def test_schema_exists(schema):
    assert schema is not None

def test_schema_has_required_fields(schema):
    required = [
        "user_id",
        "loneliness_score",
        "usage_frequency",
        "session_duration",
        "attachment_anxiety_score",
        "attachment_avoidance_score",
        "age"
    ]
    properties = schema.get("properties", {})
    for field in required:
        assert field in properties, f"Required field '{field}' missing from schema properties"

def test_schema_types(schema):
    properties = schema.get("properties", {})
    
    assert properties["user_id"]["type"] == "string"
    assert properties["loneliness_score"]["type"] == "number"
    assert properties["usage_frequency"]["type"] == "number"
    assert properties["session_duration"]["type"] == "number"
    assert properties["attachment_anxiety_score"]["type"] == "number"
    assert properties["attachment_avoidance_score"]["type"] == "number"
    assert properties["age"]["type"] == "integer"

def test_schema_constraints(schema):
    properties = schema.get("properties", {})
    
    # Check bounds for scores
    assert properties["loneliness_score"].get("minimum") is not None
    assert properties["loneliness_score"].get("maximum") is not None
    
    assert properties["usage_frequency"].get("minimum") == 0
    assert properties["session_duration"].get("maximum") == 24.0
    
    assert properties["attachment_anxiety_score"].get("maximum") == 1.0
    assert properties["attachment_avoidance_score"].get("maximum") == 1.0

def test_schema_no_additional_properties(schema):
    assert schema.get("additionalProperties") is False, \
        "Schema should not allow additional properties to ensure strict data contract"