"""
Contract test for the DocumentPair schema.

Ensures that the Parquet file produced by the preprocessing step (not part of
T001) conforms to the JSON schema defined in
`specs/001-llmxive-follow-up-extending-scalable-vis/contracts/documentpair.schema.yaml`.
This test will be executed by the CI after the preprocessing step is implemented.
"""

import json
import pathlib

import yaml
from jsonschema import Draft7Validator

# Path to the schema (relative to the repository root)
SCHEMA_PATH = pathlib.Path(
    "specs/001-llmxive-follow-up-extending-scalable-vis/contracts/documentpair.schema.yaml"
)

def load_schema() -> dict:
    with SCHEMA_PATH.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def test_documentpair_schema_is_valid():
    schema = load_schema()
    # The schema itself should be a valid Draft‑07 schema
    Draft7Validator.check_schema(schema)