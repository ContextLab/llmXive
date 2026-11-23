"""
Contract test that validates ``data/descriptors_subset.csv`` against the
JSON‑Schema defined in ``specs/001-llmxive-follow-up-extending-in-context-w/contracts/descriptor.schema.yaml``.
The test is executed after the extraction script has produced the CSV.
"""

import json
import pathlib

import jsonschema
import pandas as pd
import pytest

from llmxive_toolkit import paths

@pytest.fixture(scope="session")
def schema():
    schema_path = pathlib.Path(
        "specs/001-llmxive-follow-up-extending-in-context-w/contracts/descriptor.schema.yaml"
    )
    with open(schema_path, "r", encoding="utf-8") as f:
        return json.load(f)

def test_descriptors_schema_valid(schema):
    csv_path = paths.data("descriptors_subset.csv")
    assert csv_path.is_file(), f"{csv_path} does not exist"

    df = pd.read_csv(csv_path)
    for _, row in df.iterrows():
        record = {
            "clip_id": str(row["clip_id"]),
            "variance": (None if pd.isna(row["variance"]) else float(row["variance"])),
            "autocorr_lag1": (None if pd.isna(row["autocorr_lag1"]) else float(row["autocorr_lag1"])),
            "spectral_density": (None if pd.isna(row["spectral_density"]) else float(row["spectral_density"])),
        }
        jsonschema.validate(instance=record, schema=schema)

def test_no_missing_values():
    csv_path = paths.data("descriptors_subset.csv")
    df = pd.read_csv(csv_path)
    assert not df.isnull().values.any(), "CSV contains null/NaN values"