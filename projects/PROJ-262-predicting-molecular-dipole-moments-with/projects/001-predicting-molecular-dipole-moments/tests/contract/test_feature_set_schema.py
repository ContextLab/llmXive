import pathlib

import yaml
import jsonschema


def test_feature_set_schema_is_valid():
    """
    Load the feature_set JSON schema and verify that it is a valid JSON Schema
    definition according to jsonschema Draft7 specification.
    """
    # Resolve the path to the schema file located in the contracts directory
    schema_path = (
        pathlib.Path(__file__)
        .resolve()
        .parents[2]
        / "contracts"
        / "feature_set.schema.yaml"
    )

    # Load the YAML schema
    with open(schema_path, "r") as f:
        schema = yaml.safe_load(f)

    # Basic sanity check: the schema should be a mapping
    assert isinstance(schema, dict), "Schema file did not load as a dictionary"

    # Validate that the schema itself conforms to JSON Schema Draft7
    jsonschema.Draft7Validator.check_schema(schema)
