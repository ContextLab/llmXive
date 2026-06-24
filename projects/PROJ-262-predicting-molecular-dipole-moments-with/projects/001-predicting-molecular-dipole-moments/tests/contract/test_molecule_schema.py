"""
Contract test for the molecule schema.

This test ensures that the YAML schema file defining the expected
structure of a molecule record is syntactically valid and conforms to
JSON‑Schema Draft‑7 rules. It does **not** validate actual molecule
instances – those are covered by integration/unit tests elsewhere.
"""

import pathlib
import yaml

import pytest

def _load_schema() -> dict:
    """Load the molecule schema YAML file."""
    schema_path = (
        pathlib.Path(__file__).parent.parent
        / "contracts"
        / "molecule.schema.yaml"
    )
    if not schema_path.is_file():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    with schema_path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def test_molecule_schema_is_valid():
    """Validate that the molecule schema is a well‑formed JSON Schema."""
    schema = _load_schema()
    # Basic sanity check – the schema must be a mapping.
    assert isinstance(schema, dict), "Schema should be a mapping (dict)."

    # Try to validate the schema itself using jsonschema if available.
    try:
        from jsonschema import Draft7Validator, SchemaError
    except ImportError:  # pragma: no cover
        pytest.skip("jsonschema package not installed; schema syntax check skipped.")

    try:
        Draft7Validator.check_schema(schema)
    except SchemaError as exc:  # pragma: no cover
        pytest.fail(f"Invalid JSON Schema: {exc}")