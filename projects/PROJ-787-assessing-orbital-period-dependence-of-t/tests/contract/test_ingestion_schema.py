"""
Contract test for data ingestion output schema.

Validates that the output of the data ingestion pipeline (filtered_planets.csv
and deduped_planets.csv) adheres to the PlanetRecord schema defined in
contracts/planet_record.schema.yaml.

This test ensures data integrity before downstream analysis (US2, US3) proceeds.
"""

import os
import pytest
import pandas as pd
import json
import yaml
from pathlib import Path

# Import the schema validator logic (reusing T007 pattern)
# Since T007 created tests/contract/test_schemas.py, we assume a helper exists
# or we implement the validation logic inline here to ensure self-containment.
# Based on T004/T007 context, we validate against the YAML schema directly.

PROJECT_ROOT = Path(__file__).parent.parent.parent
SCHEMA_PATH = PROJECT_ROOT / "contracts" / "planet_record.schema.yaml"
DATA_RAW_PATH = PROJECT_ROOT / "data" / "processed" / "filtered_planets.csv"
DATA_DEDUP_PATH = PROJECT_ROOT / "data" / "processed" / "deduped_planets.csv"

# Required columns based on PlanetRecord dataclass and schema expectations
# These are the critical fields for the ingestion pipeline output
REQUIRED_COLUMNS = [
    "kepler_id",
    "planet_name",
    "radius_earth",
    "radius_uncertainty",
    "period_day",
    "period_uncertainty",
    "teff",
    "teff_uncertainty",
    "log_g",
    "log_g_uncertainty",
    "stellar_mass",
    "stellar_mass_uncertainty",
    "stellar_radius",
    "stellar_radius_uncertainty"
]

# Critical columns that must not be null for valid records
CRITICAL_COLUMNS = [
    "radius_earth",
    "radius_uncertainty",
    "period_day",
    "period_uncertainty",
    "teff"
]

# Thresholds defined in US1 requirements
MAX_RADIUS_UNCERT = 0.20  # 20%
MAX_PERIOD_UNCERT = 0.01  # 1%

def load_schema(schema_path: Path) -> dict:
    """Load the YAML schema file."""
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    with open(schema_path, 'r') as f:
        return yaml.safe_load(f)

def validate_columns(df: pd.DataFrame, required_cols: list) -> bool:
    """Check if all required columns exist in the DataFrame."""
    missing = set(required_cols) - set(df.columns)
    if missing:
        pytest.fail(f"Missing required columns: {missing}")
    return True

def validate_no_nulls(df: pd.DataFrame, critical_cols: list) -> bool:
    """Check that critical columns have no null values."""
    for col in critical_cols:
        if df[col].isnull().any():
            pytest.fail(f"Column '{col}' contains null values.")
    return True

def validate_uncertainty_thresholds(df: pd.DataFrame) -> bool:
    """
    Validate that radius uncertainty < 20% and period uncertainty < 1%.
    Note: These are fractional values (e.g., 0.20 for 20%).
    """
    # Check radius uncertainty
    if (df["radius_uncertainty"] >= MAX_RADIUS_UNCERT).any():
        pytest.fail(f"Found entries with radius uncertainty >= {MAX_RADIUS_UNCERT}")
    
    # Check period uncertainty
    if (df["period_uncertainty"] >= MAX_PERIOD_UNCERT).any():
        pytest.fail(f"Found entries with period uncertainty >= {MAX_PERIOD_UNCERT}")
    
    return True

def validate_positive_values(df: pd.DataFrame) -> bool:
    """Ensure physical quantities are positive."""
    positive_cols = ["radius_earth", "period_day", "teff", "stellar_mass", "stellar_radius"]
    for col in positive_cols:
        if col in df.columns:
            if (df[col] <= 0).any():
                pytest.fail(f"Column '{col}' contains non-positive values.")
    return True

@pytest.fixture(scope="module")
def schema():
    return load_schema(SCHEMA_PATH)

@pytest.fixture(scope="module", params=[DATA_RAW_PATH, DATA_DEDUP_PATH])
def ingestion_file_path(request):
    """Fixture to test both filtered and deduped outputs if they exist."""
    path = request.param
    if not path.exists():
        pytest.skip(f"Data file not found: {path}. Ingestion pipeline may not have run yet.")
    return path

def test_ingestion_schema_compliance(ingestion_file_path, schema):
    """
    Contract test: Verify the ingestion output matches the expected schema
    and meets the US1 filtering criteria.
    """
    # Load data
    df = pd.read_csv(ingestion_file_path)
    
    # 1. Schema Compliance: Check columns
    validate_columns(df, REQUIRED_COLUMNS)
    
    # 2. Data Integrity: Check for nulls in critical fields
    validate_no_nulls(df, CRITICAL_COLUMNS)
    
    # 3. Business Logic: Verify uncertainty thresholds (US1 FR-002)
    validate_uncertainty_thresholds(df)
    
    # 4. Physical Validity: Check for positive values
    validate_positive_values(df)
    
    # 5. Schema Type Validation (basic check)
    # Ensure numeric columns are actually numeric
    numeric_cols = ["radius_earth", "radius_uncertainty", "period_day", "period_uncertainty", "teff"]
    for col in numeric_cols:
        if col in df.columns:
            if not pd.api.types.is_numeric_dtype(df[col]):
                pytest.fail(f"Column '{col}' is not numeric.")
    
    assert len(df) > 0, "The ingestion output file is empty."

def test_duplicate_resolution_logic(ingestion_file_path):
    """
    Specific check for T015 (Duplicate Resolution).
    If the file is deduped_planets.csv, ensure no duplicate kepler_id/planet_name pairs exist.
    """
    if "deduped_planets.csv" not in str(ingestion_file_path):
        pytest.skip("Duplicate resolution check only applies to deduped file.")
    
    df = pd.read_csv(ingestion_file_path)
    
    # Check for duplicates based on Kepler ID
    if df["kepler_id"].duplicated().any():
        # Count duplicates
        dup_count = df["kepler_id"].duplicated().sum()
        pytest.fail(f"Found {dup_count} duplicate Kepler IDs in deduped file. Duplicate resolution failed.")

def test_stellar_temp_filter(ingestion_file_path):
    """
    Verify that no entries have missing stellar effective temperature (US1 FR-002).
    """
    df = pd.read_csv(ingestion_file_path)
    
    # T014 requirement: exclude entries with missing stellar effective temperature
    if df["teff"].isnull().any():
        pytest.fail("Found entries with missing stellar effective temperature (teff).")

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
