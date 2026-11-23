"""
Contract test for sensitivity report schema (T031).

Validates that `results/sensitivity_sweep.csv` conforms to the expected
schema and contains the required columns and data types mandated by
User Story 3 (FR-007, FR-008, SC-004).
"""
import os
import sys
import json
import pytest
import pandas as pd
from pathlib import Path

# Add project root to path for imports if necessary
PROJECT_ROOT = Path(__file__).resolve().parents[2]
RESULTS_DIR = PROJECT_ROOT / "results"
SENSITIVITY_FILE = RESULTS_DIR / "sensitivity_sweep.csv"

# Expected schema definition based on T033 and contracts
EXPECTED_COLUMNS = [
    "threshold",
    "r",
    "rho",
    "mae",
    "p_value",
    "bonferroni_corrected_p"
]

# Thresholds mandated by FR-007
EXPECTED_THRESHOLDS = [0.5, 0.6, 0.7]

class TestSensitivityReportSchema:
    """
    Contract tests ensuring the sensitivity analysis output matches the spec.
    """

    def test_file_exists(self):
        """
        Verify that the sensitivity sweep file exists.
        """
        assert SENSITIVITY_FILE.exists(), (
            f"Sensitivity report not found at {SENSITIVITY_FILE}. "
            "Ensure code/sensitivity.py has been executed successfully."
        )

    def test_schema_columns_present(self):
        """
        Verify that all required columns are present in the CSV.
        """
        df = pd.read_csv(SENSITIVITY_FILE)
        missing_cols = set(EXPECTED_COLUMNS) - set(df.columns)
        assert not missing_cols, (
            f"Missing required columns in sensitivity report: {missing_cols}. "
            f"Expected: {EXPECTED_COLUMNS}"
        )

    def test_column_data_types(self):
        """
        Verify that numeric columns contain numeric data.
        """
        df = pd.read_csv(SENSITIVITY_FILE)
        
        numeric_cols = ["r", "rho", "mae", "p_value", "bonferroni_corrected_p"]
        for col in numeric_cols:
            if col in df.columns:
                # Check if column is numeric (or can be cast to numeric)
                try:
                    pd.to_numeric(df[col], errors='raise')
                except (ValueError, TypeError):
                    pytest.fail(f"Column '{col}' contains non-numeric data.")

    def test_threshold_values(self):
        """
        Verify that the threshold column contains exactly the mandated values {0.5, 0.6, 0.7}.
        """
        df = pd.read_csv(SENSITIVITY_FILE)
        actual_thresholds = sorted(df["threshold"].unique().tolist())
        expected_sorted = sorted(EXPECTED_THRESHOLDS)
        
        assert actual_thresholds == expected_sorted, (
            f"Threshold values mismatch. Found: {actual_thresholds}, "
            f"Expected: {expected_sorted}."
        )

    def test_bonferroni_logic(self):
        """
        Verify that bonferroni_corrected_p is consistent with p_value * 3 (capped at 1.0).
        FR-008 mandates: multiply raw p-value by the number of tests (3) and cap at 1.0.
        """
        df = pd.read_csv(SENSITIVITY_FILE)
        
        # Calculate expected corrected p-values
        df["expected_corrected"] = (df["p_value"] * 3).clip(upper=1.0)
        
        # Compare with actual, allowing small floating point tolerance
        tolerance = 1e-6
        mismatch_count = 0
        for idx, row in df.iterrows():
            actual = row["bonferroni_corrected_p"]
            expected = row["expected_corrected"]
            if abs(actual - expected) > tolerance:
                mismatch_count += 1
        
        assert mismatch_count == 0, (
            f"Bonferroni correction logic mismatch in {mismatch_count} rows. "
            "Expected: p_value * 3 (capped at 1.0)."
        )

    def test_valid_range_metrics(self):
        """
        Verify that correlation metrics (r, rho) are within [-1, 1] and MAE/P-values are non-negative.
        """
        df = pd.read_csv(SENSITIVITY_FILE)
        
        # Check correlation range
        assert df["r"].between(-1.0, 1.0).all(), "Pearson r values outside [-1, 1]."
        assert df["rho"].between(-1.0, 1.0).all(), "Spearman rho values outside [-1, 1]."
        
        # Check non-negative metrics
        assert (df["mae"] >= 0).all(), "MAE values are negative."
        assert (df["p_value"] >= 0).all(), "p_values are negative."
        assert (df["bonferroni_corrected_p"] >= 0).all(), "Bonferroni corrected p_values are negative."

    def test_no_missing_values(self):
        """
        Verify that there are no NaN values in the critical columns.
        """
        df = pd.read_csv(SENSITIVITY_FILE)
        assert df[EXPECTED_COLUMNS].isnull().sum().sum() == 0, (
            "Sensitivity report contains missing values in critical columns."
        )