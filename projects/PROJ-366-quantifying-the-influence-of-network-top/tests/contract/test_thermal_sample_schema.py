"""
Contract tests for the ThermalSample schema (T007b).

These tests verify that:
1. The schema file loads correctly.
2. Valid thermal sample data passes validation.
3. Invalid data (missing fields, wrong types) fails validation as expected.
"""
import json
import pytest
from pathlib import Path
import yaml
import jsonschema
from jsonschema import validate, ValidationError

# Path to the schema file relative to project root
SCHEMA_PATH = Path(__file__).parent.parent.parent / "contracts" / "thermal_sample.schema.yaml"

@pytest.fixture
def schema():
    """Load the thermal_sample schema."""
    if not SCHEMA_PATH.exists():
        pytest.fail(f"Schema file not found at {SCHEMA_PATH}. "
                    "Ensure T007b has created contracts/thermal_sample.schema.yaml.")
    with open(SCHEMA_PATH, 'r') as f:
        return yaml.safe_load(f)

@pytest.fixture
def valid_sample():
    """Generate a valid ThermalSample dictionary."""
    return {
        "graph_id": "sample_01",
        "conductivity": 1.85,
        "converged": True,
        "metadata": {
            "simulation_time_ps": 200.0,
            "thermostat_type": "nose-hoover",
            "potential_file": "Si.sw",
            "temperature_K": 300.0,
            "hcacf_samples": 5000,
            "voronoi_volume_mean": 20.1,
            "impurity_fraction": 0.0
        }
    }

@pytest.fixture
def minimal_valid_sample():
    """Generate a minimal valid ThermalSample (optional metadata fields omitted)."""
    return {
        "graph_id": "sample_02",
        "conductivity": 2.10,
        "converged": False,
        "metadata": {
            "simulation_time_ps": 100.0,
            "thermostat_type": "berendsen",
            "potential_file": "Si.sw",
            "temperature_K": 500.0,
            "hcacf_samples": 2000
            # voronoi_volume_mean and impurity_fraction are nullable/optional in logic,
            # but schema requires them to be present if metadata is present? 
            # Re-reading schema: metadata properties are not required, only the top-level metadata object is.
            # Wait, schema says:
            # metadata:
            #   required: [simulation_time_ps, thermostat_type, potential_file, temperature_K]
            # So the above is valid.
        }
    }

def test_schema_loads(schema):
    """Test that the schema file is valid YAML and parses correctly."""
    assert isinstance(schema, dict)
    assert schema["$schema"] is not None
    assert schema["title"] == "ThermalSample"

def test_valid_sample_passes(schema, valid_sample):
    """Test that a fully populated valid sample passes validation."""
    try:
        validate(instance=valid_sample, schema=schema)
    except ValidationError as e:
        pytest.fail(f"Valid sample failed validation: {e.message}")

def test_minimal_valid_sample_passes(schema, minimal_valid_sample):
    """Test that a minimal valid sample passes validation."""
    try:
        validate(instance=minimal_valid_sample, schema=schema)
    except ValidationError as e:
        pytest.fail(f"Minimal valid sample failed validation: {e.message}")

def test_missing_graph_id(schema, valid_sample):
    """Test that missing required field 'graph_id' raises ValidationError."""
    del valid_sample["graph_id"]
    with pytest.raises(ValidationError):
        validate(instance=valid_sample, schema=schema)

def test_invalid_graph_id_format(schema):
    """Test that graph_id not matching pattern raises ValidationError."""
    sample = {
        "graph_id": "invalid_id_123",
        "conductivity": 1.5,
        "converged": True,
        "metadata": {
            "simulation_time_ps": 100.0,
            "thermostat_type": "nose-hoover",
            "potential_file": "Si.sw",
            "temperature_K": 300.0,
            "hcacf_samples": 1000
        }
    }
    with pytest.raises(ValidationError):
        validate(instance=sample, schema=schema)

def test_negative_conductivity(schema, valid_sample):
    """Test that negative conductivity raises ValidationError."""
    valid_sample["conductivity"] = -1.0
    with pytest.raises(ValidationError):
        validate(instance=valid_sample, schema=schema)

def test_missing_metadata_required_field(schema, valid_sample):
    """Test that missing required field in metadata raises ValidationError."""
    del valid_sample["metadata"]["temperature_K"]
    with pytest.raises(ValidationError):
        validate(instance=valid_sample, schema=schema)

def test_converged_boolean_type(schema, valid_sample):
    """Test that non-boolean converged value raises ValidationError."""
    valid_sample["converged"] = "yes"
    with pytest.raises(ValidationError):
        validate(instance=valid_sample, schema=schema)

def test_additional_properties_rejected(schema, valid_sample):
    """Test that additional properties at the root level raise ValidationError."""
    valid_sample["extra_field"] = "should_fail"
    with pytest.raises(ValidationError):
        validate(instance=valid_sample, schema=schema)