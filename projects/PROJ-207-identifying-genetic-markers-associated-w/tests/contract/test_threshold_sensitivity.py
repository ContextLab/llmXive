"""
Contract test for sensitivity analysis output format.

This test verifies that the threshold sensitivity analysis output
adheres to the expected schema defined in the project specifications.
It ensures the file `data/processed/threshold_sensitivity_report.tsv`
exists and contains the required columns and format.
"""
import os
import sys
import pandas as pd
import pytest
from pathlib import Path

# Project root adjustment for import if running from tests/
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT_DIR / "code"))

OUTPUT_PATH = ROOT_DIR / "data" / "processed" / "threshold_sensitivity_report.tsv"

REQUIRED_COLUMNS = [
    "threshold_log10",
    "threshold_pval",
    "count_significant",
    "count_total",
    "proportion_significant",
    "q_value_5th_percentile"
]

def test_output_file_exists():
    """Verify that the sensitivity report file has been generated."""
    assert OUTPUT_PATH.exists(), f"Output file not found at {OUTPUT_PATH}. " \
        "Ensure code/utils/threshold_sensitivity.py has been executed."

def test_output_has_required_columns():
    """Verify the TSV contains all mandatory columns."""
    if not OUTPUT_PATH.exists():
        pytest.skip("Output file missing, skipping column check.")
    
    df = pd.read_csv(OUTPUT_PATH, sep="\t")
    
    missing_cols = set(REQUIRED_COLUMNS) - set(df.columns)
    assert not missing_cols, f"Missing required columns: {missing_cols}. " \
        f"Found columns: {list(df.columns)}"

def test_output_column_types_and_values():
    """Verify data types and value ranges for the sensitivity report."""
    if not OUTPUT_PATH.exists():
        pytest.skip("Output file missing, skipping value check.")
    
    df = pd.read_csv(OUTPUT_PATH, sep="\t")
    
    # Check numeric columns are numeric
    numeric_cols = [
        "threshold_log10", "threshold_pval", "count_significant", 
        "count_total", "proportion_significant", "q_value_5th_percentile"
    ]
    
    for col in numeric_cols:
        if col in df.columns:
            # Allow for potential NaNs in calculation, but ensure non-NaN are numeric
            non_null = df[col].dropna()
            assert len(non_null) > 0, f"Column {col} is entirely NaN or empty."
            assert non_null.dtype in ['float64', 'int64', 'int32', 'float32', 'float'], \
                f"Column {col} has non-numeric dtype: {non_null.dtype}"

    # Check specific constraints
    if "proportion_significant" in df.columns:
        valid_proportions = df["proportion_significant"].dropna()
        if len(valid_proportions) > 0:
            assert (valid_proportions >= 0).all(), \
                "Proportion significant cannot be negative"
            assert (valid_proportions <= 1).all(), \
                "Proportion significant cannot exceed 1"

def test_output_row_count():
    """Verify that the sensitivity sweep produced multiple data points."""
    if not OUTPUT_PATH.exists():
        pytest.skip("Output file missing, skipping row count check.")
    
    df = pd.read_csv(OUTPUT_PATH, sep="\t")
    # A valid sensitivity analysis should have at least a few thresholds tested
    assert len(df) >= 3, f"Expected at least 3 rows for sensitivity sweep, got {len(df)}"