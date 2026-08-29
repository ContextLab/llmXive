"""
Unit tests for dataset schema validation (T006).
Validates that the schema file is loadable and correctly describes the expected CSV structure.
"""
import yaml
import pytest
from pathlib import Path
import sys
import os

# Add code directory to path to import validation utilities if needed, 
# though this test focuses on the schema definition itself.
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

SCHEMA_PATH = Path(__file__).parent.parent / "specs" / "001-visual-attention-recall" / "contracts" / "dataset.schema.yaml"

@pytest.fixture
def schema():
    if not SCHEMA_PATH.exists():
        pytest.fail(f"Schema file not found at {SCHEMA_PATH}. T006 artifact missing.")
    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def test_schema_file_exists():
    """Assert the schema file exists on disk."""
    assert SCHEMA_PATH.exists(), "dataset.schema.yaml must exist in contracts directory."

def test_schema_loadable(schema):
    """Assert the YAML is valid and loadable."""
    assert schema is not None
    assert "columns" in schema
    assert "entity" in schema

def test_required_columns_present(schema):
    """Assert all critical columns for analysis are defined."""
    column_names = [col["name"] for col in schema["columns"]]
    
    required_fields = [
        "participant_id", "stai_total", "stai_group",
        "stimulus_id", "valence",
        "recall_correct", "fixation_duration_ms", "stimulus_duration_ms"
    ]
    
    missing = set(required_fields) - set(column_names)
    assert not missing, f"Missing required columns in schema: {missing}"

def test_schema_constraints_valid(schema):
    """Assert that defined constraints have valid logic."""
    for col in schema["columns"]:
        if "constraints" in col:
            # Check for basic constraint types
            allowed_types = ["not_null", "min", "max", "allowed_values", "pattern"]
            for key in col["constraints"]:
                assert key in allowed_types, f"Unknown constraint type '{key}' in column {col['name']}"

def test_entity_definition(schema):
    """Assert the root entity is defined as Trial."""
    assert schema.get("entity") == "Trial", "Root entity must be 'Trial' for analysis-ready CSV."

def test_schema_version(schema):
    """Assert schema has a version."""
    assert "schema_version" in schema
    assert schema["schema_version"] != "1.0.0", "Schema version should be updated if schema changes."

def test_validation_rules_defined(schema):
    """Assert that cross-column validation rules are present."""
    assert "validation_rules" in schema
    assert len(schema["validation_rules"]) > 0

def test_target_file_path(schema):
    """Assert the target file path matches project convention."""
    assert schema.get("target_file") == "data/processed/analysis.csv"