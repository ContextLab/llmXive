"""
Contract test for period bin output schema (T019).

This test validates that the binned planet data produced by the binning
pipeline adheres to the expected schema defined in the project contracts.
It ensures data integrity before downstream GMM fitting and regression.
"""

import os
import sys
import pytest
import pandas as pd
from pathlib import Path

# Add project root to path for imports if running standalone
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "code"))

from utils.logging_config import get_logger

logger = get_logger(__name__)

# Expected schema definition for binned_planets.csv
# Based on FR-003 and US2 requirements
REQUIRED_COLUMNS = {
    "bin_id": "integer",
    "period_min": "float",
    "period_max": "float",
    "period_center": "float",
    "planet_count": "integer",
    "merged": "boolean",
    "merged_with_bin_id": "integer"
}

# Required columns for the final output used in regression
REGRESSION_COLUMNS = {
    "bin_id",
    "period_center",
    "planet_count",
    "gap_location",
    "gap_location_uncert",
    "status"
}

@pytest.fixture
def binned_data_path():
    """Path to the binned planets output file."""
    return project_root / "data" / "processed" / "binned_planets.csv"

@pytest.fixture
def gap_locations_path():
    """Path to the gap locations output file."""
    return project_root / "data" / "processed" / "gap_locations.csv"

def test_binned_planets_file_exists(binned_data_path):
    """Verify that the binned planets CSV file exists."""
    assert binned_data_path.exists(), f"Expected binned planets file not found at {binned_data_path}"

def test_binned_planets_schema(binned_data_path):
    """
    Verify the schema of binned_planets.csv matches requirements.

    Checks:
    - All required columns are present
    - Column types are appropriate
    - No null values in critical columns
    """
    df = pd.read_csv(binned_data_path)

    # Check required columns
    missing_cols = set(REQUIRED_COLUMNS.keys()) - set(df.columns)
    assert not missing_cols, f"Missing required columns: {missing_cols}"

    # Check for critical non-null constraints
    critical_cols = ["bin_id", "period_min", "period_max", "planet_count"]
    for col in critical_cols:
        null_count = df[col].isnull().sum()
        assert null_count == 0, f"Column '{col}' contains {null_count} null values"

    # Check data types (allow for pandas nullable types)
    assert df["bin_id"].dtype in ["int64", "int32", "object"], "bin_id should be integer-like"
    assert df["planet_count"].dtype in ["int64", "int32", "object"], "planet_count should be integer-like"

    # Verify binning logic: period_min < period_max for all rows
    assert (df["period_min"] < df["period_max"]).all(), "Invalid bin ranges detected (min >= max)"

    # Verify log-spacing consistency (optional but recommended)
    # Check that bin boundaries are roughly log-spaced
    log_mins = np.log10(df["period_min"])
    log_maxs = np.log10(df["period_max"])
    bin_widths = log_maxs - log_mins
    assert bin_widths.std() < 0.5, "Bin widths are highly inconsistent (expected roughly log-spaced)"

def test_gap_locations_schema(gap_locations_path):
    """
    Verify the schema of gap_locations.csv matches requirements.

    This file is produced by T028 (GMM fitting + binning integration).
    """
    if not gap_locations_path.exists():
        pytest.skip("gap_locations.csv not yet generated (T028 not completed)")

    df = pd.read_csv(gap_locations_path)

    # Check required columns for regression
    missing_cols = set(REGRESSION_COLUMNS) - set(df.columns)
    assert not missing_cols, f"Missing required columns for regression: {missing_cols}"

    # Check for nulls in critical numeric columns
    critical_numeric = ["gap_location", "gap_location_uncert", "period_center"]
    for col in critical_numeric:
        null_count = df[col].isnull().sum()
        assert null_count == 0, f"Column '{col}' contains {null_count} null values"

    # Check status column values
    valid_statuses = {"resolved", "unresolved", "unimodal"}
    actual_statuses = set(df["status"].unique())
    invalid_statuses = actual_statuses - valid_statuses
    assert not invalid_statuses, f"Invalid status values found: {invalid_statuses}"

def test_bin_merging_logic(binned_data_path):
    """
    Verify that the bin merging logic (FR-003) was applied correctly.

    If a bin has < 30 planets, it should be marked as merged.
    """
    df = pd.read_csv(binned_data_path)

    # Check that small bins are flagged
    small_bins = df[df["planet_count"] < 30]
    if not small_bins.empty:
        # These bins should be marked as merged
        assert (small_bins["merged"] == True).all(), "Bins with < 30 planets should be marked as merged"

def test_data_integrity_checksum(binned_data_path):
    """
    Verify that the data file has not been corrupted.

    Uses the checksum saved by T016/loaders.py pattern.
    """
    import hashlib
    import json

    checksum_file = binned_data_path.with_suffix(".sha256")

    if not checksum_file.exists():
        logger.warning(f"Checksum file not found at {checksum_file}. Skipping integrity check.")
        pytest.skip("Checksum file missing")

    # Load stored checksum
    with open(checksum_file, "r") as f:
        stored_checksum = json.load(f).get("sha256")

    # Compute current checksum
    with open(binned_data_path, "rb") as f:
        computed_checksum = hashlib.sha256(f.read()).hexdigest()

    assert stored_checksum == computed_checksum, "Data file checksum mismatch - file may be corrupted"