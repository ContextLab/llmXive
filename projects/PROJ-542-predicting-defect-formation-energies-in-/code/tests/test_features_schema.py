"""
Test that the feature matrix JSON‑Schema is syntactically valid and can be
loaded without error.
"""

import pathlib
import yaml
from jsonschema import Draft7Validator, exceptions


def test_features_schema_loads():
    """
    Load the schema file and verify that it is a valid JSON‑Schema Draft‑07
    document. The test passes if no exception is raised.
    """
    schema_path = pathlib.Path(__file__).resolve().parents[2] / "contracts" / "features.schema.yaml"
    # Load YAML safely
    with schema_path.open("r", encoding="utf-8") as f:
        schema = yaml.safe_load(f)

    # Basic sanity check
    assert isinstance(schema, dict), "Schema should be a dictionary"

    # Validate the schema itself (not an instance)
    try:
        Draft7Validator.check_schema(schema)
    except exceptions.SchemaError as e:
        raise AssertionError(f"Invalid JSON‑Schema: {e}") from e

    # Optionally, instantiate the validator to ensure it can be used later
    Draft7Validator(schema)  # will raise if schema is malformed

    # If we reach this point, the schema is syntactically correct.  No further
    # assertions are needed for this test.