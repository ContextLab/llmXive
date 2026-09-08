"""
Contract test ensuring that ``data/results/target_decision.json`` conforms
to the JSON schema defined in ``contracts/target_decision.schema.yaml``.
"""

import json
import pathlib
import jsonschema
import pytest

@pytest.fixture(scope="session")
def schema():
    schema_path = pathlib.Path(__file__).resolve().parents[2] / "contracts" / "target_decision.schema.yaml"
    with open(schema_path, "r", encoding="utf-8") as f:
        return json.load(f)

@pytest.fixture(scope="session")
def target_decision():
    decision_path = pathlib.Path(__file__).resolve().parents[2] / "data" / "results" / "target_decision.json"
    with open(decision_path, "r", encoding="utf-8") as f:
        return json.load(f)

def test_target_decision_schema(target_decision, schema):
    """Validate the generated decision JSON against its schema."""
    jsonschema.validate(instance=target_decision, schema=schema)