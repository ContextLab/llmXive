"""
Contract test: Verify `salience_score` column exists and is numeric in the
preprocessed output.

This test validates the schema contract for User Story 1 (US1). It ensures that
the pipeline produces a `data/processed/salience_enriched.csv` file where the
`salience_score` column exists and contains valid numeric values (floats) within
the expected range [0.0, 1.0].

This test is designed to fail if the preprocessing stage (T016) has not been
completed or if the output schema is violated.
"""

import os
import sys
import pytest
import pandas as pd
from pathlib import Path

# Ensure the project root is in the path for imports if running directly
# though typically pytest is run from the root.
PROJECT_ROOT = Path(__file__).parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data" / "processed"
OUTPUT_FILE = DATA_DIR / "salience_enriched.csv"

REQUIRED_COLUMNS = ["salience_score"]
MIN_SCORE = 0.0
MAX_SCORE = 1.0

@pytest.fixture(scope="module")
def df_salience():
    """
    Load the salience enriched dataset.
    Raises FileNotFoundError or AssertionError if the file is missing or invalid.
    """
    if not OUTPUT_FILE.exists():
        pytest.fail(
            f"Contract test failed: Output file not found at {OUTPUT_FILE}. "
            "Has T016 (preprocess) been run?"
        )
    
    try:
        df = pd.read_csv(OUTPUT_FILE)
    except Exception as e:
        pytest.fail(f"Contract test failed: Could not read CSV: {e}")
    
    return df

class TestSalienceSchema:
    """
    Contract tests for the salience enriched data schema.
    """

    def test_salience_score_column_exists(self, df_salience):
        """
        Verify that the `salience_score` column exists in the dataset.
        """
        missing_cols = [col for col in REQUIRED_COLUMNS if col not in df_salience.columns]
        assert not missing_cols, (
            f"Contract test failed: Missing required columns: {missing_cols}. "
            "The `salience_score` column is required by FR-002."
        )

    def test_salience_score_is_numeric(self, df_salience):
        """
        Verify that the `salience_score` column contains numeric data.
        """
        score_col = df_salience["salience_score"]
        
        # Check if dtype is numeric
        if not pd.api.types.is_numeric_dtype(score_col):
            # Try to coerce to see if it's string-numeric
            try:
                score_col = pd.to_numeric(score_col, errors='raise')
            except (ValueError, TypeError):
                pytest.fail(
                    f"Contract test failed: `salience_score` column is not numeric. "
                    f"Found dtype: {score_col.dtype}"
                )

    def test_salience_score_range_valid(self, df_salience):
        """
        Verify that all salience scores are within the range [0.0, 1.0].
        """
        score_col = pd.to_numeric(df_salience["salience_score"], errors='coerce')
        
        # Check for NaNs introduced by coercion (non-numeric values)
        if score_col.isna().any():
            pytest.fail(
                "Contract test failed: `salience_score` contains non-numeric values "
                "that could not be coerced."
            )

        min_val = score_col.min()
        max_val = score_col.max()

        assert min_val >= MIN_SCORE, (
            f"Contract test failed: Minimum salience score {min_val} is below "
            f"allowed minimum {MIN_SCORE}."
        )
        assert max_val <= MAX_SCORE, (
            f"Contract test failed: Maximum salience score {max_val} is above "
            f"allowed maximum {MAX_SCORE}."
        )

    def test_salience_score_not_all_null(self, df_salience):
        """
        Verify that the `salience_score` column is not entirely empty.
        """
        score_col = df_salience["salience_score"]
        valid_count = score_col.notna().sum()
        
        assert valid_count > 0, (
            "Contract test failed: `salience_score` column is entirely empty. "
            "At least one valid score is expected."
        )

    def test_salience_score_has_no_infinite_values(self, df_salience):
        """
        Verify that the `salience_score` column contains no infinite values.
        """
        score_col = pd.to_numeric(df_salience["salience_score"], errors='coerce')
        assert not score_col.isin([float('inf'), float('-inf')]).any(), (
            "Contract test failed: `salience_score` contains infinite values."
        )