"""
Contract test for the model output schema.

This test validates that the JSON file produced by the model evaluation
step (data/results/model_comparison.json) conforms to the schema defined
in contracts/model_output.schema.yaml.
"""
import json
import pathlib

import yaml
import jsonschema

# Paths to the schema and the generated model comparison file
SCHEMA_PATH = pathlib.Path(__file__).resolve().parents[2] / "contracts" / "model_output.schema.yaml"
RESULT_PATH = pathlib.Path(__file__).resolve().parents[2] / "data" / "results" / "model_comparison.json"


def load_schema(schema_path: pathlib.Path) -> dict:
    """Load a YAML schema file."""
    with schema_path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_result(result_path: pathlib.Path) -> dict:
    """Load the JSON result produced by the model evaluation step."""
    with result_path.open("r", encoding="utf-8") as f:
        return json.load(f)


def test_model_output_schema():
    """Validate the model comparison JSON against the contract schema."""
    schema = load_schema(SCHEMA_PATH)
    result = load_result(RESULT_PATH)

    # The top‑level object must be a dict (as required by the schema)
    assert isinstance(result, dict), "Model comparison output must be a JSON object"

    # Use jsonschema to validate
    jsonschema.validate(instance=result, schema=schema)
