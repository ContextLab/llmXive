import json
import pytest
from jsonschema import validate, ValidationError
from pathlib import Path

# Load schema
SCHEMA_PATH = Path(__file__).parent.parent.parent / "contracts" / "sample.schema.yaml"

def load_yaml_schema(path):
    """Simple YAML loader for the schema file."""
    with open(path, 'r') as f:
        content = f.read()
    # Basic manual parser for the specific YAML structure to avoid heavy deps
    # In production, use pyyaml, but for this specific file we can parse minimally
    # or assume pyyaml is available as per T002 requirements.
    try:
        import yaml
        return yaml.safe_load(content)
    except ImportError:
        pytest.skip("PyYAML not installed")

schema = load_yaml_schema(SCHEMA_PATH)

def test_valid_sample():
    valid_data = {
        "sample_id": "S0001",
        "plant_species": "Zea mays",
        "gps_latitude": 40.7128,
        "gps_longitude": -74.0060,
        "soil_type": "loam",
        "sequencing_depth": 50000,
        "collection_date": "2023-05-15"
    }
    validate(instance=valid_data, schema=schema)

def test_invalid_sample_missing_required():
    invalid_data = {
        "sample_id": "S0001",
        "plant_species": "Zea mays"
    }
    with pytest.raises(ValidationError):
        validate(instance=invalid_data, schema=schema)

def test_invalid_sample_bad_lat():
    invalid_data = {
        "sample_id": "S0001",
        "plant_species": "Zea mays",
        "gps_latitude": 100.0,
        "gps_longitude": -74.0060,
        "soil_type": "loam",
        "sequencing_depth": 50000
    }
    with pytest.raises(ValidationError):
        validate(instance=invalid_data, schema=schema)

def test_invalid_sample_bad_id_format():
    invalid_data = {
        "sample_id": "BAD-ID",
        "plant_species": "Zea mays",
        "gps_latitude": 40.0,
        "gps_longitude": -74.0,
        "soil_type": "loam",
        "sequencing_depth": 50000
    }
    with pytest.raises(ValidationError):
        validate(instance=invalid_data, schema=schema)
