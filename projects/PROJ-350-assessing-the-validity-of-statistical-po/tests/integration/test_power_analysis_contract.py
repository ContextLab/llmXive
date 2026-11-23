"""
Contract test for T022: Verify data/derived/power_analysis.csv schema and data types.

This test ensures that the power analysis output file:
1. Exists at the expected path.
2. Contains the required columns as defined in the project specification.
3. Has correct data types for each column.
4. Contains no null values in critical fields.
"""
import os
import pandas as pd
import pytest
from pathlib import Path

# Expected output path relative to project root
OUTPUT_PATH = Path("data/derived/power_analysis.csv")

# Required columns based on US2 implementation (T023-T026)
# These are the columns expected in the final power_analysis.csv
REQUIRED_COLUMNS = [
    "study_id",
    "field",
    "effect_size_domain",
    "planned_power",
    "actual_sample_size",
    "assumed_effect_size",
    "sensitivity_power",
    "power_gap",
    "valid_power_calc"
]

# Column data type expectations
# (column_name, expected_dtype_category)
# We check categories rather than exact dtypes to allow for pandas variations
EXPECTED_DTYPE_CATEGORIES = {
    "study_id": "object",      # String identifier
    "field": "object",         # Categorical string
    "effect_size_domain": "object", # Categorical string
    "planned_power": "float64",     # Numeric probability
    "actual_sample_size": "int64",  # Integer count
    "assumed_effect_size": "float64", # Numeric effect size
    "sensitivity_power": "float64", # Numeric probability
    "power_gap": "float64",         # Numeric difference
    "valid_power_calc": "bool"      # Boolean flag
}

@pytest.fixture
def power_analysis_df():
    """Load the power analysis CSV file for testing."""
    if not OUTPUT_PATH.exists():
        pytest.fail(f"Output file not found: {OUTPUT_PATH}. "
                   "Run the power calculation pipeline first.")
    
    try:
        df = pd.read_csv(OUTPUT_PATH)
    except Exception as e:
        pytest.fail(f"Failed to load CSV: {e}")
    
    return df

def test_file_exists():
    """Verify the output file exists."""
    assert OUTPUT_PATH.exists(), f"File {OUTPUT_PATH} does not exist"

def test_required_columns_present(power_analysis_df):
    """Verify all required columns are present in the DataFrame."""
    missing_cols = set(REQUIRED_COLUMNS) - set(power_analysis_df.columns)
    assert not missing_cols, f"Missing required columns: {missing_cols}"

def test_column_data_types(power_analysis_df):
    """Verify data types match expectations."""
    errors = []
    for col, expected_cat in EXPECTED_DTYPE_CATEGORIES.items():
        if col not in power_analysis_df.columns:
            continue  # Already caught by column presence test
        
        actual_dtype = str(power_analysis_df[col].dtype)
        if actual_dtype != expected_cat:
            errors.append(
                f"Column '{col}': expected {expected_cat}, got {actual_dtype}"
            )
    
    assert not errors, "Data type mismatches found:\n" + "\n".join(errors)

def test_no_null_critical_fields(power_analysis_df):
    """Verify no null values in critical calculation fields."""
    critical_fields = [
        "planned_power",
        "actual_sample_size",
        "assumed_effect_size",
        "sensitivity_power",
        "power_gap"
    ]
    
    for field in critical_fields:
        if field in power_analysis_df.columns:
            null_count = power_analysis_df[field].isnull().sum()
            assert null_count == 0, (
                f"Column '{field}' contains {null_count} null values"
            )

def test_power_gap_calculation_consistency(power_analysis_df):
    """Verify power_gap is correctly calculated as planned_power - sensitivity_power."""
    if "power_gap" not in power_analysis_df.columns:
        pytest.skip("power_gap column missing")
    
    # Allow small floating point tolerance
    expected_gap = power_analysis_df["planned_power"] - power_analysis_df["sensitivity_power"]
    actual_gap = power_analysis_df["power_gap"]
    
    # Check if values are close within tolerance
    tolerance = 1e-10
    if not actual_gap.equals(expected_gap):
        # Check if they are close
        close_match = pd.testing.assert_series_equal(
            actual_gap, 
            expected_gap, 
            rtol=tolerance, 
            atol=tolerance,
            check_names=False
        ) is None
        assert close_match, "power_gap values do not match planned_power - sensitivity_power"

def test_valid_power_calc_filtering(power_analysis_df):
    """Verify that valid_power_calc boolean field is present and logical."""
    if "valid_power_calc" not in power_analysis_df.columns:
        pytest.skip("valid_power_calc column missing")
    
    # All values should be boolean
    assert power_analysis_df["valid_power_calc"].dtype == "bool", (
        "valid_power_calc should be boolean"
    )
    
    # If valid_power_calc is False, power_gap should still be calculable
    # (The filtering happens at a higher level, not in this file)

def test_sample_size_positive(power_analysis_df):
    """Verify actual_sample_size is positive where present."""
    if "actual_sample_size" in power_analysis_df.columns:
        zero_or_negative = (power_analysis_df["actual_sample_size"] <= 0).sum()
        assert zero_or_negative == 0, (
            f"Found {zero_or_negative} non-positive sample sizes"
        )

def test_power_values_in_range(power_analysis_df):
    """Verify power values are within valid probability range [0, 1]."""
    power_columns = ["planned_power", "sensitivity_power"]
    
    for col in power_columns:
        if col in power_analysis_df.columns:
            out_of_range = (
                (power_analysis_df[col] < 0) | 
                (power_analysis_df[col] > 1)
            ).sum()
            assert out_of_range == 0, (
                f"Column '{col}' has {out_of_range} values outside [0, 1]"
            )