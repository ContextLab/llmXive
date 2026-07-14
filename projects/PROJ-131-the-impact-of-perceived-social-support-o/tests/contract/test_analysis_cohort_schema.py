"""
Contract test for the synthetic cohort data schema.

This test verifies that the synthetic cohort output (data/results/synthetic_cohort.csv)
adheres to the expected schema defined in the project specifications.

It checks:
1. File existence.
2. Presence of all mandatory columns (demographics, variables, weights).
3. Data types for numeric columns.
4. Non-null constraints for critical fields.
5. Valid ranges for weights and propensity scores.
"""
import os
import pytest
import pandas as pd
import numpy as np
from pathlib import Path

# Project root relative to this test file (assuming tests/ is at root)
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
COHORT_OUTPUT_PATH = PROJECT_ROOT / "data" / "results" / "synthetic_cohort.csv"

# Expected schema definition based on T014 and T015 requirements
# Columns required for the synthetic cohort:
EXPECTED_COLUMNS = {
    # Demographics (used for matching/propensity)
    "age": "numeric",
    "gender": "categorical",
    "education": "categorical",
    "income": "numeric",
    
    # Core variables (from T013 preprocessing)
    "social_support": "numeric",
    "harassment_severity": "numeric",  # Or binary exposure depending on T014 logic
    "depression": "numeric",
    "anxiety": "numeric",
    "ptsd": "numeric",
    
    # Cohort construction artifacts (T014)
    "propensity_score": "numeric",
    "match_id": "integer",  # Identifier for matched pairs
    "weight": "numeric",     # Inverse probability weight
    "source_dataset": "categorical" # GSS or Cyberbullying
}

# Columns that must not be null
CRITICAL_NON_NULL = [
    "social_support",
    "harassment_severity",
    "depression",
    "anxiety",
    "weight",
    "propensity_score"
]

# Valid ranges for numeric validation
VALID_RANGES = {
    "propensity_score": (0.0, 1.0),
    "weight": (0.0, 100.0), # Upper bound heuristic, adjust if needed
    "age": (10, 100),
    "social_support": (0, 100),
    "depression": (0, 60),
    "anxiety": (0, 21),
    "ptsd": (0, 100)
}

@pytest.fixture(scope="module")
def cohort_df():
    """Load the synthetic cohort DataFrame for testing."""
    if not COHORT_OUTPUT_PATH.exists():
        pytest.skip(f"Output file not found: {COHORT_OUTPUT_PATH}. "
                    "Run the pipeline (T014) to generate the synthetic cohort before testing.")
    
    try:
        df = pd.read_csv(COHORT_OUTPUT_PATH)
        return df
    except Exception as e:
        pytest.fail(f"Failed to load cohort CSV: {e}")

class TestCohortSchema:
    """
    Contract tests for the synthetic cohort schema.
    """
    
    def test_file_exists(self):
        """Verify the output file exists."""
        assert COHORT_OUTPUT_PATH.exists(), f"File {COHORT_OUTPUT_PATH} does not exist."
    
    def test_required_columns_present(self, cohort_df):
        """Verify all expected columns are present in the DataFrame."""
        missing_cols = set(EXPECTED_COLUMNS.keys()) - set(cohort_df.columns)
        assert not missing_cols, f"Missing required columns: {missing_cols}"
    
    def test_column_count(self, cohort_df):
        """Verify the exact number of columns matches expectation (optional strictness)."""
        # We check at least the expected ones, but allow extra columns if logic expands
        assert len(cohort_df.columns) >= len(EXPECTED_COLUMNS), \
            f"Expected at least {len(EXPECTED_COLUMNS)} columns, found {len(cohort_df.columns)}"
    
    def test_no_null_critical_values(self, cohort_df):
        """Verify critical columns have no null values."""
        for col in CRITICAL_NON_NULL:
            if col in cohort_df.columns:
                null_count = cohort_df[col].isnull().sum()
                assert null_count == 0, f"Column '{col}' contains {null_count} null values."
    
    def test_numeric_column_types(self, cohort_df):
        """Verify numeric columns are actually numeric."""
        numeric_cols = [k for k, v in EXPECTED_COLUMNS.items() if v == "numeric"]
        for col in numeric_cols:
            if col in cohort_df.columns:
                # Check if it's numeric (int or float)
                assert pd.api.types.is_numeric_dtype(cohort_df[col]), \
                    f"Column '{col}' is not numeric (dtype: {cohort_df[col].dtype})"
    
    def test_propensity_score_range(self, cohort_df):
        """Verify propensity scores are within [0, 1]."""
        if "propensity_score" in cohort_df.columns:
            scores = cohort_df["propensity_score"]
            assert (scores >= 0.0).all() and (scores <= 1.0).all(), \
                "Propensity scores must be between 0.0 and 1.0."
    
    def test_weights_positive(self, cohort_df):
        """Verify weights are positive."""
        if "weight" in cohort_df.columns:
            weights = cohort_df["weight"]
            assert (weights > 0).all(), "Weights must be strictly positive."
    
    def test_sample_size(self, cohort_df):
        """Verify the cohort has a minimum sample size (N > 30 per SC-001 context)."""
        assert len(cohort_df) > 30, f"Cohort sample size ({len(cohort_df)}) is too small (N > 30 required)."
    
    def test_variance_harassment(self, cohort_df):
        """Verify variance of Harassment Exposure/Severity is sufficient (SD > 0.5)."""
        # T015 requirement: Check Variance of Harassment Exposure (SD > 0.5)
        if "harassment_severity" in cohort_df.columns:
            std_dev = cohort_df["harassment_severity"].std()
            assert std_dev > 0.5, f"Harassment severity standard deviation ({std_dev:.2f}) is too low (must be > 0.5)."
        elif "harassment_exposure" in cohort_df.columns:
            std_dev = cohort_df["harassment_exposure"].std()
            assert std_dev > 0.5, f"Harassment exposure standard deviation ({std_dev:.2f}) is too low (must be > 0.5)."
        else:
            pytest.skip("Harassment severity/exposure column not found for variance check.")