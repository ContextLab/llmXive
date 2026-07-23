"""
Contract tests for the output schema of the data pipeline (US1).

These tests verify that the final merged dataset (CSV/Parquet) produced by
the pipeline adheres to the expected schema defined in the feature specification.

The tests are designed to fail loudly if the schema is violated, ensuring
data integrity before downstream analysis.

Expected Output File: data/processed/merged_dataset.parquet (or .csv)
"""
import os
import pytest
import pandas as pd
from pathlib import Path

# Constants for schema validation
EXPECTED_COLUMNS = {
    "strain_id",
    "species",
    "genome_path",
    "phenotype_score",
    "feature_id",
    "feature_type",
    "presence_binary",
    "pwm_count",
    "source"
}

REQUIRED_COLUMNS = {
    "strain_id",
    "species",
    "phenotype_score",
    "feature_id"
}

# Expected data types for key columns
EXPECTED_DTYPES = {
    "strain_id": "object",
    "species": "object",
    "phenotype_score": "float64",
    "presence_binary": "int64",
    "pwm_count": "int64"
}

PROJECT_ROOT = Path(__file__).parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data" / "processed"
PARQUET_PATH = DATA_DIR / "merged_dataset.parquet"
CSV_PATH = DATA_DIR / "merged_dataset.csv"

def _load_dataset():
    """
    Load the dataset from disk.
    Prefers Parquet, falls back to CSV if Parquet doesn't exist.
    Raises FileNotFoundError if neither exists.
    """
    if PARQUET_PATH.exists():
        return pd.read_parquet(PARQUET_PATH)
    elif CSV_PATH.exists():
        return pd.read_csv(CSV_PATH)
    else:
        raise FileNotFoundError(
            f"Output dataset not found. Expected at {PARQUET_PATH} or {CSV_PATH}. "
            "Run the data pipeline (T015-T021) to generate the dataset."
        )

class TestOutputSchema:
    """
    Contract tests for the merged dataset schema.
    """

    def test_file_exists(self):
        """Contract: The output file must exist."""
        assert PARQUET_PATH.exists() or CSV_PATH.exists(), (
            "Output file does not exist. The pipeline must be run first."
        )

    def test_required_columns_present(self):
        """Contract: All required columns must be present."""
        df = _load_dataset()
        missing_cols = REQUIRED_COLUMNS - set(df.columns)
        assert not missing_cols, f"Missing required columns: {missing_cols}"

    def test_expected_columns_present(self):
        """Contract: All expected columns from the spec must be present."""
        df = _load_dataset()
        missing_cols = EXPECTED_COLUMNS - set(df.columns)
        assert not missing_cols, f"Missing expected columns: {missing_cols}"

    def test_no_extra_columns(self):
        """Contract: No unexpected columns should be present (strict schema)."""
        df = _load_dataset()
        extra_cols = set(df.columns) - EXPECTED_COLUMNS
        # Allow metadata columns if specified, but for now, strict check
        assert not extra_cols, f"Unexpected columns found: {extra_cols}"

    def test_data_types_correct(self):
        """Contract: Data types for key columns must match expectations."""
        df = _load_dataset()
        for col, expected_type in EXPECTED_DTYPES.items():
            if col in df.columns:
                # Normalize pandas dtypes for comparison
                actual_type = str(df[col].dtype)
                # Handle potential object vs string differences
                if expected_type == "object":
                    assert df[col].dtype == "object" or df[col].dtype.name == "string"
                else:
                    assert actual_type == expected_type, (
                        f"Column '{col}' has dtype {actual_type}, expected {expected_type}"
                    )

    def test_no_null_strain_ids(self):
        """Contract: strain_id must not be null."""
        df = _load_dataset()
        assert df["strain_id"].isnull().sum() == 0, "Found null values in 'strain_id'"

    def test_no_null_phenotype_scores(self):
        """Contract: phenotype_score must not be null (rows are dropped if missing)."""
        df = _load_dataset()
        assert df["phenotype_score"].isnull().sum() == 0, "Found null values in 'phenotype_score'"

    def test_minimum_record_count(self):
        """Contract: Dataset must contain at least 10 distinct isolates (US1 requirement)."""
        df = _load_dataset()
        unique_isolates = df["strain_id"].nunique()
        assert unique_isolates >= 10, (
            f"Dataset contains only {unique_isolates} distinct isolates. "
            "US1 requires at least 10."
        )

    def test_presence_binary_values(self):
        """Contract: presence_binary must be 0 or 1."""
        df = _load_dataset()
        valid_values = {0, 1}
        unique_values = set(df["presence_binary"].unique())
        invalid_values = unique_values - valid_values
        assert not invalid_values, f"Invalid values in 'presence_binary': {invalid_values}"

    def test_species_not_empty(self):
        """Contract: species column must not contain empty strings."""
        df = _load_dataset()
        assert not df["species"].isin(["", " ", None]).any(), "Found empty or null species names"

    def test_file_format_valid(self):
        """Contract: If Parquet exists, it must be readable by pyarrow/fastparquet."""
        if PARQUET_PATH.exists():
            try:
                pd.read_parquet(PARQUET_PATH)
            except Exception as e:
                pytest.fail(f"Parquet file is corrupted or invalid: {e}")
        elif CSV_PATH.exists():
            try:
                pd.read_csv(CSV_PATH)
            except Exception as e:
                pytest.fail(f"CSV file is corrupted or invalid: {e}")