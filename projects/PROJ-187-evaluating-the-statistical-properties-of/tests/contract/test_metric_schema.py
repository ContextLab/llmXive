"""Contract validation test for ``metric_results.json``."""
import json
import pathlib

import pytest
import yaml
from jsonschema import Draft7Validator

PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[2]

SMOKE_JSON = PROJECT_ROOT / "outputs" / "metrics" / "metric_results_smoke.json"
FULL_JSON = PROJECT_ROOT / "outputs" / "metrics" / "metric_results.json"
SCHEMA_YAML = (
    PROJECT_ROOT
    / "specs"
    / "001-statistical-fidelity"
    / "contracts"
    / "metric_results.schema.yaml"
)

@pytest.fixture(scope="module")
def metric_data():
    target = SMOKE_JSON if SMOKE_JSON.is_file() else FULL_JSON
    if not target.is_file():
        pytest.fail(f"No metric results file found at {SMOKE_JSON} or {FULL_JSON}")
    with target.open("r", encoding="utf-8") as f:
        return json.load(f)

@pytest.fixture(scope="module")
def schema():
    if not SCHEMA_YAML.is_file():
        pytest.fail(f"Schema file not found: {SCHEMA_YAML}")
    with SCHEMA_YAML.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def test_metric_results_schema(metric_data, schema):
    validator = Draft7Validator(schema)
    errors = sorted(validator.iter_errors(metric_data), key=lambda e: e.path)
    if errors:
        msgs = "\n".join(
            f"{'/'.join(map(str, error.path))}: {error.message}" for error in errors
        )
        raise AssertionError(f"Schema validation errors:\n{msgs}")
    assert True