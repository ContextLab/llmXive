"""
Unit test that validates the cleaned dataset against the JSON schema
defined in ``specs/001-predicting-the-influence-of-composition/contracts/mg_dataset.schema.yaml``.
The test runs the ingestion pipeline (which writes the parquet file) and then
loads the parquet to ensure the schema contract holds.
"""

import json
from pathlib import Path

import pandas as pd
import pytest
import yaml

from llmxive_toolkit import paths
from features.dataset_models import validate_dataframe_schema

@pytest.fixture(scope="module")
def run_ingestion():
    """Execute the ingestion script once for the test session."""
    from code.ingestion.fetch_data import main as ingestion_main

    # The script writes its outputs; any exception will cause the test to fail.
    ingestion_main()

def test_clean_dataset_schema(run_ingestion):
    """
    Load the parquet file produced by the ingestion step and validate it
    against the JSON schema.
    """
    parquet_path = paths.data("processed", "clean_mg_data.parquet")
    assert parquet_path.is_file(), f"Expected parquet file at {parquet_path}"

    df = pd.read_parquet(parquet_path)
    assert not df.empty, "Clean dataset should contain at least one row."

    # Validate using the project's dataset model helper
    assert validate_dataframe_schema(df), "DataFrame does not conform to the schema."

    # Additional sanity check: required columns exist
    required_cols = {
        "material_id",
        "composition",
        "cte",
        "weighted_mean_atomic_radius",
        "electronegativity_variance",
        "vec",
        "atomic_size_coefficient_of_variation",
        "source_method",
        "amorphous_flag",
        "checksum",
    }
    assert required_cols.issubset(set(df.columns)), "Missing required columns in the cleaned dataset."
