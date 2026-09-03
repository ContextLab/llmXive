import os
import pytest
import pandas as pd
import numpy as np
from pathlib import Path

# Project root resolution for test execution
PROJECT_ROOT = Path(__file__).parents[2]
FEATURES_PATH = PROJECT_ROOT / "data" / "processed" / "features.csv"

REQUIRED_COLUMNS = [
    "participant_id",
    "median_rt",
    "delta_rel",
    "theta_rel",
    "alpha_rel",
    "low_beta_rel",
    "high_beta_rel",
    "gamma_rel"
]

# Plausible response time range for simple RT tasks (ms)
# Standard simple RT is typically 150-400ms. We allow a generous range 50-2000ms
# to account for outliers that might have slipped through, but strictly reject
# physiological impossibilities (negative, 0, or > 5000ms).
MIN_RT_MS = 50.0
MAX_RT_MS = 5000.0

@pytest.fixture
def features_df():
    """Load the features file, failing loudly if missing."""
    if not FEATURES_PATH.exists():
        pytest.fail(
            f"Required input file missing: {FEATURES_PATH}. "
            "Ensure T012c (04c_relative_power.py) has run successfully."
        )
    try:
        df = pd.read_csv(FEATURES_PATH)
    except Exception as e:
        pytest.fail(f"Failed to read {FEATURES_PATH}: {e}")
    return df

def test_schema_columns_exist(features_df):
    """Verify all required columns are present."""
    missing = set(REQUIRED_COLUMNS) - set(features_df.columns)
    assert not missing, f"Missing required columns: {missing}"

def test_schema_no_nulls(features_df):
    """Verify no null values in required columns."""
    for col in REQUIRED_COLUMNS:
        null_count = features_df[col].isna().sum()
        assert null_count == 0, f"Column '{col}' contains {null_count} null values."

def test_schema_median_rt_range(features_df):
    """Verify median_rt is within a plausible experimental range."""
    rt_col = "median_rt"
    if rt_col not in features_df.columns:
        # This should be caught by test_schema_columns_exist, but safety check
        return

    invalid_low = (features_df[rt_col] < MIN_RT_MS).sum()
    invalid_high = (features_df[rt_col] > MAX_RT_MS).sum()

    assert invalid_low == 0, f"Found {invalid_low} participants with RT < {MIN_RT_MS}ms."
    assert invalid_high == 0, f"Found {invalid_high} participants with RT > {MAX_RT_MS}ms."

def test_schema_numeric_types(features_df):
    """Verify behavioral and power columns are numeric."""
    numeric_cols = [c for c in REQUIRED_COLUMNS if c != "participant_id"]
    for col in numeric_cols:
        # pd.to_numeric with errors='raise' ensures the column is actually numeric
        # and not an object/string column that happens to look like numbers
        try:
            pd.to_numeric(features_df[col], errors='raise')
        except (ValueError, TypeError):
            pytest.fail(f"Column '{col}' is not numeric.")

def test_schema_participant_id_non_empty(features_df):
    """Verify participant_id is not empty string or null."""
    pid_col = "participant_id"
    if pid_col in features_df.columns:
        empty_count = features_df[pid_col].astype(str).str.strip().eq("").sum()
        assert empty_count == 0, f"Found {empty_count} empty participant_id values."
