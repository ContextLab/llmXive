"""Contract test for the Task definition CSV.

The test loads ``data/derived/task_definitions.csv`` and validates each
row against the JSON schema located at
``specs/001-llmxive-follow-up-extending-a-matter-of/task.schema.yaml``.
Any row missing a required field or violating type constraints will cause
the test to fail.
"""

import csv
import json
from pathlib import Path

import pytest
from jsonschema import Draft7Validator, RefResolver

from llmxive_toolkit import paths

# Resolve the schema file relative to the project root.
SCHEMA_PATH = Path(__file__).parents[2] / "specs" / "001-llmxive-follow-up-extending-a-matter-of" / "task.schema.yaml"
assert SCHEMA_PATH.is_file(), f"Schema file not found at {SCHEMA_PATH}"

@pytest.fixture(scope="module")
def schema():
    with SCHEMA_PATH.open("r", encoding="utf-8") as f:
        return json.load(f)

@pytest.fixture(scope="module")
def csv_path():
    return paths.data("derived", "task_definitions.csv")

def test_csv_exists(csv_path):
    assert csv_path.is_file(), f"Expected CSV at {csv_path}"

def test_rows_conform_to_schema(schema, csv_path):
    validator = Draft7Validator(schema)

    with csv_path.open("r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader, start=1):
            # Convert empty strings to ``None`` to match JSON ``null``.
            normalized = {k: (v if v != "" else None) for k, v in row.items()}
            errors = sorted(validator.iter_errors(normalized), key=lambda e: e.path)
            assert not errors, f"Row {i} failed validation: {errors}"