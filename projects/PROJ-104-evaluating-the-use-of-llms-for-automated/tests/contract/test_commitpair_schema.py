"""Contract test for the commitpair CSV schema.

The schema is defined in `specs/001-evaluating-the-use-of-llms-for-automated/contracts/commitpair.schema.yaml`.
This test loads the CSV produced by `code/data_extraction.py` and
validates each row against the schema using jsonschema.
"""

from __future__ import annotations

import csv
import json
import pathlib

import jsonschema
import yaml

from llmxive_toolkit import paths

SCHEMA_PATH = pathlib.Path(
    "specs/001-evaluating-the-use-of-llms-for-automated/contracts/commitpair.schema.yaml"
)

def load_schema() -> dict:
    with SCHEMA_PATH.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def test_commitpair_csv_schema():
    schema = load_schema()
    csv_path = paths.data("raw", "commit_pairs.csv")
    assert csv_path.exists(), f"{csv_path} does not exist"

    with csv_path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader, start=1):
            # jsonschema expects proper JSON types; ensure fields are strings.
            instance = {
                "commit_hash": row["commit_hash"],
                "commit_message": row["commit_message"],
                "repository_name": row["repository_name"],
                "doc_diff": row["doc_diff"],
                "timestamp": row["timestamp"],
            }
            try:
                jsonschema.validate(instance=instance, schema=schema)
            except jsonschema.ValidationError as e:
                raise AssertionError(f"Row {i} fails schema validation: {e}") from e