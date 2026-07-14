"""
Contract tests for the sensitivity analysis results schema.

This module validates that the output of `code/analysis/sensitivity.py`
adheres to the expected schema defined in the project specifications.
It ensures that the sensitivity results file (`data/results/sensitivity_analysis.csv`)
contains all required columns, correct data types, and valid value ranges.
"""

import os
import pytest
import pandas as pd
from pathlib import Path

# Path to the expected output file
# This path is relative to the project root.
EXPECTED_OUTPUT_PATH = Path("data/results/sensitivity_analysis.csv")

# Required columns as per the specification for sensitivity analysis
# The file should contain results from re-fitting models with continuous harassment
# severity and stratified by platform.
REQUIRED_COLUMNS = [
    "model_type",          # e.g., 'continuous_severity', 'stratified_platform'
    "outcome_variable",    # e.g., 'depression', 'anxiety', 'ptsd'
    "platform",            # e.g., 'twitter', 'reddit', 'Other', or 'all'
    "predictor",           # e.g., 'social_support', 'harassment_severity', 'interaction'
    "coefficient",         # Float: The estimated coefficient
    "std_err",             # Float: Standard error
    "p_value",             # Float: P-value
    "ci_lower",            # Float: Lower bound of CI
    "ci_upper",            # Float: Upper bound of CI
    "n_obs",               # Int: Number of observations used
    "baseline_coefficient", # Float: The corresponding coefficient from the baseline model (T020)
    "coefficient_shift",   # Float: Difference between sensitivity and baseline
]

# Expected data types for each column
EXPECTED_DTYPE_MAP = {
    "model_type": object,
    "outcome_variable": object,
    "platform": object,
    "predictor": object,
    "coefficient": float,
    "std_err": float,
    "p_value": float,
    "ci_lower": float,
    "ci_upper": float,
    "n_obs": int,
    "baseline_coefficient": float,
    "coefficient_shift": float,
}

# Constraints for numeric columns
NUMERIC_CONSTRAINTS = {
    "p_value": (0.0, 1.0),
    "coefficient": (None, None),  # No specific range, but must be numeric
    "std_err": (0.0, None),       # Must be non-negative
    "ci_lower": (None, None),
    "ci_upper": (None, None),
    "n_obs": (1, None),           # Must be positive
    "baseline_coefficient": (None, None),
    "coefficient_shift": (None, None),
}


def get_sensitivity_results() -> pd.DataFrame:
    """
    Loads the sensitivity analysis results from the expected output path.
    
    Returns:
        pd.DataFrame: The loaded results.
    
    Raises:
        FileNotFoundError: If the output file does not exist.
        ValueError: If the file cannot be parsed as CSV.
    """
    if not EXPECTED_OUTPUT_PATH.exists():
        raise FileNotFoundError(
            f"Sensitivity results file not found at {EXPECTED_OUTPUT_PATH}. "
            "Ensure T027-T029 have been executed successfully."
        )
    
    try:
        return pd.read_csv(EXPECTED_OUTPUT_PATH)
    except Exception as e:
        raise ValueError(f"Failed to parse sensitivity results CSV: {e}")


class TestSensitivityResultsSchema:
    """
    Contract tests for the sensitivity analysis results schema.
    """

    def test_file_exists(self):
        """Test that the sensitivity results file exists."""
        assert EXPECTED_OUTPUT_PATH.exists(), (
            f"Contract failed: {EXPECTED_OUTPUT_PATH} does not exist. "
            "The sensitivity analysis script (T027-T029) must be run first."
        )

    def test_required_columns_present(self):
        """Test that all required columns are present in the results."""
        df = get_sensitivity_results()
        missing_cols = set(REQUIRED_COLUMNS) - set(df.columns)
        assert not missing_cols, (
            f"Contract failed: Missing required columns: {missing_cols}. "
            f"Found columns: {list(df.columns)}"
        )

    def test_column_data_types(self):
        """Test that columns have the expected data types."""
        df = get_sensitivity_results()
        errors = []
        for col, expected_type in EXPECTED_DTYPE_MAP.items():
            if col in df.columns:
                actual_type = df[col].dtype
                # Handle object vs string nuances
                if expected_type == object and actual_type == object:
                    continue
                # Allow int to float conversion if necessary, but strict for others
                if expected_type == int and actual_type == float:
                    # Check if they are actually integers
                    if not df[col].eq(df[col].astype(int)).all():
                        errors.append(f"Column '{col}' should be int, found float with non-integer values.")
                    continue
                if expected_type == float and actual_type == int:
                    # Int can be cast to float
                    continue
                
                if actual_type != expected_type:
                    errors.append(
                        f"Column '{col}' expected {expected_type}, got {actual_type}"
                    )
        
        assert not errors, "Contract failed on data types:\n" + "\n".join(errors)

    def test_numeric_constraints(self):
        """Test that numeric columns satisfy value constraints."""
        df = get_sensitivity_results()
        errors = []
        
        for col, (min_val, max_val) in NUMERIC_CONSTRAINTS.items():
            if col not in df.columns:
                continue
            
            values = df[col].dropna()
            if values.empty:
                errors.append(f"Column '{col}' has no valid numeric values.")
                continue

            if min_val is not None:
                if (values < min_val).any():
                    errors.append(
                        f"Column '{col}' contains values < {min_val}."
                    )
            if max_val is not None:
                if (values > max_val).any():
                    errors.append(
                        f"Column '{col}' contains values > {max_val}."
                    )
        
        assert not errors, "Contract failed on numeric constraints:\n" + "\n".join(errors)

    def test_model_types_valid(self):
        """Test that model_type column contains expected values."""
        df = get_sensitivity_results()
        valid_model_types = {"continuous_severity", "stratified_platform"}
        actual_types = set(df["model_type"].unique())
        invalid_types = actual_types - valid_model_types
        assert not invalid_types, (
            f"Contract failed: Invalid model types found: {invalid_types}. "
            f"Expected one of {valid_model_types}."
        )

    def test_outcome_variables_valid(self):
        """Test that outcome_variable column contains expected values."""
        df = get_sensitivity_results()
        valid_outcomes = {"depression", "anxiety", "ptsd"}
        actual_outcomes = set(df["outcome_variable"].str.lower().unique())
        invalid_outcomes = actual_outcomes - valid_outcomes
        assert not invalid_outcomes, (
            f"Contract failed: Invalid outcome variables found: {invalid_outcomes}. "
            f"Expected one of {valid_outcomes}."
        )

    def test_no_duplicate_rows(self):
        """Test that there are no exact duplicate rows in the results."""
        df = get_sensitivity_results()
        duplicates = df.duplicated().sum()
        assert duplicates == 0, (
            f"Contract failed: Found {duplicates} duplicate rows in the results."
        )

    def test_coefficient_shift_calculation(self):
        """
        Verify that coefficient_shift is consistent with coefficient and baseline_coefficient.
        Expected: coefficient_shift = coefficient - baseline_coefficient
        """
        df = get_sensitivity_results()
        # Allow for small floating point errors
        expected_shift = df["coefficient"] - df["baseline_coefficient"]
        actual_shift = df["coefficient_shift"]
        
        if not actual_shift.isna().all() and not expected_shift.isna().all():
            is_consistent = pd.testing.assert_series_equal(
                actual_shift, 
                expected_shift, 
                check_names=False
            ) is None
            
            # If assert_series_equal doesn't raise, it's consistent.
            # We do a manual check for NaN handling to be safe
            mask = ~actual_shift.isna() & ~expected_shift.isna()
            if mask.any():
                diff = (actual_shift[mask] - expected_shift[mask]).abs()
                if (diff > 1e-6).any():
                    pytest.fail("coefficient_shift does not match coefficient - baseline_coefficient")