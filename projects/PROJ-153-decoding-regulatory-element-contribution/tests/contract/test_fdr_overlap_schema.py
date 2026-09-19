"""
Contract test for T041: FDR Overlap Analysis Output Schema.
Verifies that results/fdr_overlap_stats.csv matches the expected schema.
"""
import os
import pytest
import pandas as pd

OUTPUT_PATH = "results/fdr_overlap_stats.csv"

REQUIRED_COLUMNS = ["stress", "threshold_a", "threshold_b", "overlap_percentage"]
EXPECTED_STRESSES = ["heat-shock", "osmotic", "oxidative"]  # Based on manifest/research.md
VALID_THRESHOLDS = [0.01, 0.05, 0.10]

def test_output_file_exists():
    """Assert that the output file is generated."""
    assert os.path.exists(OUTPUT_PATH), f"Output file {OUTPUT_PATH} not found. Run T041 first."

def test_schema_columns():
    """Assert that all required columns are present."""
    df = pd.read_csv(OUTPUT_PATH)
    assert set(REQUIRED_COLUMNS).issubset(set(df.columns)), \
        f"Missing columns. Found: {list(df.columns)}, Required: {REQUIRED_COLUMNS}"

def test_schema_types():
    """Assert that columns have correct data types."""
    df = pd.read_csv(OUTPUT_PATH)
    assert df["stress"].dtype == object, "Column 'stress' should be string/object."
    assert pd.api.types.is_numeric_dtype(df["threshold_a"]), "Column 'threshold_a' should be numeric."
    assert pd.api.types.is_numeric_dtype(df["threshold_b"]), "Column 'threshold_b' should be numeric."
    assert pd.api.types.is_numeric_dtype(df["overlap_percentage"]), "Column 'overlap_percentage' should be numeric."

def test_threshold_values():
    """Assert that threshold values match the defined set."""
    df = pd.read_csv(OUTPUT_PATH)
    valid_th = set(VALID_THRESHOLDS)
    found_th = set(df["threshold_a"].unique()) | set(df["threshold_b"].unique())
    invalid = found_th - valid_th
    assert len(invalid) == 0, f"Invalid threshold values found: {invalid}. Expected only {VALID_THRESHOLDS}."

def test_overlap_range():
    """Assert that overlap percentages are between 0 and 100."""
    df = pd.read_csv(OUTPUT_PATH)
    assert (df["overlap_percentage"] >= 0).all(), "Overlap percentage cannot be negative."
    assert (df["overlap_percentage"] <= 100).all(), "Overlap percentage cannot exceed 100."

def test_diagonal_overlap():
    """Assert that overlap of a threshold with itself is 100% (or N/A if empty sets)."""
    df = pd.read_csv(OUTPUT_PATH)
    # Filter for diagonal comparisons (threshold_a == threshold_b)
    diagonal = df[df["threshold_a"] == df["threshold_b"]]
    # If there are results, they should be 100% overlap with themselves
    if not diagonal.empty:
        assert (diagonal["overlap_percentage"] == 100.0).all(), \
            "Self-overlap (threshold vs itself) must be 100% if CREs exist."