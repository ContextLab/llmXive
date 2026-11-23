"""
Unit tests for the bulk‑property retrieval script (T024).

The tests verify that the script creates the expected processed CSV,
that the required columns are present, and that the JSON‑Schema
validation passes.
"""

import pathlib
import pandas as pd
import pytest

from llmxive_toolkit import paths

# Import the script as a module to call its ``main`` function.
import sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / "code"))
from retrieve_bulk_properties import main as retrieve_main


def test_bulk_properties_file_created(tmp_path, monkeypatch):
    """
    Run the script and check that the processed CSV exists and contains
    the correct columns.
    """
    # Monkey‑patch the output location to a temporary directory so the test
    # does not interfere with the repository state.
    processed_path = tmp_path / "bulk_properties.csv"
    monkeypatch.setattr(
        "retrieve_bulk_properties.PROCESSED_BULK_CSV", processed_path
    )

    # Execute the retrieval script.
    retrieve_main()

    # Verify the file was created.
    assert processed_path.is_file(), "Processed bulk properties CSV was not created"

    # Load and inspect the CSV.
    df = pd.read_csv(processed_path)
    expected_cols = {"pair_id", "density", "viscosity"}
    assert set(df.columns) == expected_cols, f"Columns mismatch: {df.columns}"

    # Basic sanity check: there should be at least one row (the fallback CSV
    # contains 20 rows).
    assert len(df) > 0, "Processed CSV is empty"


def test_schema_validation(tmp_path, monkeypatch):
    """
    Ensure that the JSON‑Schema validation runs without raising an error.
    """
    processed_path = tmp_path / "bulk_properties.csv"
    monkeypatch.setattr(
        "retrieve_bulk_properties.PROCESSED_BULK_CSV", processed_path
    )

    # Run the script – any ValidationError would cause the test to fail.
    retrieve_main()

    # Load the CSV and manually validate a random row against the schema.
    df = pd.read_csv(processed_path)
    schema_path = pathlib.Path(__file__).resolve().parents[2] / "contracts" / "raw_bulk_properties.schema.yaml"
    import yaml
    from jsonschema import validate

    schema = yaml.safe_load(schema_path.read_text())
    # Validate the first row.
    validate(instance=df.iloc[0].to_dict(), schema=schema)