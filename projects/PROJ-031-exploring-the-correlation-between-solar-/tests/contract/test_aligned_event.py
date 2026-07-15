"""
Contract test for aligned_events.csv schema validation.

This test verifies that the aligned events data conforms to the
schema defined in contracts/aligned_event.schema.yaml.
"""
import os
import json
import tempfile
from pathlib import Path

import pytest
import yaml
from jsonschema import validate, ValidationError, SchemaError

# Project root is two levels up from tests/contract/
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
CONTRACTS_DIR = PROJECT_ROOT / "contracts"
SCHEMA_PATH = CONTRACTS_DIR / "aligned_event.schema.yaml"

# Mock fixture data representing a valid row in aligned_events.csv
# This simulates what would be loaded from the CSV after processing
VALID_ALIGNED_EVENT_FIXTURE = {
    "storm_id": "STORM_20230115_001",
    "storm_timestamp": "2023-01-15T12:00:00Z",
    "dst_min": -150.5,
    "dst_min_timestamp": "2023-01-15T06:00:00Z",
    "flare_id": "FLARE_20230112_001",
    "flare_timestamp": "2023-01-12T08:30:00Z",
    "flare_class": "X2.1",
    "flare_flux": 2.1e-4,
    "cme_id": "CME_20230112_001",
    "cme_speed": 1200,
    "cme_width": 180,
    "cme_direction": "180",
    "time_diff_days": 2.75,
    "is_recurrent": False,
    "missing_flare": False,
    "missing_cme": False,
    "source_flare": "GOES",
    "source_cme": "LASCO"
}

@pytest.fixture
def schema():
    """Load the aligned_event schema from the contracts directory."""
    if not SCHEMA_PATH.exists():
        raise FileNotFoundError(f"Schema file not found at {SCHEMA_PATH}. "
                                "Ensure T004 has been completed.")
    with open(SCHEMA_PATH, 'r') as f:
        try:
            return yaml.safe_load(f)
        except yaml.YAMLError as e:
            pytest.fail(f"Failed to parse schema YAML: {e}")

@pytest.fixture
def valid_data():
    """Return the valid mock fixture data."""
    return VALID_ALIGNED_EVENT_FIXTURE

def test_aligned_event_schema_valid(schema, valid_data):
    """
    Contract test: Verify that valid aligned event data passes schema validation.
    
    Asserts that the mock fixture data (representing a valid row from aligned_events.csv)
    conforms to the schema defined in contracts/aligned_event.schema.yaml.
    """
    try:
        validate(instance=valid_data, schema=schema)
    except ValidationError as e:
        pytest.fail(f"Valid fixture data failed schema validation: {e.message}")
    except SchemaError as e:
        pytest.fail(f"Schema itself is invalid: {e.message}")

def test_aligned_event_schema_invalid_type(schema):
    """
    Contract test: Verify that invalid data (wrong types) fails validation.
    
    This ensures the schema actually rejects incorrect data types.
    """
    invalid_data = valid_data_copy(schema, valid_data)
    # Introduce a type error: make a numeric field a string
    invalid_data["dst_min"] = "not_a_number"
    
    with pytest.raises(ValidationError):
        validate(instance=invalid_data, schema=schema)

def valid_data_copy(schema, original):
    """Helper to create a deep copy of the fixture data."""
    import copy
    return copy.deepcopy(original)
