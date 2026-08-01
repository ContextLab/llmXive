import pathlib
import yaml
import jsonschema
import pytest

# Path to the contract schema
SCHEMA_PATH = pathlib.Path(__file__).resolve().parents[2] / "contracts" / "transport_schema.schema.yaml"

@pytest.fixture(scope="module")
def schema():
    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def test_transport_schema_validation(schema):
    """Validate a sample TransportResult instance against the JSON schema."""
    sample_instance = {
        "network_id": "net_001",
        "kappa": 1.23,
        "error_estimate": 0.04,
        "convergence_status": "converged",
        "runtime": 1250.0,
        "regime_flag": "diffusive",
    }
    # jsonschema.validate will raise ValidationError if the instance does not match
    jsonschema.validate(instance=sample_instance, schema=schema)
