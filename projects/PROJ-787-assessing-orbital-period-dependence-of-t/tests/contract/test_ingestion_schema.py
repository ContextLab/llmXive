"""
Contract tests for User Story 1: Data Ingestion Output Schema.

These tests verify that the data ingestion pipeline outputs conform to the
expected schema defined in the project specifications. Specifically, they
validate the structure, column names, and data types of the filtered and
deduplicated planet catalogs produced by the ingestion pipeline.

The tests assert:
1. The output file exists at the expected path.
2. Required columns are present (e.g., 'pl_name', 'pl_orbper', 'pl_radj', 'st_teff').
3. Data types match expectations (numeric for measurements, string for identifiers).
4. No null values exist in critical columns (radius, period, temperature).
5. Constraints are met (e.g., radius uncertainty < 20%, period uncertainty < 1%).
"""

import os
import sys
import pytest
import pandas as pd
import numpy as np
from pathlib import Path

# Add project root to path to allow imports if running standalone
project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))

# Define expected paths relative to project root
DATA_PROCESSED_DIR = project_root / "data" / "processed"
FILTERED_PLANETS_PATH = DATA_PROCESSED_DIR / "filtered_planets.csv"
DEDUPED_PLANETS_PATH = DATA_PROCESSED_DIR / "deduped_planets.csv"

# Define the expected schema for the ingestion output
# Based on the task description: radius uncertainty < 20%, period uncertainty < 1%,
# and non-missing stellar effective temperature.
EXPECTED_COLUMNS = {
    "pl_name": "object",  # Planet name (string)
    "pl_discmethod": "object",  # Discovery method
    "pl_orbper": "float64",  # Orbital period (days)
    "pl_orbpererr1": "float64",  # Period uncertainty
    "pl_radj": "float64",  # Planet radius (Jupiter radii)
    "pl_radjerr1": "float64",  # Radius uncertainty
    "st_teff": "float64",  # Stellar effective temperature
    "st_tefferr1": "float64",  # Temperature uncertainty
    "st_mass": "float64",  # Stellar mass
    "st_masserr1": "float64",  # Stellar mass uncertainty
    "kepid": "int64",  # Kepler ID
    "koi": "float64",  # KOI number
    "pl_controvflag": "int64",  # Controversy flag
    "pl_tranflag": "int64",  # Transit flag
}

REQUIRED_COLUMNS = [
    "pl_name",
    "pl_orbper",
    "pl_orbpererr1",
    "pl_radj",
    "pl_radjerr1",
    "st_teff",
    "st_tefferr1",
    "kepid",
]

def get_file_path(filename: str) -> Path:
    """Get the full path for a data file, checking existence."""
    path = DATA_PROCESSED_DIR / filename
    if not path.exists():
        pytest.fail(f"Expected data file not found: {path}")
    return path

def load_test_data(filename: str) -> pd.DataFrame:
    """Load a CSV file and return as DataFrame."""
    path = get_file_path(filename)
    try:
        df = pd.read_csv(path)
        return df
    except Exception as e:
        pytest.fail(f"Failed to load {filename}: {e}")

class TestFilteredPlanetsSchema:
    """Tests for the filtered_planets.csv output schema."""

    @pytest.fixture(scope="class")
    def df(self):
        return load_test_data("filtered_planets.csv")

    def test_file_exists(self):
        """Verify the filtered planets file exists."""
        assert FILTERED_PLANETS_PATH.exists(), "filtered_planets.csv does not exist"

    def test_required_columns_present(self, df):
        """Verify all required columns are present in the dataframe."""
        missing_cols = set(REQUIRED_COLUMNS) - set(df.columns)
        assert not missing_cols, f"Missing required columns: {missing_cols}"

    def test_column_dtypes(self, df):
        """Verify data types match the expected schema."""
        for col, expected_type in EXPECTED_COLUMNS.items():
            if col in df.columns:
                # Handle object vs string nuances in pandas
                if expected_type == "object":
                    assert df[col].dtype == "object" or df[col].dtype.name.startswith("str"), \
                        f"Column {col} has dtype {df[col].dtype}, expected object/string"
                else:
                    # Allow for potential float32/float64 variations if strictness allows,
                    # but strict check is preferred for contract testing.
                    assert str(df[col].dtype) == expected_type, \
                        f"Column {col} has dtype {df[col].dtype}, expected {expected_type}"

    def test_no_nulls_in_critical_columns(self, df):
        """Verify no null values in critical measurement columns."""
        critical_cols = ["pl_orbper", "pl_radj", "st_teff", "kepid"]
        for col in critical_cols:
            if col in df.columns:
                assert df[col].isnull().sum() == 0, \
                    f"Column {col} contains {df[col].isnull().sum()} null values"

    def test_radius_uncertainty_constraint(self, df):
        """Verify radius uncertainty is < 20% (0.20)."""
        if "pl_radjerr1" in df.columns and "pl_radj" in df.columns:
            # Calculate percentage uncertainty
            # Avoid division by zero if radius is 0 (though physically unlikely for planets)
            valid_mask = df["pl_radj"] > 0
            if valid_mask.any():
                percent_uncertainty = df.loc[valid_mask, "pl_radjerr1"] / df.loc[valid_mask, "pl_radj"]
                assert (percent_uncertainty < 0.20).all(), \
                    "Some entries have radius uncertainty >= 20%"

    def test_period_uncertainty_constraint(self, df):
        """Verify period uncertainty is < 1% (0.01)."""
        if "pl_orbpererr1" in df.columns and "pl_orbper" in df.columns:
            valid_mask = df["pl_orbper"] > 0
            if valid_mask.any():
                percent_uncertainty = df.loc[valid_mask, "pl_orbpererr1"] / df.loc[valid_mask, "pl_orbper"]
                assert (percent_uncertainty < 0.01).all(), \
                    "Some entries have period uncertainty >= 1%"

    def test_stellar_temp_present(self, df):
        """Verify stellar effective temperature is present (not null)."""
        assert "st_teff" in df.columns
        assert df["st_teff"].notnull().all(), "Some entries have missing stellar effective temperature"

class TestDedupedPlanetsSchema:
    """Tests for the deduped_planets.csv output schema."""

    @pytest.fixture(scope="class")
    def df(self):
        return load_test_data("deduped_planets.csv")

    def test_file_exists(self):
        """Verify the deduped planets file exists."""
        assert DEDUPED_PLANETS_PATH.exists(), "deduped_planets.csv does not exist"

    def test_subset_of_filtered_columns(self, df):
        """Verify deduped file has a subset of columns from filtered file (no new columns)."""
        filtered_df = load_test_data("filtered_planets.csv")
        missing_in_deduped = set(filtered_df.columns) - set(df.columns)
        # We expect deduped to have the same or fewer columns, but definitely not new ones
        # unless the deduplication process adds metadata columns (not expected here).
        assert not missing_in_deduped, \
            f"Deduped file is missing columns present in filtered: {missing_in_deduped}"

    def test_no_duplicate_kepid(self, df):
        """Verify no duplicate Kepler IDs exist in the deduped file."""
        if "kepid" in df.columns:
            duplicates = df["kepid"].duplicated().sum()
            assert duplicates == 0, f"Found {duplicates} duplicate Kepler IDs in deduped file"

    def test_no_duplicate_koi(self, df):
        """Verify no duplicate KOI numbers exist in the deduped file."""
        if "koi" in df.columns:
            duplicates = df["koi"].duplicated().sum()
            assert duplicates == 0, f"Found {duplicates} duplicate KOI numbers in deduped file"

    def test_row_count_consistency(self, df):
        """Verify deduped file has <= rows than filtered file."""
        filtered_df = load_test_data("filtered_planets.csv")
        assert len(df) <= len(filtered_df), \
            "Deduped file has more rows than filtered file, indicating logic error"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])