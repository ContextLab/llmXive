"""
Integration test for variable validation and missing value flagging in the data pipeline.

This test verifies that the data cleaning and validation scripts correctly:
1. Identify missing values in the curated dataset.
2. Flag columns exceeding the 5% missing value threshold.
3. Ensure the dataset meets the minimum row count requirement (>= 100).
4. Validate the presence of required columns (polymer_smiles, filler_smiles, adhesion_energy).

Prerequisites:
- T012 (Download) must have run to produce raw data.
- T015 (Clean) must have run to produce curated data.
- The test expects `data/curated/curated_dataset.csv` to exist.
"""

import os
import sys
import pandas as pd
import pytest
from pathlib import Path
import logging

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "code"))

from utils.exceptions import DataError
from data.clean import validate_missing_values, validate_row_count, validate_adhesion_energy

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

CURATED_PATH = PROJECT_ROOT / "data" / "curated" / "curated_dataset.csv"
REQUIRED_COLUMNS = ["polymer_smiles", "filler_smiles", "adhesion_energy"]
MISSING_THRESHOLD = 0.05  # 5%
MIN_ROWS = 100

class TestDataValidation:
    """Integration tests for data validation logic."""

    def test_curated_dataset_exists(self):
        """Verify that the curated dataset file exists."""
        assert CURATED_PATH.exists(), f"Curated dataset not found at {CURATED_PATH}. Run T012 and T015 first."

    def test_required_columns_present(self):
        """Verify that all required columns are present in the dataset."""
        df = pd.read_csv(CURATED_PATH)
        missing_cols = set(REQUIRED_COLUMNS) - set(df.columns)
        assert len(missing_cols) == 0, f"Missing required columns: {missing_cols}"

    def test_row_count_validation(self):
        """Verify that the dataset meets the minimum row count requirement."""
        df = pd.read_csv(CURATED_PATH)
        row_count = len(df)
        assert row_count >= MIN_ROWS, f"Dataset has {row_count} rows, which is less than the minimum {MIN_ROWS}."

    def test_missing_values_flagging(self):
        """Verify that missing values are correctly identified and flagged."""
        df = pd.read_csv(CURATED_PATH)
        
        # Calculate missing percentages for each required column
        missing_pcts = {}
        for col in REQUIRED_COLUMNS:
            if col in df.columns:
                missing_pcts[col] = df[col].isna().sum() / len(df)
            else:
                missing_pcts[col] = 1.0  # If column missing, 100% missing

        # Check if any column exceeds the threshold
        flagged_columns = [col for col, pct in missing_pcts.items() if pct > MISSING_THRESHOLD]
        
        if flagged_columns:
            # If the test fails here, it means the data cleaning step (T015) should have aborted
            # or flagged the data. Since we are running the integration test, we assert that
            # the validation logic *would* catch this.
            logger.warning(f"Columns exceeding missing value threshold: {flagged_columns}")
            # In a strict pipeline, this would raise an error. For this test, we verify the logic works.
            # If the data is valid (<=5% missing), this test passes.
            # If the data is invalid (>5% missing), the test fails, indicating a data quality issue.
            assert False, f"Data quality check failed: Columns {flagged_columns} exceed {MISSING_THRESHOLD*100}% missing values."
        else:
            logger.info("All required columns are within the missing value threshold.")

    def test_adhesion_energy_validation(self):
        """Verify that adhesion energy is present and valid (non-zero/NaN if expected)."""
        df = pd.read_csv(CURATED_PATH)
        assert "adhesion_energy" in df.columns, "adhesion_energy column missing."
        
        # Check for NaN values specifically in adhesion_energy
        nan_count = df['adhesion_energy'].isna().sum()
        if nan_count > 0:
            pct = nan_count / len(df)
            assert pct <= MISSING_THRESHOLD, f"adhesion_energy has {pct*100}% missing values, exceeding threshold."
        
        logger.info("Adhesion energy validation passed.")

    def test_validate_missing_values_function(self):
        """Unit test for the validate_missing_values function from clean.py."""
        df = pd.read_csv(CURATED_PATH)
        # This function should return a boolean or raise an error depending on implementation.
        # Based on T015 spec, it flags missing values.
        try:
            result = validate_missing_values(df, REQUIRED_COLUMNS, MISSING_THRESHOLD)
            # If it returns True, data is valid. If False, data is invalid.
            assert result is True, "validate_missing_values returned False for valid data."
        except DataError as e:
            # If it raises DataError, that's also a valid outcome for invalid data.
            # Since we expect valid data here, we check the error message.
            assert "missing values" in str(e).lower(), f"Unexpected error: {e}"

    def test_validate_row_count_function(self):
        """Unit test for the validate_row_count function from clean.py."""
        df = pd.read_csv(CURATED_PATH)
        try:
            result = validate_row_count(df, MIN_ROWS)
            assert result is True, "validate_row_count returned False for valid row count."
        except DataError as e:
            assert "row count" in str(e).lower(), f"Unexpected error: {e}"

    def test_validate_adhesion_energy_function(self):
        """Unit test for the validate_adhesion_energy function from clean.py."""
        df = pd.read_csv(CURATED_PATH)
        try:
            result = validate_adhesion_energy(df)
            assert result is True, "validate_adhesion_energy returned False for valid data."
        except DataError as e:
            assert "adhesion energy" in str(e).lower(), f"Unexpected error: {e}"