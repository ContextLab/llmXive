"""
Unit tests for the data_gap_report.schema.yaml schema validation.
"""
import json
import os
import tempfile
from datetime import datetime
from pathlib import Path

import pytest

# Try to import jsonschema if available, otherwise skip or mock
try:
    import jsonschema
    HAS_JSONSCHEMA = True
except ImportError:
    HAS_JSONSCHEMA = False

SCHEMA_PATH = Path(__file__).parent.parent.parent / "contracts" / "data_gap_report.schema.yaml"

def load_schema():
    """Load the YAML schema file."""
    import yaml
    with open(SCHEMA_PATH, "r") as f:
        return yaml.safe_load(f)

@pytest.mark.skipif(not HAS_JSONSCHEMA, reason="jsonschema not installed")
def test_valid_report_with_null_fallback():
    """Test a valid report where fallback_id is explicitly null."""
    schema = load_schema()
    report = {
        "dataset_id": "ds_search_task_switching",
        "reason": "No dataset found matching criteria",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "fallback_id": None
    }
    jsonschema.validate(instance=report, schema=schema)

@pytest.mark.skipif(not HAS_JSONSCHEMA, reason="jsonschema not installed")
def test_valid_report_with_fallback_id():
    """Test a valid report where fallback_id is a string."""
    schema = load_schema()
    report = {
        "dataset_id": "ds000000",
        "reason": "Dataset found but incomplete",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "fallback_id": "ds000001"
    }
    jsonschema.validate(instance=report, schema=schema)

@pytest.mark.skipif(not HAS_JSONSCHEMA, reason="jsonschema not installed")
def test_invalid_missing_required_field():
    """Test that a report missing a required field fails validation."""
    schema = load_schema()
    report = {
        "dataset_id": "ds000000",
        "reason": "Missing reason",
        "timestamp": datetime.utcnow().isoformat() + "Z"
        # fallback_id is missing
    }
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(instance=report, schema=schema)

@pytest.mark.skipif(not HAS_JSONSCHEMA, reason="jsonschema not installed")
def test_invalid_fallback_id_type():
    """Test that a fallback_id of incorrect type fails validation."""
    schema = load_schema()
    report = {
        "dataset_id": "ds000000",
        "reason": "Invalid fallback type",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "fallback_id": 12345  # Should be string or null
    }
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(instance=report, schema=schema)

@pytest.mark.skipif(not HAS_JSONSCHEMA, reason="jsonschema not installed")
def test_schema_structure():
    """Verify the schema file contains the expected keys."""
    schema = load_schema()
    assert "properties" in schema
    props = schema["properties"]
    assert "dataset_id" in props
    assert "reason" in props
    assert "timestamp" in props
    assert "fallback_id" in props
    
    # Check fallback_id allows null
    fallback_type = props["fallback_id"]["type"]
    assert "null" in fallback_type if isinstance(fallback_type, list) else fallback_type == "null" or fallback_type == ["string", "null"]