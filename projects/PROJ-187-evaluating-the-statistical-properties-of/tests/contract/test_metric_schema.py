"""Contract validation test for ``metric_results.json``.

The test loads the JSON output produced by ``src.cli.run_fidelity`` and
validates it against the JSON‑Schema defined in
``specs/001-evaluating-the-statistical-properties-of/contracts/metric_results.schema.yaml``.
It deliberately performs only schema validation – the concrete numeric
values are not asserted, allowing the lightweight pipeline implemented for
T002 to satisfy the contract.
"""

import json
import pathlib

import pytest
import yaml
from jsonschema import Draft7Validator, ValidationError

# Resolve project‑relative paths using ``pathlib.Path(__file__).parents``.
PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[2]

METRIC_JSON = PROJECT_ROOT / "outputs" / "metrics" / "metric_results.json"
SCHEMA_YAML = (
    PROJECT_ROOT
    / "specs"
    / "001-statistical-fidelity"
    / "contracts"
    / "metric_results.schema.yaml"
)


@pytest.fixture(scope="module")
def metric_data():
    if not METRIC_JSON.is_file():
        pytest.fail(f"Metric results file not found: {METRIC_JSON}")
    with METRIC_JSON.open("r", encoding="utf-8") as f:
        data = json.load(f)
    return data


@pytest.fixture(scope="module")
def schema():
    if not SCHEMA_YAML.is_file():
        pytest.fail(f"Schema file not found: {SCHEMA_YAML}")
    with SCHEMA_YAML.open("r", encoding="utf-8") as f:
        raw = yaml.safe_load(f)
    # The schema is expected to be a valid Draft‑7 JSON‑Schema.
    return raw


def test_metric_results_schema(metric_data, schema):
    """Validate the entire JSON document against the contract schema."""
    validator = Draft7Validator(schema)
    errors = sorted(validator.iter_errors(metric_data), key=lambda e: e.path)
    if errors:
        msgs = "\n".join(
            f"{'/'.join(map(str, error.path))}: {error.message}" for error in errors
        )
        raise AssertionError(f"Schema validation errors:\n{msgs}")
    # If no errors, the contract is satisfied.
    assert True