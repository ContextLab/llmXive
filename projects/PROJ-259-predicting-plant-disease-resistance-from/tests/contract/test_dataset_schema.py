"""
Test that the data manifest conforms to the dataset schema.

The schema is defined in ``contracts/dataset.schema.yaml`` and the
manifest is located at ``data/data_manifest.yaml``.  The test loads both
files using ``PyYAML`` and validates the manifest with ``jsonschema``.
Any ``jsonschema.exceptions.ValidationError`` will cause the test to
fail, which is the desired behaviour.
"""

import jsonschema
import yaml
from llmxive_toolkit import paths

def _load_yaml(path):
    """Load a YAML file and return the parsed Python object."""
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def test_data_manifest_schema():
    """
    Validate ``data/data_manifest.yaml`` against the JSON schema
    defined in ``contracts/dataset.schema.yaml``.
    """
    # Resolve paths using the toolkit helpers
    manifest_path = paths.data("data_manifest.yaml")
    schema_path = paths.contracts("dataset.schema.yaml")

    # Load the files
    manifest = _load_yaml(manifest_path)
    schema = _load_yaml(schema_path)

    # Perform validation – any ValidationError will cause pytest to fail
    jsonschema.validate(instance=manifest, schema=schema)