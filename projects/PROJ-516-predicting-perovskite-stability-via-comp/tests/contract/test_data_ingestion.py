"""
Contract test for data ingestion output schema (T010).
Verifies that the final processed dataset contains the required columns
with non-null values as specified in the user story 1 requirements.
"""
import os
import sys
import pytest
import pandas as pd
from pathlib import Path

# Add project root to path for imports if running via pytest
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

REQUIRED_COLUMNS = [
    "formula",
    "T_d",
    "atomic_fraction_A",
    "atomic_fraction_B",
    "atomic_fraction_X",
    "weighted_ionic_radius",
    "weighted_electronegativity",
    "weighted_formation_enthalpy",
    "variance_ionic_radius",
    "variance_electronegativity",
    "total_uncertainty"
]

# The expected output file path based on the pipeline flow
# T017 writes to data/processed/descriptors_final.csv
EXPECTED_OUTPUT_PATH = PROJECT_ROOT / "data" / "processed" / "descriptors_final.csv"

def test_output_file_exists():
    """Verify that the final processed dataset file exists."""
    assert EXPECTED_OUTPUT_PATH.exists(), (
        f"Output file {EXPECTED_OUTPUT_PATH} does not exist. "
        "Ensure the data ingestion pipeline (T012-T017) has been run successfully."
    )

def test_required_columns_present():
    """Verify that the output CSV contains all required columns."""
    df = pd.read_csv(EXPECTED_OUTPUT_PATH)
    missing_columns = set(REQUIRED_COLUMNS) - set(df.columns)
    assert not missing_columns, (
        f"Missing required columns in {EXPECTED_OUTPUT_PATH}: {missing_columns}. "
        f"Found columns: {list(df.columns)}"
    )

def test_columns_non_null():
    """Verify that all required columns have non-null values."""
    df = pd.read_csv(EXPECTED_OUTPUT_PATH)
    for col in REQUIRED_COLUMNS:
        null_count = df[col].isnull().sum()
        assert null_count == 0, (
            f"Column '{col}' contains {null_count} null values in {EXPECTED_OUTPUT_PATH}. "
            "All required columns must have non-null values."
        )

def test_data_types():
    """Verify that numeric columns contain numeric data."""
    df = pd.read_csv(EXPECTED_OUTPUT_PATH)
    numeric_cols = [
        "T_d",
        "atomic_fraction_A",
        "atomic_fraction_B",
        "atomic_fraction_X",
        "weighted_ionic_radius",
        "weighted_electronegativity",
        "weighted_formation_enthalpy",
        "variance_ionic_radius",
        "variance_electronegativity",
        "total_uncertainty"
    ]
    for col in numeric_cols:
        # Check if the column can be converted to numeric
        # This handles cases where the column might be read as object due to mixed types
        try:
            pd.to_numeric(df[col])
        except (ValueError, TypeError):
            pytest.fail(f"Column '{col}' contains non-numeric data: {df[col].head()}")

def test_formula_validity():
    """Verify that formula entries are non-empty strings."""
    df = pd.read_csv(EXPECTED_OUTPUT_PATH)
    assert all(df["formula"].astype(str).str.len() > 0), (
        "All formula entries must be non-empty strings."
    )

def test_total_uncertainty_positive():
    """Verify that total_uncertainty values are non-negative."""
    df = pd.read_csv(EXPECTED_OUTPUT_PATH)
    assert all(df["total_uncertainty"] >= 0), (
        "All total_uncertainty values must be non-negative."
    )