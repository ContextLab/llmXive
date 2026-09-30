import os
import sys
import pytest
import pandas as pd
from pathlib import Path

# Add project root to path to allow imports if needed, though this test is standalone
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "code"))

FEATURE_FILE = PROJECT_ROOT / "data" / "processed" / "features.csv"

REQUIRED_COLUMNS = [
    "participant_id",
    "median_rt",
    "delta_rel",
    "theta_rel",
    "alpha_rel",
    "low_beta_rel",
    "high_beta_rel",
    "gamma_rel",
]

# Plausible response time range in milliseconds (100ms to 2000ms based on T013 logic)
# T013 filters RT < 100ms and RT > 2000ms.
MIN_PLAUSIBLE_RT = 100.0
MAX_PLAUSIBLE_RT = 2000.0

def test_feature_file_exists():
    """Assert that the features.csv file exists at the expected path."""
    assert FEATURE_FILE.exists(), f"Feature file not found at {FEATURE_FILE}"

def test_feature_schema_columns():
    """Assert that all required columns exist in the features.csv file."""
    if not FEATURE_FILE.exists():
        pytest.skip("Feature file does not exist yet.")
    
    df = pd.read_csv(FEATURE_FILE)
    missing_cols = set(REQUIRED_COLUMNS) - set(df.columns)
    assert not missing_cols, f"Missing required columns: {missing_cols}"

def test_feature_schema_no_nulls():
    """Assert that no values in the required columns are null."""
    if not FEATURE_FILE.exists():
        pytest.skip("Feature file does not exist yet.")
    
    df = pd.read_csv(FEATURE_FILE)
    for col in REQUIRED_COLUMNS:
        if col in df.columns:
            null_count = df[col].isnull().sum()
            assert null_count == 0, f"Column '{col}' contains {null_count} null values."

def test_feature_schema_median_rt_range():
    """Assert that median_rt values are within a plausible response time range."""
    if not FEATURE_FILE.exists():
        pytest.skip("Feature file does not exist yet.")
    
    df = pd.read_csv(FEATURE_FILE)
    assert "median_rt" in df.columns, "Column 'median_rt' is missing."
    
    rt_values = df["median_rt"]
    out_of_range = rt_values[(rt_values < MIN_PLAUSIBLE_RT) | (rt_values > MAX_PLAUSIBLE_RT)]
    
    assert len(out_of_range) == 0, (
        f"Found {len(out_of_range)} median_rt values outside the plausible range "
        f"[{MIN_PLAUSIBLE_RT}, {MAX_PLAUSIBLE_RT}]. Values: {out_of_range.tolist()}"
    )

def test_feature_schema_data_types():
    """Assert that numeric columns are numeric and participant_id is string/object."""
    if not FEATURE_FILE.exists():
        pytest.skip("Feature file does not exist yet.")
    
    df = pd.read_csv(FEATURE_FILE)
    
    # Check participant_id is not numeric (should be string)
    assert not pd.api.types.is_numeric_dtype(df["participant_id"]), \
        "Column 'participant_id' should be string/object, not numeric."
    
    # Check numeric columns are numeric
    numeric_cols = [c for c in REQUIRED_COLUMNS if c != "participant_id"]
    for col in numeric_cols:
        if col in df.columns:
            assert pd.api.types.is_numeric_dtype(df[col]), \
                f"Column '{col}' should be numeric, but is {df[col].dtype}."
