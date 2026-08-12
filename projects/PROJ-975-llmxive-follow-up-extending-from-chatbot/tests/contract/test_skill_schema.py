"""
Contract test for skill.schema.yaml.
Validates that a sample skill object conforms to the defined schema.
"""
import os
import json
import yaml
import pytest
from jsonschema import validate, ValidationError, Draft7Validator

# Path to the schema file (relative to project root)
SCHEMA_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
    "contracts",
    "skill.schema.yaml"
)

@pytest.fixture
def skill_schema():
    """Load the skill schema from disk."""
    if not os.path.exists(SCHEMA_PATH):
        pytest.fail(f"Schema file not found at {SCHEMA_PATH}")
    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

@pytest.fixture
def valid_skill():
    """Generate a valid sample skill object."""
    return {
        "skill_id": "skill_001",
        "function_code": "def add(a, b):\n    return a + b",
        "embedding_vector": [0.1] * 384,  # Simulate a 384-dim vector
        "usage_count": 5
    }

@pytest.fixture
def invalid_skill_missing_id():
    """Generate an invalid skill object missing skill_id."""
    return {
        "function_code": "def add(a, b): return a + b",
        "embedding_vector": [0.1] * 384,
        "usage_count": 5
    }

@pytest.fixture
def invalid_skill_wrong_type():
    """Generate an invalid skill object with wrong type for usage_count."""
    return {
        "skill_id": "skill_001",
        "function_code": "def add(a, b): return a + b",
        "embedding_vector": [0.1] * 384,
        "usage_count": "five"  # Should be integer
    }

def test_schema_loads(skill_schema):
    """Verify the schema itself is valid JSON Schema."""
    Draft7Validator.check_schema(skill_schema)

def test_valid_skill_passes(skill_schema, valid_skill):
    """Verify a valid skill object passes validation."""
    validate(instance=valid_skill, schema=skill_schema)

def test_missing_required_field_fails(skill_schema, invalid_skill_missing_id):
    """Verify validation fails when required field is missing."""
    with pytest.raises(ValidationError):
        validate(instance=invalid_skill_missing_id, schema=skill_schema)

def test_wrong_type_fails(skill_schema, invalid_skill_wrong_type):
    """Verify validation fails when field type is incorrect."""
    with pytest.raises(ValidationError):
        validate(instance=invalid_skill_wrong_type, schema=skill_schema)

def test_embedding_vector_structure(skill_schema):
    """Verify embedding_vector must be an array of numbers."""
    invalid_vec = {
        "skill_id": "skill_001",
        "function_code": "def f(): pass",
        "embedding_vector": "not_a_vector",
        "usage_count": 0
    }
    with pytest.raises(ValidationError):
        validate(instance=invalid_vec, schema=skill_schema)

def test_additional_properties_forbidden(skill_schema):
    """Verify that additional properties are forbidden at the root level."""
    extra_prop_skill = {
        "skill_id": "skill_001",
        "function_code": "def f(): pass",
        "embedding_vector": [0.1] * 384,
        "usage_count": 0,
        "extra_field": "should_fail"
    }
    with pytest.raises(ValidationError):
        validate(instance=extra_prop_skill, schema=skill_schema)