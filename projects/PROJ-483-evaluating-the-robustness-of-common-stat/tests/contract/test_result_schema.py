"""
Contract test for the output CSV schema of the simulation pipeline.

This test verifies that the generated results file (results/simulation_raw.csv)
adheres to the expected schema defined in the project specifications.

It checks:
1. File existence.
2. Presence of all required columns.
3. Correct data types for each column.
4. Absence of null values in critical columns.
"""
import os
import pandas as pd
import pytest
from pathlib import Path

# Define the expected schema based on the simulation requirements
# Columns: run_id, test_type, dependency_type, dependency_strength, n_samples, p_value, significant
EXPECTED_COLUMNS = {
    "run_id": "int64",
    "test_type": "object",
    "dependency_type": "object",
    "dependency_strength": "float64",
    "n_samples": "int64",
    "p_value": "float64",
    "significant": "bool"
}

REQUIRED_COLUMNS = list(EXPECTED_COLUMNS.keys())

def get_results_path():
    """Locate the results file relative to the project root."""
    # Assuming tests are run from the project root or via pytest --rootdir
    project_root = Path(__file__).resolve().parent.parent.parent
    return project_root / "results" / "simulation_raw.csv"

@pytest.fixture
def results_df():
    """Load the results dataframe if the file exists."""
    path = get_results_path()
    if not path.exists():
        pytest.skip(f"Results file not found at {path}. Run the simulation first.")
    return pd.read_csv(path)

def test_file_exists():
    """Verify the output file exists."""
    path = get_results_path()
    assert path.exists(), f"Results file {path} does not exist."

def test_required_columns_present(results_df):
    """Verify all required columns are present in the dataframe."""
    missing = set(REQUIRED_COLUMNS) - set(results_df.columns)
    assert not missing, f"Missing required columns: {missing}"

def test_column_dtypes(results_df):
    """Verify data types match the expected schema."""
    for col, expected_type in EXPECTED_COLUMNS.items():
        if col in results_df.columns:
            # Pandas sometimes infers object for strings, int64 for ints, etc.
            # We check the underlying numpy dtype category
            actual_dtype = str(results_df[col].dtype)
            
            # Map pandas specific types to expected string representations
            type_mapping = {
                "int64": ["int64", "Int64"],
                "float64": ["float64", "Float64"],
                "object": ["object", "string"],
                "bool": ["bool", "boolean"]
            }
            
            valid_types = type_mapping.get(expected_type, [expected_type])
            assert actual_dtype in valid_types, (
                f"Column '{col}' has dtype '{actual_dtype}', expected '{expected_type}'"
            )

def test_no_nulls_in_required_columns(results_df):
    """Verify critical columns do not contain null values."""
    for col in REQUIRED_COLUMNS:
        if col in results_df.columns:
            null_count = results_df[col].isnull().sum()
            assert null_count == 0, f"Column '{col}' contains {null_count} null values."

def test_test_type_values(results_df):
    """Verify 'test_type' contains only expected test names."""
    valid_types = {"t-test", "anova", "chi-squared"}
    found_types = set(results_df["test_type"].unique())
    invalid = found_types - valid_types
    assert not invalid, f"Unexpected test types found: {invalid}"

def test_dependency_type_values(results_df):
    """Verify 'dependency_type' contains only expected structures."""
    valid_types = {"AR(1)", "Block Bootstrap", "Spatial Kernel"}
    found_types = set(results_df["dependency_type"].unique())
    # Allow for empty sets if no data yet, but if data exists, it must match
    if found_types:
        invalid = found_types - valid_types
        assert not invalid, f"Unexpected dependency types found: {invalid}"

def test_dependency_strength_range(results_df):
    """Verify dependency strength is within valid range [0, 0.9]."""
    if "dependency_strength" in results_df.columns:
        min_val = results_df["dependency_strength"].min()
        max_val = results_df["dependency_strength"].max()
        assert min_val >= 0.0, f"Dependency strength minimum {min_val} is below 0."
        assert max_val <= 0.9, f"Dependency strength maximum {max_val} exceeds 0.9."

def test_p_value_range(results_df):
    """Verify p-values are within [0, 1]."""
    if "p_value" in results_df.columns:
        min_val = results_df["p_value"].min()
        max_val = results_df["p_value"].max()
        assert min_val >= 0.0, f"P-value minimum {min_val} is below 0."
        assert max_val <= 1.0, f"P-value maximum {max_val} exceeds 1."

def test_significant_logic(results_df):
    """Verify 'significant' column is boolean and consistent with p-value (alpha=0.05)."""
    if "significant" in results_df.columns and "p_value" in results_df.columns:
        alpha = 0.05
        # Recalculate expected significant flag
        expected_significant = results_df["p_value"] < alpha
        # Compare with actual column
        assert results_df["significant"].equals(expected_significant), (
            "The 'significant' column does not match the logic (p_value < 0.05)."
        )