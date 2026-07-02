"""
Contract tests for model_output schema validation.
Verifies that model output artifacts conform to specs/001-predict-sn1-rate-constants/contracts/model_output.schema.yaml
"""
import os
import yaml
import pytest
from pathlib import Path
from jsonschema import validate, ValidationError

PROJECT_ROOT = Path(__file__).parent.parent.parent
SCHEMA_PATH = PROJECT_ROOT / "specs" / "001-predict-sn1-rate-constants" / "contracts" / "model_output.schema.yaml"

@pytest.fixture
def schema():
    with open(SCHEMA_PATH, 'r') as f:
        return yaml.safe_load(f)

@pytest.fixture
def valid_model_output():
    return {
        "model_id": "mpnn-v1",
        "hyperparameters": {
            "hidden_dim": 64,
            "num_layers": 3
        },
        "metrics": {
            "r2": 0.85,
            "mae": 0.05
        },
        "weights_path": "artifacts/best_model.pt"
    }

def test_schema_exists():
    assert SCHEMA_PATH.exists(), f"Schema file not found at {SCHEMA_PATH}"

def test_valid_output_conforms(schema, valid_model_output):
    try:
        validate(instance=valid_model_output, schema=schema)
    except ValidationError as e:
        pytest.fail(f"Valid output failed schema validation: {e.message}")

def test_missing_metrics_raises(schema):
    invalid_output = {
        "model_id": "mpnn-v1",
        # Missing metrics
        "weights_path": "artifacts/best_model.pt"
    }
    with pytest.raises(ValidationError):
        validate(instance=invalid_output, schema=schema)

def test_missing_r2_in_metrics_raises(schema):
    invalid_output = {
        "model_id": "mpnn-v1",
        "metrics": {
            "mae": 0.05
            # Missing r2
        },
        "weights_path": "artifacts/best_model.pt"
    }
    with pytest.raises(ValidationError):
        validate(instance=invalid_output, schema=schema)
