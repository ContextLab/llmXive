"""
Contract test for T009b: Validate skill.json schema against contracts/skill.schema.yaml.
"""
import os
import sys
import json
import yaml
import pytest
from jsonschema import validate, ValidationError

# Add parent directory to path to allow imports if needed, though this is a standalone test
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

SCHEMA_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "contracts",
    "skill.schema.yaml"
)

def load_schema():
    """Load the skill schema from YAML."""
    if not os.path.exists(SCHEMA_PATH):
        pytest.fail(f"Schema file not found at {SCHEMA_PATH}")
    with open(SCHEMA_PATH, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

def test_schema_loads():
    """Verify the schema file is valid YAML and loads correctly."""
    schema = load_schema()
    assert schema is not None
    assert 'properties' in schema
    assert 'skill_id' in schema['properties']
    assert 'function_code' in schema['properties']
    assert 'embedding_vector' in schema['properties']
    assert 'usage_count' in schema['properties']

def test_valid_skill_object():
    """Validate a sample skill object against the schema."""
    schema = load_schema()
    
    valid_skill = {
        "skill_id": "skill_001",
        "function_code": "def add(a, b): return a + b",
        "embedding_vector": [0.1, 0.2, 0.3, 0.4, 0.5],
        "usage_count": 10
    }
    
    try:
        validate(instance=valid_skill, schema=schema)
    except ValidationError as e:
        pytest.fail(f"Valid skill object failed schema validation: {e.message}")

def test_missing_required_field():
    """Verify that a skill object missing a required field fails validation."""
    schema = load_schema()
    
    invalid_skill = {
        "skill_id": "skill_002",
        "function_code": "def sub(a, b): return a - b",
        # Missing embedding_vector and usage_count
    }
    
    with pytest.raises(ValidationError):
        validate(instance=invalid_skill, schema=schema)

def test_wrong_type_field():
    """Verify that a skill object with wrong type for a field fails validation."""
    schema = load_schema()
    
    invalid_skill = {
        "skill_id": "skill_003",
        "function_code": "def mul(a, b): return a * b",
        "embedding_vector": "not a list",  # Should be list of numbers
        "usage_count": 5
    }
    
    with pytest.raises(ValidationError):
        validate(instance=invalid_skill, schema=schema)

def test_negative_usage_count():
    """Verify that negative usage_count fails validation."""
    schema = load_schema()
    
    invalid_skill = {
        "skill_id": "skill_004",
        "function_code": "def div(a, b): return a / b",
        "embedding_vector": [0.1, 0.2],
        "usage_count": -1
    }
    
    with pytest.raises(ValidationError):
        validate(instance=invalid_skill, schema=schema)