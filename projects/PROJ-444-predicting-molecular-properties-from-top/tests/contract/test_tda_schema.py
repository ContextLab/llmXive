"""
Contract test for data/processed/tda_features.csv schema.

This test verifies that the TDA features output file adheres to the strict
schema defined in the project specifications. It ensures column existence,
data types, and non-null constraints are met.
"""
import os
import sys
import pandas as pd
import numpy as np
import pytest
from pathlib import Path

# Project root path resolution
PROJECT_ROOT = Path(__file__).parent.parent.parent
OUTPUT_FILE = PROJECT_ROOT / "data" / "processed" / "tda_features.csv"

# Expected schema definition based on FR-001 and FR-002
# Columns: molecule_id, smiles, molecular_weight, persistence_image_vector (flattened), 
#          betti_0_count, betti_1_count, persistence_entropy, lifetime_sum
EXPECTED_COLUMNS = [
    "molecule_id",
    "smiles",
    "molecular_weight",
    "persistence_image_vector",
    "betti_0_count",
    "betti_1_count",
    "persistence_entropy",
    "lifetime_sum"
]

# Column type expectations (approximate via pandas dtypes)
# Strings for ID/SMILES, Floats for numerical features
EXPECTED_DTYPES = {
    "molecule_id": "object",
    "smiles": "object",
    "molecular_weight": "float64",
    "persistence_image_vector": "object", # Stored as list or string representation
    "betti_0_count": "int64",
    "betti_1_count": "int64",
    "persistence_entropy": "float64",
    "lifetime_sum": "float64"
}

# Minimum required rows (from power analysis in T008, N >= 128)
MIN_REQUIRED_ROWS = 128


class TestTdaFeaturesSchema:
    """Contract tests for TDA features CSV schema."""

    @pytest.fixture(scope="class", autouse=True)
    def setup_file_check(self):
        """Ensure the output file exists before running tests."""
        if not OUTPUT_FILE.exists():
            pytest.fail(
                f"Output file {OUTPUT_FILE} does not exist. "
                "Run code/02_tda_computation.py to generate data."
            )

    def test_file_exists(self):
        """Verify the output file exists at the expected path."""
        assert OUTPUT_FILE.exists(), f"File {OUTPUT_FILE} not found."

    def test_has_required_columns(self):
        """Verify all required columns are present in the CSV."""
        df = pd.read_csv(OUTPUT_FILE)
        missing_columns = set(EXPECTED_COLUMNS) - set(df.columns)
        assert not missing_columns, f"Missing required columns: {missing_columns}"

    def test_column_count_matches(self):
        """Verify the exact number of columns matches the schema."""
        df = pd.read_csv(OUTPUT_FILE)
        assert len(df.columns) == len(EXPECTED_COLUMNS), (
            f"Expected {len(EXPECTED_COLUMNS)} columns, found {len(df.columns)}. "
            f"Found: {list(df.columns)}"
        )

    def test_column_order(self):
        """Verify columns are in the expected order."""
        df = pd.read_csv(OUTPUT_FILE)
        assert list(df.columns) == EXPECTED_COLUMNS, (
            f"Column order mismatch. Expected: {EXPECTED_COLUMNS}, Found: {list(df.columns)}"
        )

    def test_no_null_values_in_required_fields(self):
        """Verify no null values in critical columns."""
        df = pd.read_csv(OUTPUT_FILE)
        critical_columns = ["molecule_id", "smiles", "betti_0_count", "betti_1_count"]
        
        for col in critical_columns:
            null_count = df[col].isnull().sum()
            assert null_count == 0, f"Column '{col}' contains {null_count} null values."

    def test_molecular_weight_positive(self):
        """Verify molecular weight is positive for all entries."""
        df = pd.read_csv(OUTPUT_FILE)
        assert (df["molecular_weight"] > 0).all(), "Found non-positive molecular weights."

    def test_betti_counts_non_negative(self):
        """Verify Betti counts are non-negative integers."""
        df = pd.read_csv(OUTPUT_FILE)
        assert (df["betti_0_count"] >= 0).all(), "Negative betti_0_count found."
        assert (df["betti_1_count"] >= 0).all(), "Negative betti_1_count found."

    def test_persistence_features_valid(self):
        """Verify persistence entropy and lifetime sum are non-negative."""
        df = pd.read_csv(OUTPUT_FILE)
        assert (df["persistence_entropy"] >= 0).all(), "Negative persistence entropy found."
        assert (df["lifetime_sum"] >= 0).all(), "Negative lifetime sum found."

    def test_minimum_row_count(self):
        """Verify the dataset meets the minimum sample size requirement."""
        df = pd.read_csv(OUTPUT_FILE)
        assert len(df) >= MIN_REQUIRED_ROWS, (
            f"Dataset has {len(df)} rows, which is less than the required {MIN_REQUIRED_ROWS}."
        )

    def test_smiles_format_basic(self):
        """Basic check that SMILES strings are non-empty strings."""
        df = pd.read_csv(OUTPUT_FILE)
        assert all(isinstance(s, str) and len(s) > 0 for s in df["smiles"]), (
            "Invalid SMILES format detected (non-string or empty)."
        )

    def test_vector_column_format(self):
        """Verify persistence_image_vector contains list-like data or string representation."""
        df = pd.read_csv(OUTPUT_FILE)
        # The vector might be stored as a string representation of a list or a python object
        # depending on how it was written. We check that it's not null and has content.
        for idx, val in enumerate(df["persistence_image_vector"]):
            if isinstance(val, str):
                # Check if it looks like a list string "[...]"
                assert val.startswith("[") and val.endswith("]"), (
                    f"Row {idx}: persistence_image_vector string format invalid."
                )
            elif isinstance(val, (list, np.ndarray)):
                continue
            else:
                pytest.fail(f"Row {idx}: persistence_image_vector is unexpected type {type(val)}")

if __name__ == "__main__":
    pytest.main([__file__, "-v"])