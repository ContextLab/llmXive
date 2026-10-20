"""
Contract‑validation test suite for T001.

This suite checks three things required by the task:
  1. The validator can successfully validate a *valid* JSON object against each
     of the four schemas and raises a ``jsonschema.exceptions.ValidationError``
     for an *invalid* object.
  2. Requesting validation for an unknown schema name raises ``ValueError``.
  3. The global configuration random seed is an integer and matches the seed
     stored in ``config/sweep_config.yaml``.

The tests construct minimal JSON objects dynamically based on the actual
``required`` field list in each schema, so they remain robust even if the
schema definitions evolve.
"""

import json
import pathlib

import pytest
import yaml

from orchestrator import contract_validator
from orchestrator.contract_validator import validate_schema, load_schema_from_yaml
from orchestrator.config import get_config


@pytest.mark.parametrize(
    "schema_file",
    [
        "physical-node.schema.yaml",
        "dropout-event.schema.yaml",
        "execution-run.schema.yaml",
        "regression-model.schema.yaml",
    ],
)
def test_valid_and_invalid_objects(schema_file):
    """
    Build a minimal valid object using the schema's ``required`` fields,
    then verify that validation succeeds. Remove one required field and
    assert that validation fails with a ``jsonschema.ValidationError``.
    """
    # Load the schema from the specs directory
    schema_path = pathlib.Path(__file__).parents[3] / "specs" / "001-build-a-mesh-network-that-forms-the-larg" / "contracts" / schema_file
    schema = load_schema_from_yaml(schema_path)

    # Helper to generate a dummy value for a given JSON‑Schema type
    def dummy_for(prop_schema):
        typ = prop_schema.get("type", "string")
        if typ == "string":
            return "example"
        if typ in ("number", "integer"):
            return 0
        if typ == "boolean":
            return False
        if typ == "array":
            return []
        if typ == "object":
            return {}
        return None

    # Construct a minimal valid instance
    valid_instance = {}
    for prop in schema.get("required", []):
        prop_schema = schema["properties"].get(prop, {})
        valid_instance[prop] = dummy_for(prop_schema)

    # Validation must succeed for the valid instance
    assert validate_schema(valid_instance, schema_file)

    # Build an invalid instance by omitting the first required property
    if schema.get("required"):
        invalid_instance = valid_instance.copy()
        invalid_instance.pop(schema["required"][0])
        with pytest.raises(Exception) as exc:
            validate_schema(invalid_instance, schema_file)
        # The specific exception type is jsonschema.ValidationError, but we
        # avoid importing jsonschema directly to keep the test lightweight.
        assert "ValidationError" in str(exc.type)


def test_unknown_schema_raises():
    """
    The validator should raise ``ValueError`` when an unknown schema name
    (or file) is requested.
    """
    unknown_name = "nonexistent.schema.yaml"
    with pytest.raises(ValueError):
        validate_schema({"any": "data"}, unknown_name)


def test_random_seed_is_integer_and_matches_sweep_config():
    """
    Ensure that the global random seed defined in ``orchestrator.config``
    is an integer and that the same value appears in the sweep config
    YAML file.
    """
    cfg = get_config()
    assert isinstance(cfg.random_seed, int), "random_seed must be an integer"

    sweep_path = pathlib.Path(__file__).parents[3] / "config" / "sweep_config.yaml"
    with sweep_path.open("rt", encoding="utf-8") as f:
        sweep_cfg = yaml.safe_load(f)

    assert sweep_cfg.get("random_seed") == cfg.random_seed, (
        "random_seed in sweep_config.yaml must mirror the value from config.py"
    )
