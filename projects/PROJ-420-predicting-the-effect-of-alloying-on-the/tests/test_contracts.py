"""
Basic contract validation tests.

These tests ensure that the JSON/YAML contract files required by the
pipeline exist and are syntactically valid. They do not depend on any
external data and therefore run quickly in the CI environment.
"""

import json
import yaml
from pathlib import Path

import pytest

CONTRACTS_DIR = Path("contracts")

@pytest.mark.parametrize(
    "contract_file",
    [
        "logging_schema.yaml",
        "dataset.schema.yaml",
        "model_metrics.schema.yaml",
        "feature_importance.schema.yaml",
        "collinearity_diagnostic.schema.yaml",
    ],
)
def test_contract_file_exists_and_valid(contract_file: str):
    """Check that a contract file exists and can be parsed as YAML/JSON."""
    path = CONTRACTS_DIR / contract_file
    assert path.is_file(), f"Contract file missing: {contract_file}"

    # Try loading as YAML (covers both YAML and JSON)
    try:
        with open(path, "r") as f:
            yaml.safe_load(f)
    except Exception as exc:
        pytest.fail(f"Failed to parse contract {contract_file}: {exc}")

def test_logging_schema_matches_expected_fields():
    """Validate that the logging schema contains the required top‑level fields."""
    path = CONTRACTS_DIR / "logging_schema.yaml"
    with open(path, "r") as f:
        schema = yaml.safe_load(f)

    required_fields = {"timestamp", "level", "message", "trace_id", "module"}
    # The schema may define a "properties" dict; extract its keys
    properties = schema.get("properties", {})
    if isinstance(properties, dict):
        fields = set(properties.keys())
    else:
        fields = set()

    missing = required_fields - fields
    assert not missing, f"Logging schema missing fields: {missing}"