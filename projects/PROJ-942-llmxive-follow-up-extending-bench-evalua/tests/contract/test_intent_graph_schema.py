import json
import pathlib

import pytest
import yaml
from jsonschema import Draft7Validator
from llmxive_toolkit import paths

@pytest.fixture(scope="module")
def schema():
    schema_path = paths.path("specs", "001-llmxive-follow-up-extending-bench-evalua", "contracts", "intent_graph.schema.yaml")
    with open(schema_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def test_intent_graph_schema_validates_all_graphs(schema):
    graph_dir = paths.path("data", "derived", "intent_graphs")
    validator = Draft7Validator(schema)
    for json_file in graph_dir.rglob("*.json"):
        with open(json_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        errors = sorted(validator.iter_errors(data), key=lambda e: e.path)
        assert not errors, f"Schema validation errors in {json_file}: {errors}"