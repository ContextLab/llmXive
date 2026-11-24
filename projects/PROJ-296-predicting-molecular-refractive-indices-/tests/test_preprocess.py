"""
Integration test for the preprocessing step.

The test creates a minimal raw CSV file with a couple of valid SMILES,
invokes the preprocessing script, and checks that the expected output
files exist and contain the required columns.
"""

import json
import os
from pathlib import Path

import pandas as pd
import pytest

from llmxive_toolkit import paths

# Import the main function from the script for direct invocation
from code.data.preprocess import main as preprocess_main


@pytest.fixture
def raw_csv_path():
    """Create a tiny raw CSV file in the expected location."""
    raw_path = Path(paths.root) / "data" / "raw" / "ri_dataset.csv"
    raw_path.parent.mkdir(parents=True, exist_ok=True)

    # Minimal dataset with two molecules
    df = pd.DataFrame(
        {
            "smiles": ["C", "CCO"],  # methane and ethanol
            "refractive_index": [1.33, 1.36],
            # optional temperature column to trigger normalisation
            "temperature": [20.0, 25.0],
        }
    )
    df.to_csv(raw_path, index=False)
    yield raw_path
    # Cleanup after test
    if raw_path.is_file():
        raw_path.unlink()


def test_preprocess_creates_splits(tmp_path, raw_csv_path):
    # Ensure a clean processed directory
    processed_dir = Path(paths.root) / "data" / "processed"
    if processed_dir.is_dir():
        for f in processed_dir.iterdir():
            f.unlink()
    else:
        processed_dir.mkdir(parents=True)

    # Run preprocessing (uses the global RAW_CSV_PATH)
    preprocess_main(filter_mw=500.0, split_ratio=(0.8, 0.1, 0.1))

    # Verify that the three split files exist
    for split_name in ["train", "val", "test"]:
        split_path = processed_dir / f"{split_name}.csv"
        assert split_path.is_file(), f"{split_name}.csv not created"

        df = pd.read_csv(split_path)
        # Required columns per schema
        required_cols = {
            "smiles",
            "molecular_weight",
            "refractive_index",
            "node_features",
            "edge_features",
            "scaffold_id",
        }
        assert required_cols.issubset(set(df.columns)), f"Missing columns in {split_name}.csv"

        # Spot‑check that node_features and edge_features are valid JSON strings
        for _, row in df.iterrows():
            json.loads(row["node_features"])
            json.loads(row["edge_features"])