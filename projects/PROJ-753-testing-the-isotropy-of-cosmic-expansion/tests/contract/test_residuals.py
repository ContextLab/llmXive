"""
Contract test for data/processed/residuals.csv schema.

This test verifies that the residuals.csv file produced by the ingestion pipeline
adheres to the expected schema defined in the project specifications.

Required columns:
- ID: Supernova identifier (string)
- RA: Right Ascension in degrees (float)
- Dec: Declination in degrees (float)
- z: Redshift (float)
- mu_obs: Observed distance modulus (float)
- sigma_mu: Uncertainty in distance modulus (float)
- mu_th: Theoretical distance modulus (float)
- residual: Calculated residual (mu_obs - mu_th) (float)

Dependencies:
- T016 (Implementation of ingestion pipeline producing residuals.csv)
"""
import csv
import os
from pathlib import Path
import pytest

# Import project root helper from conftest
from conftest import project_root

REQUIRED_COLUMNS = [
    "ID",
    "RA",
    "Dec",
    "z",
    "mu_obs",
    "sigma_mu",
    "mu_th",
    "residual"
]

FILE_PATH = "data/processed/residuals.csv"

def get_residuals_path() -> Path:
    """Construct the absolute path to the residuals.csv file."""
    return project_root() / FILE_PATH

@pytest.fixture
def csv_data():
    """Load the CSV file content for testing."""
    path = get_residuals_path()
    if not path.exists():
        pytest.fail(f"Contract test failed: {FILE_PATH} does not exist. "
                    f"Ensure T016 (ingestion) has been run to generate the file.")
    
    with open(path, "r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        header = reader.fieldnames
    return header, rows

def test_schema_columns_exist(csv_data):
    """Verify that all required columns are present in the CSV header."""
    header, _ = csv_data
    missing = set(REQUIRED_COLUMNS) - set(header)
    assert not missing, (
        f"Schema contract violation: Missing required columns in {FILE_PATH}: {missing}. "
        f"Found columns: {header}"
    )

def test_schema_column_order(csv_data):
    """Verify that required columns appear in the expected order (if strict order is required).
    
    Note: While CSV readers often ignore order, some downstream tools might rely on it.
    We check that the required columns appear in the header in the order defined.
    """
    header, _ = csv_data
    # Filter header to only include required columns to check relative order
    filtered_header = [col for col in header if col in REQUIRED_COLUMNS]
    assert filtered_header == REQUIRED_COLUMNS, (
        f"Schema contract violation: Column order mismatch in {FILE_PATH}. "
        f"Expected order: {REQUIRED_COLUMNS}, Found: {filtered_header}"
    )

def test_schema_row_count(csv_data):
    """Verify that the file contains at least one row of data."""
    _, rows = csv_data
    assert len(rows) > 0, (
        f"Schema contract violation: {FILE_PATH} is empty. "
        f"Expected at least one data row."
    )

def test_schema_data_types(csv_data):
    """Verify that data types in the rows match the expected schema."""
    _, rows = csv_data
    
    for i, row in enumerate(rows):
        # ID should be non-empty string
        assert isinstance(row["ID"], str) and len(row["ID"]) > 0, \
            f"Row {i}: ID is not a non-empty string."
        
        # RA, Dec, z, mu_obs, sigma_mu, mu_th, residual should be convertible to float
        float_fields = ["RA", "Dec", "z", "mu_obs", "sigma_mu", "mu_th", "residual"]
        for field in float_fields:
            try:
                float(row[field])
            except ValueError:
                pytest.fail(f"Row {i}: Field '{field}' value '{row[field]}' is not a valid float.")

def test_schema_residual_consistency(csv_data):
    """Verify that the 'residual' column is consistent with mu_obs - mu_th."""
    _, rows = csv_data
    
    for i, row in enumerate(rows):
        mu_obs = float(row["mu_obs"])
        mu_th = float(row["mu_th"])
        residual = float(row["residual"])
        
        # Allow for small floating point differences
        expected_residual = mu_obs - mu_th
        tolerance = 1e-6
        
        if abs(residual - expected_residual) > tolerance:
            pytest.fail(
                f"Row {i}: Residual inconsistency. "
                f"mu_obs={mu_obs}, mu_th={mu_th}, expected residual={expected_residual}, "
                f"found residual={residual}."
            )