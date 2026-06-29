"""
Contract test for the model output schema.

This test ensures that the JSON/YAML schema located at
`contracts/model_output.schema.yaml` is a valid JSON Schema (Draft 7).
It does not validate concrete model output files, but guarantees that
the schema itself is well‑formed and can be used for downstream validation.
"""

import pathlib

import yaml
import jsonschema


def _load_schema() -> dict:
    """Load the model output schema from the contracts directory."""
    # The test file resides in `tests/contract/`, so we go two levels up
    # to the repository root and then into `contracts/`.
    schema_path = (
        pathlib.Path(__file__).resolve().parents[2]
        / "contracts"
        / "model_output.schema.yaml"
    )
    with open(schema_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def test_model_output_schema_is_valid():
    """Validate that the schema conforms to JSON Schema Draft‑7."""
    schema = _load_schema()
    # jsonschema provides a helper to check the schema itself.
    jsonschema.Draft7Validator.check_schema(schema)
