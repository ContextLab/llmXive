"""
Contract test for the generated stimulus CSV.

This test loads ``data/raw/stimuli.csv`` and validates it against the
JSON/YAML schema defined in ``specs/001-the-impact-of-text-message-tone-on-perce/contracts/stimulus.schema.yaml``.
The schema file is assumed to exist in the repository (it is part of the
specification). The test uses the project's ``validate_schemas`` helper
to perform the validation.
"""

import pathlib
import pytest

from validate_schemas import load_schema, validate_csv_against_schema

# Resolve paths relative to the repository root
PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[2]

STIMULI_CSV = PROJECT_ROOT / "data" / "raw" / "stimuli.csv"
SCHEMA_PATH = (
    PROJECT_ROOT
    / "specs"
    / "001-the-impact-of-text-message-tone-on-perce"
    / "contracts"
    / "stimulus.schema.yaml"
)

def test_stimuli_file_exists():
    assert STIMULI_CSV.is_file(), f"Stimuli CSV not found at {STIMULI_CSV}"

def test_schema_validation():
    schema = load_schema(SCHEMA_PATH)
    # The helper raises a ValidationError on failure; we simply call it.
    validate_csv_against_schema(STIMULI_CSV, schema)