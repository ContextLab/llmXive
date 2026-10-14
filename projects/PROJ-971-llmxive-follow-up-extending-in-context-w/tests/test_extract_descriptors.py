"""
Unit test for ``src.pipeline.extract_descriptors``.

The test validates that the CSV produced by ``extract_all_descriptors``
conforms to the JSON‑Schema defined at
``specs/001-llmxive-follow-up-extending-in-context-w/contracts/descriptor.schema.yaml``.
"""

import json
from pathlib import Path

import pandas as pd
import pytest
from jsonschema import validate, ValidationError

# Import the function under test.
from src.pipeline.extract_descriptors import extract_all_descriptors

# Path helpers.
from llmxive_toolkit import paths

# Load the JSON‑Schema once.
SCHEMA_PATH = Path(__file__).parents[1] / "specs" / "001-llmxive-follow-up-extending-in-context-w" / "contracts" / "descriptor.schema.yaml"

@pytest.fixture(scope="module")
def descriptor_schema():
    """Load the descriptor JSON‑Schema."""
    import yaml
    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        schema = yaml.safe_load(f)
    return schema

def test_descriptors_schema_validation(tmp_path, descriptor_schema):
    """
    Run the descriptor extraction on whatever clips are present in the
    repository (typically a small test set) and ensure the resulting CSV
    validates against the schema.
    """
    # Use the repository's existing raw data directory.
    input_dir = paths.data("raw")
    output_path = tmp_path / "descriptors_test.csv"

    # Perform extraction (should not raise).
    extract_all_descriptors(input_dir, output_path)

    # Load the resulting CSV.
    df = pd.read_csv(output_path)

    # Basic sanity: required columns exist.
    required_cols = {"clip_id", "variance", "autocorr_lag1", "spectral_density"}
    assert required_cols.issubset(set(df.columns)), "Missing required columns in CSV"

    # Validate each record against the JSON‑Schema.
    for _, row in df.iterrows():
        record = {
            "clip_id": str(row["clip_id"]),
            "variance": float(row["variance"]),
            "autocorr_lag1": float(row["autocorr_lag1"]),
            "spectral_density": float(row["spectral_density"]),
        }
        try:
            validate(instance=record, schema=descriptor_schema)
        except ValidationError as exc:
            pytest.fail(f"Descriptor record failed schema validation: {exc}")

def test_empty_input_dir_creates_header(tmp_path):
    """
    Ensure that when the input directory contains no ``clip_*.npz`` files,
    the function still creates a CSV with only the header and does not
    raise an exception.
    """
    empty_dir = tmp_path / "empty_raw"
    empty_dir.mkdir()
    output_path = tmp_path / "empty_descriptors.csv"

    # Should complete without error.
    extract_all_descriptors(empty_dir, output_path)

    df = pd.read_csv(output_path)
    # Expect zero rows but correct columns.
    assert df.empty
    assert list(df.columns) == ["clip_id", "variance", "autocorr_lag1", "spectral_density"]