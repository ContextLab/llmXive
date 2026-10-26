"""Contract validation for all top‑level schemas.

The test suite loads the consolidated ``project.schema.yaml`` and
validates each artefact that exists on disk against its corresponding
definition.  At this stage of the project only ``CommitPair`` has
a concrete file (``data/raw/commit_pairs.csv``); additional artefacts
will be added in later tasks.
"""
from __future__ import annotations

import csv
import pathlib

import jsonschema
import yaml

from llmxive_toolkit import paths

# ----------------------------------------------------------------------
# Load the consolidated JSON‑Schema
# ----------------------------------------------------------------------
SCHEMA_PATH = pathlib.Path(
    "specs/001-evaluating-the-use-of-llms-for-automated/contracts/project.schema.yaml"
)

def load_schema() -> dict:
    with SCHEMA_PATH.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)

# ----------------------------------------------------------------------
# Helper to validate a CSV file against a schema definition
# ----------------------------------------------------------------------
def validate_csv(csv_path: pathlib.Path, definition_name: str) -> None:
    schema = load_schema()
    if "$defs" not in schema or definition_name not in schema["$defs"]:
        raise AssertionError(f"Schema definition {definition_name!r} not found")
    definition = schema["$defs"][definition_name]

    with csv_path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader, start=1):
            instance = {k: row[k] for k in definition["required"]}
            try:
                jsonschema.validate(instance=instance, schema=definition)
            except jsonschema.ValidationError as e:
                raise AssertionError(
                    f"{csv_path.name} row {i} fails {definition_name} schema: {e}"
                ) from e

# ----------------------------------------------------------------------
# Tests
# ----------------------------------------------------------------------
def test_commitpair_schema():
    """Validate ``data/raw/commit_pairs.csv`` against the ``CommitPair`` schema."""
    csv_path = paths.data("raw", "commit_pairs.csv")
    assert csv_path.exists(), f"{csv_path} does not exist"
    validate_csv(csv_path, "CommitPair")

# Placeholder hooks for future artefacts – they simply assert existence
# if the corresponding file is present.  This keeps the test suite
# extensible without causing failures for artefacts that have not yet
# generated.
def _optional_file_check(relative_path: str):
    path = paths.root / relative_path
    if path.exists():
        assert path.is_file(), f"{path} should be a regular file"

def test_generated_output_schema():
    _optional_file_check("data/generated/generation_success_rates.csv")

def test_entityset_schema():
    _optional_file_check("data/intermediate/surface_entities/sample.json")

def test_fidelity_metric_schema():
    _optional_file_check("data/processed/fidelity_metrics.csv")
