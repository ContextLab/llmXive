"""
Contract test for ThermalSample schema (T007b).
Validates that data produced by simulation modules conforms to contracts/thermal_sample.schema.yaml.
"""
import json
import pytest
from pathlib import Path
import yaml
from jsonschema import validate, ValidationError
from jsonschema.exceptions import ValidationError as SchemaValidationError

# Import the loader utility from the project's ingest validators to ensure consistency
# or implement a local loader if not available.
# Based on existing API: from ingest.validators import load_schema, validate_data
# We will implement a local loader here to avoid circular imports or missing dependencies
# if the task T007b is run in isolation before T007a/c are fully integrated.

SCHEMA_PATH = Path("contracts/thermal_sample.schema.yaml")

def load_schema(schema_path: Path) -> dict:
    """Load a JSON/YAML schema from disk."""
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    with open(schema_path, "r") as f:
        if schema_path.suffix in (".yaml", ".yml"):
            return yaml.safe_load(f)
        else:
            return json.load(f)

def test_schema_file_exists():
    """Verify the schema file exists."""
    assert SCHEMA_PATH.exists(), f"Schema file {SCHEMA_PATH} is missing."

def test_schema_loads_valid_json():
    """Verify the schema is valid JSON/YAML."""
    schema = load_schema(SCHEMA_PATH)
    assert isinstance(schema, dict)
    assert schema.get("$schema") is not None
    assert schema.get("type") == "object"

def test_valid_thermal_sample():
    """Test a valid ThermalSample instance against the schema."""
    schema = load_schema(SCHEMA_PATH)
    
    valid_instance = {
        "graph_id": "sample_001",
        "conductivity": 1.45,
        "converged": True,
        "metadata": {
            "simulation_time_ps": 50.0,
            "temperature_K": 300.0,
            "potential": "Stillinger-Weber",
            "cores": 2,
            "hcacf_relative_change": 0.005,
            "voronoi_volume_mean": 20.1,
            "impurity_fraction": 0.0
        }
    }
    
    # This should not raise
    validate(instance=valid_instance, schema=schema)

def test_minimal_valid_thermal_sample():
    """Test a minimal valid instance (without optional fields)."""
    schema = load_schema(SCHEMA_PATH)
    
    minimal_instance = {
        "graph_id": "sample_002",
        "conductivity": 1.42,
        "converged": True,
        "metadata": {
            "simulation_time_ps": 20.0,
            "temperature_K": 300.0,
            "potential": "Stillinger-Weber",
            "cores": 2,
            "hcacf_relative_change": 0.008
        }
    }
    
    validate(instance=minimal_instance, schema=schema)

def test_invalid_missing_conductivity():
    """Test that missing required field raises error."""
    schema = load_schema(SCHEMA_PATH)
    
    invalid_instance = {
        "graph_id": "sample_003",
        "converged": True,
        "metadata": {
            "simulation_time_ps": 20.0,
            "temperature_K": 300.0,
            "potential": "Stillinger-Weber",
            "cores": 2,
            "hcacf_relative_change": 0.008
        }
    }
    
    with pytest.raises(SchemaValidationError):
        validate(instance=invalid_instance, schema=schema)

def test_invalid_conductivity_type():
    """Test that wrong type for conductivity raises error."""
    schema = load_schema(SCHEMA_PATH)
    
    invalid_instance = {
        "graph_id": "sample_004",
        "conductivity": "not_a_number",
        "converged": True,
        "metadata": {
            "simulation_time_ps": 20.0,
            "temperature_K": 300.0,
            "potential": "Stillinger-Weber",
            "cores": 2,
            "hcacf_relative_change": 0.008
        }
    }
    
    with pytest.raises(SchemaValidationError):
        validate(instance=invalid_instance, schema=schema)

def test_invalid_converged_type():
    """Test that wrong type for converged raises error."""
    schema = load_schema(SCHEMA_PATH)
    
    invalid_instance = {
        "graph_id": "sample_005",
        "conductivity": 1.45,
        "converged": "yes",
        "metadata": {
            "simulation_time_ps": 20.0,
            "temperature_K": 300.0,
            "potential": "Stillinger-Weber",
            "cores": 2,
            "hcacf_relative_change": 0.008
        }
    }
    
    with pytest.raises(SchemaValidationError):
        validate(instance=invalid_instance, schema=schema)