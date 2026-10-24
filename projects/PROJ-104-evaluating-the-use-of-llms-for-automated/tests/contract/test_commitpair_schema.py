"""Contract test for the commit‑pair CSV schema.

Validates that ``data/raw/commit_pairs.csv`` exists and conforms to the
JSON‑Schema definition in ``specs/001-evaluating-the-use-of-llms-for-automated/contracts/commitpair.schema.yaml``.
"""
from __future__ import annotations

import csv
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