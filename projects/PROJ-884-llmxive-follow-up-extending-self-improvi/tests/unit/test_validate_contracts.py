"""
Unit tests to ensure that the JSON‑Schema contract files are syntactically valid YAML.
This satisfies task T015 which requires that loading the schema files with
`yaml.safe_load` does not raise an exception.
"""

import yaml
from pathlib import Path

def test_dataset_schema_load():
    """Load contracts/dataset.schema.yaml and ensure it parses as valid YAML."""
    schema_path = Path("contracts/dataset.schema.yaml")
    assert schema_path.is_file(), f"Schema file not found: {schema_path}"
    # yaml.safe_load will raise if the file is not valid YAML
    yaml.safe_load(schema_path.read_text())

def test_output_schema_load():
    """Load contracts/output.schema.yaml and ensure it parses as valid YAML."""
    schema_path = Path("contracts/output.schema.yaml")
    assert schema_path.is_file(), f"Schema file not found: {schema_path}"
    yaml.safe_load(schema_path.read_text())