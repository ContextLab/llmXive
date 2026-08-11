import pytest
import yaml
from pathlib import Path
import json
from jsonschema import validate, ValidationError

PROJECT_ROOT = Path(__file__).parent.parent.parent
CONTRACTS_DIR = PROJECT_ROOT / "contracts"

def load_schema(schema_name: str):
    schema_path = CONTRACTS_DIR / f"{schema_name}.schema.yaml"
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    with open(schema_path, 'r') as f:
        return yaml.safe_load(f)

def test_rollout_log_schema():
    """
    Contract test for rollout log schema.
    Verifies that valid rollout log entries conform to the schema defined in T004a.
    """
    schema = load_schema("rollout_log")
    valid_data = [
        {
            "step": 1,
            "confidence": 0.85,
            "candidate": "A",
            "selected": "A",
            "correct": True,
            "prompt_length": 50
        }
    ]
    try:
        validate(instance=valid_data, schema=schema)
        assert True
    except ValidationError as e:
        pytest.fail(f"Schema validation failed: {e}")

def test_run_metadata_schema():
    """
    Contract test for run metadata schema.
    Verifies that run metadata entries conform to the schema defined in T004b.
    """
    schema = load_schema("run_metadata")
    valid_data = {
        "run_id": "test-001",
        "seed": 42,
        "timestamp": "2023-10-01T12:00:00Z",
        "config": {"mode": "baseline", "buffer_cycles": 100}
    }
    try:
        validate(instance=valid_data, schema=schema)
        assert True
    except ValidationError as e:
        pytest.fail(f"Schema validation failed: {e}")

def test_aggregated_metrics_schema():
    """
    Contract test for aggregated metrics schema.
    Verifies that aggregated metrics entries conform to the schema defined in T004c.
    """
    schema = load_schema("aggregated_metrics")
    valid_data = [
        {
            "run_id": "test-001",
            "aucc": 0.75,
            "final_accuracy": 0.82,
            "prompt_length": 45,
            "std_dev": 0.05
        }
    ]
    try:
        validate(instance=valid_data, schema=schema)
        assert True
    except ValidationError as e:
        pytest.fail(f"Schema validation failed: {e}")

def test_convergence_result_schema():
    """
    Contract test for convergence result schema.
    Verifies that convergence result entries conform to the schema defined in T004d.
    """
    schema = load_schema("convergence_result")
    valid_data = {
        "converged": True,
        "cycles_to_converge": 50,
        "final_accuracy": 0.82,
        "accuracy_curve": [0.5, 0.6, 0.7, 0.75, 0.8]
    }
    try:
        validate(instance=valid_data, schema=schema)
        assert True
    except ValidationError as e:
        pytest.fail(f"Schema validation failed: {e}")