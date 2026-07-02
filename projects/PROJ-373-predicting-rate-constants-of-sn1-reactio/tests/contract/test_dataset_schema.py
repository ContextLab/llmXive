"""
Contract tests for dataset schema validation.
Verifies that data rows conform to specs/001-predict-sn1-rate-constants/contracts/dataset.schema.yaml
"""
import os
import json
import yaml
import pytest
from pathlib import Path
from jsonschema import validate, ValidationError

# Resolve paths relative to project root
PROJECT_ROOT = Path(__file__).parent.parent.parent
SCHEMA_PATH = PROJECT_ROOT / "specs" / "001-predict-sn1-rate-constants" / "contracts" / "dataset.schema.yaml"

@pytest.fixture
def schema():
    with open(SCHEMA_PATH, 'r') as f:
        return yaml.safe_load(f)

@pytest.fixture
def valid_row():
    """A minimal valid row according to the schema."""
    return {
        "smiles": "CC(C)(C)Br",
        "rate_constant": 1.5e-4,
        "substrate_class": "tertiary",
        "gasteiger_charges": [0.1, -0.2, 0.0, 0.0],
        "topological_indices": [2.5, 1.1],
        "source_id": "NIST-001"
    }

def test_schema_exists():
    assert SCHEMA_PATH.exists(), f"Schema file not found at {SCHEMA_PATH}"

def test_valid_row_conforms(schema, valid_row):
    """Test that a valid row passes validation."""
    try:
        validate(instance=valid_row, schema=schema)
    except ValidationError as e:
        pytest.fail(f"Valid row failed schema validation: {e.message}")

def test_missing_required_field_raises(schema):
    """Test that missing a required field raises ValidationError."""
    invalid_row = {
        "smiles": "CC(C)(C)Br",
        # Missing rate_constant
        "substrate_class": "tertiary"
    }
    with pytest.raises(ValidationError):
        validate(instance=invalid_row, schema=schema)

def test_invalid_substrate_class_raises(schema):
    """Test that invalid substrate_class enum value raises ValidationError."""
    invalid_row = {
        "smiles": "CC(C)(C)Br",
        "rate_constant": 1.5e-4,
        "substrate_class": "quaternary",  # Invalid enum
        "gasteiger_charges": [],
        "topological_indices": [],
        "source_id": "test"
    }
    with pytest.raises(ValidationError):
        validate(instance=invalid_row, schema=schema)

def test_wrong_type_raises(schema):
    """Test that wrong type for a field raises ValidationError."""
    invalid_row = {
        "smiles": "CC(C)(C)Br",
        "rate_constant": "not_a_number",  # Should be number
        "substrate_class": "tertiary",
        "gasteiger_charges": [],
        "topological_indices": [],
        "source_id": "test"
    }
    with pytest.raises(ValidationError):
        validate(instance=invalid_row, schema=schema)