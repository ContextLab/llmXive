import os
import yaml
from pathlib import Path
import pytest

# Import project utilities if available, otherwise use standard paths
try:
    from config import get_contracts_dir
    from validate_schemas import load_schema
except ImportError:
    # Fallback for direct test execution without full project import
    pass


CONTRACTS_DIR = Path("specs/001-the-impact-of-text-message-tone-on-perce/contracts")

SCHEMA_FILES = [
    "stimulus.schema.yaml",
    "rating.schema.yaml",
    "analysis_ready.schema.yaml",
    "lmm_summary.schema.yaml",
    "analysis_result.schema.yaml",
]


def test_schemas_exist():
    """Verify that all required schema files exist in the contracts directory."""
    for schema_name in SCHEMA_FILES:
        schema_path = CONTRACTS_DIR / schema_name
        assert schema_path.exists(), f"Schema file missing: {schema_path}"


def test_schemas_valid_yaml():
    """Verify that all schema files are valid YAML and parseable."""
    for schema_name in SCHEMA_FILES:
        schema_path = CONTRACTS_DIR / schema_name
        with open(schema_path, "r", encoding="utf-8") as f:
            try:
                schema = yaml.safe_load(f)
                assert schema is not None, f"Schema file is empty: {schema_name}"
                assert "type" in schema, f"Schema missing 'type' field: {schema_name}"
                assert "properties" in schema, f"Schema missing 'properties' field: {schema_name}"
            except yaml.YAMLError as e:
                pytest.fail(f"Invalid YAML in {schema_name}: {e}")


def test_schemas_have_required_fields():
    """Verify that schemas define required fields."""
    required_top_level = ["type", "properties", "required"]
    
    for schema_name in SCHEMA_FILES:
        schema_path = CONTRACTS_DIR / schema_name
        with open(schema_path, "r", encoding="utf-8") as f:
            schema = yaml.safe_load(f)
            
            for field in required_top_level:
                assert field in schema, f"Schema {schema_name} missing required field: {field}"
            
            # Verify properties are not empty
            assert len(schema["properties"]) > 0, f"Schema {schema_name} has no properties"
            
            # Verify 'required' list is not empty
            assert len(schema["required"]) > 0, f"Schema {schema_name} has no required fields"


def test_stimulus_schema_structure():
    """Specific validation for stimulus schema."""
    schema_path = CONTRACTS_DIR / "stimulus.schema.yaml"
    with open(schema_path, "r", encoding="utf-8") as f:
        schema = yaml.safe_load(f)
    
    required_fields = ["id", "text", "emoji_count", "punctuation_type", "length_category", "scenario_id", "cue_intensity"]
    for field in required_fields:
        assert field in schema["properties"], f"Stimulus schema missing field: {field}"
        assert field in schema["required"], f"Stimulus schema field not in required: {field}"


def test_rating_schema_structure():
    """Specific validation for rating schema."""
    schema_path = CONTRACTS_DIR / "rating.schema.yaml"
    with open(schema_path, "r", encoding="utf-8") as f:
        schema = yaml.safe_load(f)
    
    required_fields = ["prolific_id", "stimulus_id", "relationship_type", "rating", "timestamp"]
    for field in required_fields:
        assert field in schema["properties"], f"Rating schema missing field: {field}"
        assert field in schema["required"], f"Rating schema field not in required: {field}"
    
    # Check enum values for relationship_type
    rel_type_prop = schema["properties"]["relationship_type"]
    assert "enum" in rel_type_prop, "relationship_type missing enum values"
    assert set(rel_type_prop["enum"]) == {"friend", "acquaintance"}, "Invalid relationship_type enum values"


def test_lmm_summary_schema_structure():
    """Specific validation for LMM summary schema."""
    schema_path = CONTRACTS_DIR / "lmm_summary.schema.yaml"
    with open(schema_path, "r", encoding="utf-8") as f:
        schema = yaml.safe_load(f)
    
    required_fields = ["fixed_effect", "estimate", "stderr", "z_value", "p_value"]
    for field in required_fields:
        assert field in schema["properties"], f"LMM summary schema missing field: {field}"
        assert field in schema["required"], f"LMM summary schema field not in required: {field}"
