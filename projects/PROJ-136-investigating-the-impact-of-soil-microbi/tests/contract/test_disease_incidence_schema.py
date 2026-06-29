import json
import pytest
from jsonschema import validate, ValidationError
from pathlib import Path

# Load schema
SCHEMA_PATH = Path(__file__).parent.parent.parent / "contracts" / "disease-incidence.schema.yaml"

def load_yaml_schema(path):
    """Simple YAML loader for the schema file."""
    with open(path, 'r') as f:
        content = f.read()
    try:
        import yaml
        return yaml.safe_load(content)
    except ImportError:
        pytest.skip("PyYAML not installed")

schema = load_yaml_schema(SCHEMA_PATH)

def test_valid_disease_record():
    valid_data = {
        "record_id": "D0001",
        "sample_id": "S0001",
        "disease_type": "Fusarium wilt",
        "incidence_rate": 0.15,
        "measurement_date": "2023-05-20"
    }
    validate(instance=valid_data, schema=schema)

def test_invalid_disease_missing_required():
    invalid_data = {
        "record_id": "D0001",
        "disease_type": "Fusarium wilt"
    }
    with pytest.raises(ValidationError):
        validate(instance=invalid_data, schema=schema)

def test_invalid_disease_rate_out_of_bounds():
    invalid_data = {
        "record_id": "D0001",
        "sample_id": "S0001",
        "disease_type": "Fusarium wilt",
        "incidence_rate": 1.5,
        "measurement_date": "2023-05-20"
    }
    with pytest.raises(ValidationError):
        validate(instance=invalid_data, schema=schema)
