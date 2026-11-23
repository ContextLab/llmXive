"""
Contract validation tests for the ``utils.validation`` module.

The tests dynamically generate a minimal instance that satisfies the
required fields of each schema (based on the ``required`` keyword) and
verify that:

1. Validation succeeds for a correctly‑shaped record.
2. Validation fails when a required field is omitted.
"""

import copy
from pathlib import Path

import pytest
from jsonschema import ValidationError

# The project root is added to ``sys.path`` by the test harness, so we can
# import the utilities directly.
from utils.validation import (
    validate_cleaned_study,
    validate_effect_size,
)


def _load_schema(schema_name: str) -> dict:
    """Load a schema YAML file from the ``contracts`` directory."""
    contracts_dir = Path(__file__).resolve().parents[2] / "contracts"
    schema_path = contracts_dir / schema_name
    with schema_path.open("r", encoding="utf-8") as f:
        import yaml

        return yaml.safe_load(f)


def _dummy_value(prop_schema: dict):
    """Return a simple dummy value compatible with the given JSON‑Schema."""
    typ = prop_schema.get("type")
    if typ == "string":
        return "example"
    if typ in ("integer", "number"):
        return 0
    if typ == "boolean":
        return True
    if typ == "array":
        # Use an empty list – most schemas accept it.
        return []
    if typ == "object":
        # Recursively create a minimal object if possible.
        props = prop_schema.get("properties", {})
        required = prop_schema.get("required", [])
        return {
            k: _dummy_value(props[k]) for k in required if k in props
        }
    # Fallback for unknown/unspecified types.
    return None


def _generate_minimal_instance(schema: dict) -> dict:
    """
    Generate the smallest possible instance that satisfies the ``required``
    fields of a JSON‑Schema.  This is sufficient for our validation tests
    without needing to know the full domain‑specific details.
    """
    required = schema.get("required", [])
    properties = schema.get("properties", {})
    instance = {}
    for field in required:
        if field not in properties:
            # If the schema does not describe the field, fall back to a
            # generic placeholder.
            instance[field] = "placeholder"
            continue
        instance[field] = _dummy_value(properties[field])
    return instance


@pytest.mark.parametrize(
    "schema_name, validator",
    [
        ("cleaned_study.schema.yaml", validate_cleaned_study),
        ("effect_size.schema.yaml", validate_effect_size),
    ],
)
def test_valid_instance_passes(schema_name, validator):
    """A minimal valid instance should pass validation."""
    schema = _load_schema(schema_name)
    minimal = _generate_minimal_instance(schema)
    # The validator returns ``True`` on success.
    assert validator(minimal) is True


@pytest.mark.parametrize(
    "schema_name, validator",
    [
        ("cleaned_study.schema.yaml", validate_cleaned_study),
        ("effect_size.schema.yaml", validate_effect_size),
    ],
)
def test_missing_required_field_raises(schema_name, validator):
    """
    Removing a required field must raise ``jsonschema.ValidationError``.
    """
    schema = _load_schema(schema_name)
    minimal = _generate_minimal_instance(schema)

    # Ensure there is at least one required field to drop.
    required_fields = schema.get("required", [])
    assert required_fields, "Schema has no required fields; test is moot."

    # Remove the first required field.
    broken = copy.deepcopy(minimal)
    broken.pop(required_fields[0], None)

    with pytest.raises(ValidationError):
        validator(broken)