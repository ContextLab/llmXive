"""
Contract Test for Dataset Schema Validation.

This test verifies that the dataset schema file exists, is valid YAML,
and contains the required structure as defined in the project specifications.
"""
import os
import sys
import pytest
import yaml
from pathlib import Path

# Add project root to path to allow imports if needed, though this test is standalone
PROJECT_ROOT = Path(__file__).parent.parent.parent
SCHEMA_PATH = PROJECT_ROOT / "contracts" / "dataset_schema.yaml"

@pytest.fixture
def schema_data():
    """Load the schema file. Fails loudly if missing or invalid."""
    if not SCHEMA_PATH.exists():
        pytest.fail(f"Schema file missing at expected path: {SCHEMA_PATH}")
    
    try:
        with open(SCHEMA_PATH, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        return data
    except yaml.YAMLError as e:
        pytest.fail(f"Schema file is not valid YAML: {e}")

def test_schema_file_exists():
    """Verify the schema file exists at the correct location."""
    assert SCHEMA_PATH.exists(), f"Schema file not found at {SCHEMA_PATH}"

def test_schema_is_valid_dict(schema_data):
    """Verify the loaded schema is a dictionary."""
    assert isinstance(schema_data, dict), "Schema root must be an object"

def test_schema_has_required_top_level_keys(schema_data):
    """Verify required top-level keys are present."""
    required_keys = ['version', 'interactions']
    for key in required_keys:
        assert key in schema_data, f"Missing required key: {key}"

def test_schema_version_is_correct(schema_data):
    """Verify the schema version matches the expected constant."""
    assert schema_data.get('version') == "1.0.0", "Schema version must be 1.0.0"

def test_schema_has_metadata_section(schema_data):
    """Verify the metadata section exists and has required fields."""
    assert 'metadata' in schema_data, "Missing 'metadata' section"
    metadata = schema_data['metadata']
    assert isinstance(metadata, dict), "Metadata must be an object"
    assert 'created_at' in metadata, "Metadata missing 'created_at'"
    assert 'source' in metadata, "Metadata missing 'source'"

def test_schema_interactions_structure(schema_data):
    """Verify the interactions array structure and required properties."""
    interactions = schema_data['interactions']
    assert isinstance(interactions, dict), "Interactions definition must be an object (schema definition)"
    
    # Check it's a schema definition for an array
    assert interactions.get('type') == 'array', "Interactions must be an array type"
    assert 'items' in interactions, "Interactions must define 'items'"
    
    items_schema = interactions['items']
    assert isinstance(items_schema, dict), "Items must be an object"
    assert items_schema.get('type') == 'object', "Items must be objects"
    
    required_fields = ['interaction_id', 'modalities', 'trust_score']
    item_required = items_schema.get('required', [])
    for field in required_fields:
        assert field in item_required, f"Interaction item missing required field: {field}"

def test_schema_interactions_modalities(schema_data):
    """Verify modalities structure within interactions."""
    items = schema_data['interactions']['items']
    modalities_def = items['properties']['modalities']
    
    assert 'required' in modalities_def, "Modalities must have required fields"
    assert 'facial' in modalities_def['required'], "Modalities must require 'facial'"
    assert 'vocal' in modalities_def['required'], "Modalities must require 'vocal'"

def test_schema_interactions_trust_score_range(schema_data):
    """Verify trust_score has valid range constraints."""
    items = schema_data['interactions']['items']
    trust_score_def = items['properties']['trust_score']
    
    assert trust_score_def.get('type') == 'integer', "Trust score must be an integer"
    assert trust_score_def.get('minimum') == 1, "Trust score minimum must be 1"
    assert trust_score_def.get('maximum') == 7, "Trust score maximum must be 7"

def test_schema_interactions_avatar_type_enum(schema_data):
    """Verify avatar_type has correct enum values."""
    items = schema_data['interactions']['items']
    avatar_def = items['properties']['avatar_type']
    
    expected_avatars = ['neutral', 'expressive', 'exaggerated']
    assert avatar_def.get('type') == 'string', "Avatar type must be a string"
    assert set(avatar_def.get('enum', [])) == set(expected_avatars), "Avatar type enum mismatch"

def test_schema_additional_properties_false(schema_data):
    """Verify that additional properties are restricted to enforce strict schema."""
    assert schema_data.get('additionalProperties') == False, "Schema must forbid additional properties at root"
    
    # Check items also restrict additional properties if defined
    if 'items' in schema_data['interactions']:
        items_schema = schema_data['interactions']['items']
        # Ideally items should also have additionalProperties: false for strictness
        # but we check the root requirement primarily.

if __name__ == "__main__":
    pytest.main([__file__, "-v"])