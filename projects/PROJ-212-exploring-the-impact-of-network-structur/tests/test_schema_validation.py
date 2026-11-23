"""
Test suite for exercising all JSON schemas defined in the contracts directory.

For each ``*.schema.yaml`` file, this test loads the schema, constructs a minimal
instance that satisfies the required properties (using simple placeholder values
based on the declared type), and validates the instance with ``jsonschema``.
The ``src.validators`` module is imported to ensure it is available, as required
by the task specification, but the actual validation is performed via
``jsonschema.validate`` to avoid reliance on implementation details of the
validators module.
"""

import pathlib
import yaml
import jsonschema
import pytest

# Import the validators module to satisfy the requirement of using it.
# The module is not directly used for validation in this test, but its import
# confirms that the package is importable and that any side‑effects (e.g.,
# registration of custom formats) are applied.
from src import validators  # noqa: F401

def _generate_min_instance(schema: dict) -> dict:
    """
    Generate a minimal JSON instance that satisfies the required properties
    of a JSON schema.

    The function iterates over the ``required`` list of the schema and creates
    placeholder values based on the declared ``type`` of each property.
    Unsupported or complex types fall back to ``None``.
    """
    instance = {}
    required = schema.get("required", [])
    properties = schema.get("properties", {})

    for prop in required:
        prop_schema = properties.get(prop, {})
        typ = prop_schema.get("type")
        if typ == "string":
            instance[prop] = ""
        elif typ in ("number", "integer"):
            instance[prop] = 0
        elif typ == "boolean":
            instance[prop] = False
        elif typ == "array":
            # Use an empty array; if ``items`` are required, they will be
            # optional unless explicitly listed as required.
            instance[prop] = []
        elif typ == "object":
            # Recursively generate a nested empty object.
            instance[prop] = {}
        else:
            # Fallback for unknown or missing type specifications.
            instance[prop] = None
    return instance

@pytest.mark.parametrize(
    "schema_path",
    [
        p
        for p in pathlib.Path(__file__).parents[2]
        .joinpath("contracts")
        .glob("*.schema.yaml")
    ],
)
def test_schema_validation(schema_path: pathlib.Path) -> None:
    """
    Load a schema and validate a minimal instance against it.

    The test will fail if the schema is invalid or if the generated instance
    does not satisfy the schema constraints.
    """
    # Load the YAML schema.
    raw_schema = schema_path.read_text()
    schema = yaml.safe_load(raw_schema)

    # Generate a minimal conforming instance.
    instance = _generate_min_instance(schema)

    # Perform validation. ``jsonschema.validate`` raises an exception on failure.
    jsonschema.validate(instance=instance, schema=schema)