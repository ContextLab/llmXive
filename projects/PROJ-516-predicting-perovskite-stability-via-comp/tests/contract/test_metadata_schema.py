"""
Contract test for metadata.schema.yaml.
Validates that generated metadata adheres to the instrumentation schema.
"""
import json
import jsonschema
import pytest
from pathlib import Path
import sys

# Add code directory to path for imports if needed, though this is a contract test
# against a static schema file.
PROJECT_ROOT = Path(__file__).parent.parent.parent
SCHEMA_PATH = PROJECT_ROOT / "contracts" / "metadata.schema.yaml"

import yaml

@pytest.fixture
def schema():
    if not SCHEMA_PATH.exists():
        pytest.fail(f"Schema file not found at {SCHEMA_PATH}")
    with open(SCHEMA_PATH, "r") as f:
        return yaml.safe_load(f)

@pytest.fixture
def valid_metadata_entry():
    return {
        "perovskite_id": "CsPbI3",
        "tga_model": "TA Instruments Q500",
        "uncertainty_value": 5.0,
        "uncertainty_unit": "Celsius",
        "uncertainty_source": "instrument_spec",
        "is_default_uncertainty": False,
        "notes": "High precision run"
    }

@pytest.fixture
def default_uncertainty_entry():
    return {
        "perovskite_id": "MAPbBr3",
        "tga_model": "Unknown Model",
        "uncertainty_value": 10.0,
        "uncertainty_unit": "Celsius",
        "uncertainty_source": "default_bound",
        "is_default_uncertainty": True
    }

def test_schema_is_valid_json(schema):
    """Ensure the schema itself is valid JSON/YAML structure."""
    assert isinstance(schema, dict)
    assert "$schema" in schema
    assert "properties" in schema
    assert "required" in schema

def test_valid_entry_passes(schema, valid_metadata_entry):
    """Test that a valid metadata entry conforms to the schema."""
    jsonschema.validate(instance=valid_metadata_entry, schema=schema)

def test_default_uncertainty_entry_passes(schema, default_uncertainty_entry):
    """Test that a default uncertainty entry conforms to the schema."""
    jsonschema.validate(instance=default_uncertainty_entry, schema=schema)

def test_missing_required_field_fails(schema, valid_metadata_entry):
    """Test that missing a required field raises validation error."""
    del valid_metadata_entry["tga_model"]
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(instance=valid_metadata_entry, schema=schema)

def test_invalid_uncertainty_source_fails(schema, valid_metadata_entry):
    """Test that an invalid uncertainty_source value raises error."""
    valid_metadata_entry["uncertainty_source"] = "invalid_source"
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(instance=valid_metadata_entry, schema=schema)

def test_negative_uncertainty_fails(schema, valid_metadata_entry):
    """Test that negative uncertainty value raises error."""
    valid_metadata_entry["uncertainty_value"] = -5.0
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(instance=valid_metadata_entry, schema=schema)

def test_wrong_unit_fails(schema, valid_metadata_entry):
    """Test that an invalid unit raises error."""
    valid_metadata_entry["uncertainty_unit"] = "Fahrenheit"
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(instance=valid_metadata_entry, schema=schema)