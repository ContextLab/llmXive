"""
Integration tests for the solubility prediction pipeline.
Tests the end-to-end flow from data ingestion to feature engineering.
"""
import os
import sys
import pytest
import pandas as pd
from pathlib import Path

# Add project root to path to import code modules if needed,
# though this test primarily validates file artifacts.
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Expected output path based on T018
OUTPUT_FILE = PROJECT_ROOT / "data" / "processed" / "solubility_features.csv"

# Required columns as per task description
REQUIRED_COLUMNS = ['solute_fp', 'solvent_desc', 'interaction_terms', 'logS']


def test_ingest_sample():
    """
    Verify that the pipeline produced a valid processed dataset.
    
    Input: data/processed/solubility_features.csv
    Expected: Columns ['solute_fp', 'solvent_desc', 'interaction_terms', 'logS'] present.
              Row count >= 10.
    """
    # Check file existence
    assert OUTPUT_FILE.exists(), f"Output file {OUTPUT_FILE} does not exist. " \
                                 "Pipeline T018 (data production) has not run or failed."

    # Load the dataset
    try:
        df = pd.read_csv(OUTPUT_FILE)
    except Exception as e:
        pytest.fail(f"Failed to read {OUTPUT_FILE}: {e}")

    # Verify row count
    assert len(df) >= 10, f"Dataset has {len(df)} rows, expected >= 10. " \
                          "The pipeline may have filtered too aggressively or failed to ingest data."

    # Verify required columns
    missing_columns = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    assert not missing_columns, f"Missing required columns: {missing_columns}. " \
                                f"Expected columns: {REQUIRED_COLUMNS}, Found: {list(df.columns)}"

    # Additional sanity checks on data types/content if necessary
    # Ensure 'logS' is numeric
    if 'logS' in df.columns:
        assert pd.api.types.is_numeric_dtype(df['logS']), "Column 'logS' must be numeric."

    # Ensure 'solute_fp' is not empty (assuming it's a string representation of a fingerprint)
    if 'solute_fp' in df.columns:
        non_empty = df['solute_fp'].dropna().astype(str).str.len().gt(0).sum()
        assert non_empty > 0, "Column 'solute_fp' appears to be empty or all NaN."

    # If 'solvent_desc' is expected to be a list or string representation, check it exists
    if 'solvent_desc' in df.columns:
        non_empty = df['solvent_desc'].dropna().astype(str).str.len().gt(0).sum()
        assert non_empty > 0, "Column 'solvent_desc' appears to be empty or all NaN."

    # If 'interaction_terms' is expected, check it exists
    if 'interaction_terms' in df.columns:
        non_empty = df['interaction_terms'].dropna().astype(str).str.len().gt(0).sum()
        assert non_empty > 0, "Column 'interaction_terms' appears to be empty or all NaN."

    # Test passed
    print(f"Pipeline integration test passed: {len(df)} rows, columns {list(df.columns)}")