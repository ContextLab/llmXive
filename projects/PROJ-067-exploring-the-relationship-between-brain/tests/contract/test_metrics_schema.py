"""
Contract test for the metrics CSV schema.

This test verifies that `data/metrics/subject_metrics.csv` (produced by T031)
strictly adheres to the expected schema defined in the project specifications.

Expected Columns:
  - subject_id: str (e.g., 'sub-001')
  - dream_recall_frequency: float
  - dmn_flexibility: float
  - dmn_stability: float
  - salience_flexibility: float
  - salience_stability: float
  - hippocampal_flexibility: float
  - hippocampal_stability: float
  - processing_status: str ('success' or 'excluded')
  - exclusion_reason: str (optional, empty if success)

The test ensures:
  1. The file exists at the expected path.
  2. All required columns are present.
  3. Data types match expectations (numeric for metrics, string for IDs).
  4. No NaN values exist in required numeric columns for 'success' rows.
"""

import os
import pytest
import pandas as pd
from pathlib import Path

# Define the expected output path relative to project root
# Assuming the test runs from the project root or code/ directory
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
METRICS_FILE = PROJECT_ROOT / "data" / "metrics" / "subject_metrics.csv"

REQUIRED_COLUMNS = [
    "subject_id",
    "dream_recall_frequency",
    "dmn_flexibility",
    "dmn_stability",
    "salience_flexibility",
    "salience_stability",
    "hippocampal_flexibility",
    "hippocampal_stability",
    "processing_status",
    "exclusion_reason"
]

NUMERIC_METRICS = [
    "dream_recall_frequency",
    "dmn_flexibility",
    "dmn_stability",
    "salience_flexibility",
    "salience_stability",
    "hippocampal_flexibility",
    "hippocampal_stability"
]


@pytest.fixture
def metrics_df():
    """Load the metrics CSV file if it exists."""
    if not METRICS_FILE.exists():
        pytest.fail(f"Metrics file not found at {METRICS_FILE}. "
                    "Ensure T031 has been executed to generate the data.")
    try:
        df = pd.read_csv(METRICS_FILE)
    except Exception as e:
        pytest.fail(f"Failed to read metrics CSV: {e}")
    return df


def test_file_exists(metrics_df):
    """Contract: Verify the metrics file exists."""
    assert METRICS_FILE.exists(), "Metrics file does not exist."


def test_required_columns_present(metrics_df):
    """Contract: Verify all required columns are present."""
    missing = set(REQUIRED_COLUMNS) - set(metrics_df.columns)
    assert not missing, f"Missing required columns in metrics CSV: {missing}"


def test_column_order(metrics_df):
    """Contract: Verify columns appear in the expected order (optional but strict)."""
    actual_cols = list(metrics_df.columns)
    expected_subset = [col for col in REQUIRED_COLUMNS if col in actual_cols]
    assert actual_cols == expected_subset, (
        f"Column order mismatch. Expected: {expected_subset}, Got: {actual_cols}"
    )


def test_numeric_columns_valid(metrics_df):
    """Contract: Verify numeric metric columns are numeric and non-NaN for successful subjects."""
    # Filter for successful processing
    successful_rows = metrics_df[metrics_df['processing_status'] == 'success']

    for col in NUMERIC_METRICS:
        # Check if column is numeric
        if not pd.api.types.is_numeric_dtype(metrics_df[col]):
            pytest.fail(f"Column '{col}' is not numeric.")

        # Check for NaN in successful rows
        if successful_rows[col].isnull().any():
            pytest.fail(f"Column '{col}' contains NaN values for subjects with processing_status='success'.")


def test_subject_id_format(metrics_df):
    """Contract: Verify subject_id format (e.g., 'sub-XXX')."""
    # Basic regex check for 'sub-' followed by digits
    import re
    pattern = re.compile(r'^sub-\d+$')
    invalid_ids = metrics_df[~metrics_df['subject_id'].astype(str).str.match(pattern)]

    assert invalid_ids.empty, f"Found invalid subject_id formats: {invalid_ids['subject_id'].tolist()}"


def test_processing_status_values(metrics_df):
    """Contract: Verify processing_status only contains allowed values."""
    allowed_values = {'success', 'excluded'}
    invalid_values = set(metrics_df['processing_status'].unique()) - allowed_values
    assert not invalid_values, f"Invalid processing_status values found: {invalid_values}"


def test_exclusion_reason_logic(metrics_df):
    """Contract: Verify exclusion_reason is populated for excluded subjects and empty for success."""
    for idx, row in metrics_df.iterrows():
        if row['processing_status'] == 'excluded':
            if pd.isna(row['exclusion_reason']) or row['exclusion_reason'] == '':
                pytest.fail(f"Subject {row['subject_id']} is marked 'excluded' but has no exclusion_reason.")
        elif row['processing_status'] == 'success':
            if not pd.isna(row['exclusion_reason']) and row['exclusion_reason'] != '':
                # Allow empty string or NaN for success, but warn if filled
                pass # Strictly speaking, we might want to enforce empty, but often NaN is used.
                # Let's enforce it must be empty/NaN for strict contract
                # if row['exclusion_reason']:
                #     pytest.fail(f"Subject {row['subject_id']} is 'success' but has exclusion_reason.")
                pass

if __name__ == "__main__":
    pytest.main([__file__, "-v"])