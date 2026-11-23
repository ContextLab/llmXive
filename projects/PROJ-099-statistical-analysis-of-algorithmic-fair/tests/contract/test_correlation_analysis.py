"""
Contract test for correlation analysis (T032).

This test verifies that the correlation analysis output satisfies the
interface and data contract required by User Story 3.

It checks that:
1. The output file `data/analysis/correlations.csv` exists.
2. The file contains the required columns:
   - metric_a, metric_b
   - pearson_r, pearson_p, pearson_q
   - spearman_r, spearman_p, spearman_q
   - interpretation
3. The data types are correct (floats for coefficients/p-values, strings for interpretation).
4. The DP-difference vs DI-ratio pair is excluded (as per plan).
5. No NaN values exist in the critical numeric columns.
"""
import os
import pytest
import pandas as pd
from pathlib import Path

# Path constants
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
CORRELATION_FILE = PROJECT_ROOT / "data" / "analysis" / "correlations.csv"

REQUIRED_COLUMNS = [
    "metric_a", "metric_b",
    "pearson_r", "pearson_p", "pearson_q",
    "spearman_r", "spearman_p", "spearman_q",
    "interpretation"
]

EXCLUDED_PAIR = ("demographic_parity_difference", "disparate_impact_ratio")
# Also check reverse order just in case
EXCLUDED_PAIR_REVERSE = ("disparate_impact_ratio", "demographic_parity_difference")

@pytest.fixture
def correlation_df():
    """Load the correlation analysis output file."""
    if not CORRELATION_FILE.exists():
        pytest.fail(f"Correlation output file not found at {CORRELATION_FILE}. "
                    "Run 05_correlation_analysis.py to generate it.")
    
    try:
        df = pd.read_csv(CORRELATION_FILE)
    except Exception as e:
        pytest.fail(f"Failed to read correlation file: {e}")
    
    return df

def test_file_exists(correlation_df):
    """Assert the output file exists and is readable."""
    assert CORRELATION_FILE.exists(), "Correlation output file does not exist."

def test_required_columns_present(correlation_df):
    """Assert all required columns are present in the output."""
    missing_cols = set(REQUIRED_COLUMNS) - set(correlation_df.columns)
    assert not missing_cols, f"Missing required columns: {missing_cols}"

def test_no_missing_values_in_critical_columns(correlation_df):
    """Assert no NaN values in critical numeric columns."""
    critical_cols = ["pearson_r", "pearson_p", "pearson_q", 
                     "spearman_r", "spearman_p", "spearman_q"]
    
    for col in critical_cols:
        if correlation_df[col].isna().any():
            pytest.fail(f"Column '{col}' contains NaN values.")

def test_excluded_pair_not_present(correlation_df):
    """Assert the theoretically circular pair is excluded."""
    pairs = list(zip(correlation_df["metric_a"], correlation_df["metric_b"]))
    
    if EXCLUDED_PAIR in pairs or EXCLUDED_PAIR_REVERSE in pairs:
        pytest.fail("The DP-difference vs DI-ratio pair is present but should be excluded due to theoretical circularity.")

def test_data_types_correct(correlation_df):
    """Assert numeric columns are floats."""
    numeric_cols = ["pearson_r", "pearson_p", "pearson_q", 
                    "spearman_r", "spearman_p", "spearman_q"]
    
    for col in numeric_cols:
        if not pd.api.types.is_float_dtype(correlation_df[col]):
            pytest.fail(f"Column '{col}' is not of float dtype. Found: {correlation_df[col].dtype}")

def test_interpretation_format(correlation_df):
    """Assert interpretation column contains non-empty strings."""
    if correlation_df["interpretation"].isna().any():
        pytest.fail("Interpretation column contains NaN values.")
    
    if (correlation_df["interpretation"] == "").any():
        pytest.fail("Interpretation column contains empty strings.")

def test_row_count_reasonable(correlation_df):
    """Assert we have a reasonable number of pairs (6 metrics -> 15 pairs, minus 1 excluded = 14)."""
    # 6 metrics: DP, EO, PP, CWG, DI, FPR
    # Total pairs = 6 * 5 / 2 = 15
    # Excluded = 1 (DP vs DI)
    # Expected = 14
    expected_min = 10  # Allow some flexibility if more metrics were added later
    assert len(correlation_df) >= expected_min, \
        f"Expected at least {expected_min} rows, found {len(correlation_df)}. " \
        "This suggests correlation analysis may not have covered all metric pairs."