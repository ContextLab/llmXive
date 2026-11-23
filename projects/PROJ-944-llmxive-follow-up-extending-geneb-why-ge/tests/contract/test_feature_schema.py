"""
Contract test for User Story 1: Sequence Feature Extraction.

This test verifies that the output CSV schema matches the `SequenceFeatureSet`
definition defined in `specs/001-gene-regulation/contracts/dataset.schema.yaml`.

It ensures:
1. The schema file exists and is valid YAML.
2. The schema defines the required structure for sequence features.
3. The schema explicitly excludes 'at_content' (due to collinearity with GC-Content).
4. The schema allows for dynamic feature names as defined in data-model.md.
5. The schema enforces numeric types for feature values.
"""

import os
import yaml
import pytest
from pathlib import Path

# Import schema loading utility from the project's utils
from utils.schema_validator import load_schema, ensure_schema_exists
from utils.logging import get_logger, PipelineError

logger = get_logger(__name__)

SCHEMA_PATH = Path("specs/001-gene-regulation/contracts/dataset.schema.yaml")
EXPECTED_FEATURE_COUNT = 15
EXCLUDED_FEATURES = ["at_content"]

def test_schema_file_exists():
    """Verify that the dataset schema file exists."""
    assert SCHEMA_PATH.exists(), f"Schema file not found at {SCHEMA_PATH}"

def test_schema_is_valid_yaml():
    """Verify that the schema file contains valid YAML."""
    try:
        with open(SCHEMA_PATH, 'r') as f:
            schema = yaml.safe_load(f)
        assert schema is not None, "Schema file is empty or invalid YAML"
    except yaml.YAMLError as e:
        pytest.fail(f"Schema file contains invalid YAML: {e}")

def test_schema_structure_matches_sequence_feature_set():
    """
    Verify the schema structure matches the expected `SequenceFeatureSet` definition.
    
    The schema should define:
    - A root object with 'properties'
    - A 'task_id' field (string)
    - A set of numeric feature fields
    - Proper type definitions
    """
    schema = load_schema(SCHEMA_PATH)
    
    # Check root structure
    assert isinstance(schema, dict), "Schema root must be a dictionary"
    assert "properties" in schema, "Schema must have 'properties' key"
    
    properties = schema["properties"]
    assert isinstance(properties, dict), "Properties must be a dictionary"
    
    # Verify 'task_id' exists and is a string
    assert "task_id" in properties, "Schema must define 'task_id'"
    assert properties["task_id"].get("type") == "string", "task_id must be type string"

def test_schema_excludes_at_content():
    """
    Verify that 'at_content' is explicitly excluded from the schema.
    
    According to Plan.md (Constitution Check, Principle VII), 'at_content'
    must be excluded due to perfect collinearity with GC-Content.
    """
    schema = load_schema(SCHEMA_PATH)
    properties = schema.get("properties", {})
    
    for excluded_feature in EXCLUDED_FEATURES:
        assert excluded_feature not in properties, (
            f"Schema must NOT include '{excluded_feature}' due to collinearity with GC-Content"
        )

def test_schema_allows_dynamic_feature_names():
    """
    Verify the schema allows for dynamic feature names.
    
    The schema should not hardcode specific feature names (other than task_id)
    but rather define a pattern or allow for a flexible set of numeric fields
    as defined in data-model.md.
    """
    schema = load_schema(SCHEMA_PATH)
    properties = schema.get("properties", {})
    
    # We expect at least task_id plus the feature fields
    # The exact feature names should come from data-model.md, not be hardcoded here
    # We check that we have numeric fields defined
    numeric_fields = [
        k for k, v in properties.items() 
        if k != "task_id" and v.get("type") in ["number", "integer", "float"]
    ]
    
    assert len(numeric_fields) >= 1, (
        "Schema must define at least one numeric feature field (excluding task_id)"
    )
    
    # Verify that 'at_content' is not among the numeric fields
    assert "at_content" not in numeric_fields, (
        "at_content must not be in the numeric feature fields"
    )

def test_schema_validates_numeric_types():
    """
    Verify that feature values are defined as numeric types.
    """
    schema = load_schema(SCHEMA_PATH)
    properties = schema.get("properties", {})
    
    for field_name, field_def in properties.items():
        if field_name == "task_id":
            assert field_def.get("type") == "string", "task_id must be string"
        else:
            # All other fields (features) should be numeric
            field_type = field_def.get("type")
            assert field_type in ["number", "integer", "float"], (
                f"Feature field '{field_name}' must be numeric, got '{field_type}'"
            )

def test_schema_has_required_fields():
    """
    Verify that the schema defines required fields.
    """
    schema = load_schema(SCHEMA_PATH)
    
    assert "required" in schema, "Schema must define 'required' fields"
    required_fields = schema["required"]
    assert isinstance(required_fields, list), "'required' must be a list"
    assert "task_id" in required_fields, "'task_id' must be in required fields"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])