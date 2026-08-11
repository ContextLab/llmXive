"""
Unit tests for data ingestion module.
"""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys

# Add parent directory to path to allow imports from code/
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.data_ingestion import impute_missing_values, filter_primary_outcomes

def load_fixture(filepath):
    """Helper to load a fixture file."""
    fixture_path = Path(__file__).parent.parent / "fixtures" / filepath
    if not fixture_path.exists():
        raise FileNotFoundError(f"Fixture file not found: {fixture_path}")
    return pd.read_csv(fixture_path)

class TestDataIngestion:
    """Tests for data ingestion logic."""

    def test_imputation_sex_mode_returns_most_frequent(self):
        """
        Test that Sex imputation uses Mode (most frequent value).
        Fixture: tests/fixtures/sample_imputation.csv
        Expected: Majority 'M', so NaN should be imputed to 'M'.
        """
        # Load the fixture
        df = load_fixture("sample_imputation.csv")
        
        # Verify fixture setup: Majority M, some F, some NaN
        # Count non-null values
        sex_counts = df['sex'].value_counts(dropna=False)
        assert 'M' in sex_counts.index, "Fixture must have 'M' values"
        assert df['sex'].isna().any(), "Fixture must have NaN values in sex"
        
        # Calculate the expected mode manually to ensure test validity
        expected_mode = df['sex'].mode()[0]
        assert expected_mode == 'M', "Fixture setup error: Mode should be M"
        
        # Call the actual implementation
        # We pass a strategy dict to enforce 'mode' for 'sex'
        # The function signature in code/data_ingestion.py is assumed to be:
        # impute_missing_values(df, strategy=None) or similar.
        # Based on T013 description: "Apply Median for Age, BMI, DQS; Mode for Sex."
        # We will assume the function has a default strategy or we can pass one.
        # If the function doesn't accept a strategy argument yet, we assume it
        # implements the hardcoded logic from T013.
        
        # Assuming the function signature matches the task description logic:
        df_imputed = impute_missing_values(df)
        
        # Verify no NaNs remain in the 'sex' column
        assert not df_imputed['sex'].isna().any(), "Imputation should remove all NaNs in sex"
        
        # Verify the filled values are the mode ('M')
        # Specifically check the row that was NaN
        # In our fixture, the last row (index 5) had NaN.
        # We need to ensure it is now 'M'.
        # Since the order is preserved, we can check the last value if we know the fixture structure.
        # A safer check: all non-null values in the original were 'M' or 'F'.
        # The imputed value must be 'M'.
        
        # Check that the count of 'M' increased by 1 (the NaN was filled with M)
        # Original count of M (excluding NaN)
        original_m_count = df['sex'].value_counts().get('M', 0)
        # New count of M
        new_m_count = df_imputed['sex'].value_counts().get('M', 0)
        
        assert new_m_count == original_m_count + 1, "The NaN value should have been filled with 'M', increasing the count by 1"

    def test_filtering_excludes_null_primary_outcomes(self):
        """
        Test that filtering excludes participants with null alpha diversity, 
        fluid intelligence, or DQS.
        Input: A sample with null values in primary outcomes.
        Expected: Reduced row count.
        """
        # Create a small in-memory sample with nulls
        data = {
            'participant_id': [1, 2, 3, 4, 5],
            'alpha_diversity': [3.0, np.nan, 3.2, 3.1, 3.3],
            'fluid_intelligence': [12.0, 11.5, np.nan, 12.5, 13.0],
            'dqs': [80.0, 75.0, 78.0, np.nan, 82.0]
        }
        df = pd.DataFrame(data)
        
        initial_count = len(df)
        assert initial_count == 5, "Test setup error"
        
        # Call the actual implementation
        filtered_df = filter_primary_outcomes(df)
        
        final_count = len(filtered_df)
        
        # Expect only row 0 (id 1) and row 4 (id 5) to remain
        # Row 0: [3.0, 12.0, 80.0] -> Keep
        # Row 1: [nan, 11.5, 75.0] -> Drop
        # Row 2: [3.2, nan, 78.0] -> Drop
        # Row 3: [3.1, 12.5, nan] -> Drop
        # Row 4: [3.3, 13.0, 82.0] -> Keep
        
        assert final_count == 2, f"Expected 2 rows after filtering, got {final_count}"
        assert filtered_df['participant_id'].tolist() == [1, 5], "Incorrect rows retained"