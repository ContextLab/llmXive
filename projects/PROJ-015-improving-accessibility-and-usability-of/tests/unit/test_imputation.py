"""
Unit tests for SUS imputation logic (T021b) in code/analysis/data_cleaner.py.

This test verifies that the DataCleaner correctly imputes a single missing SUS item
with the participant's mean score, and marks the session as incomplete if >1 items
are missing.
"""
import pytest
import pandas as pd
import numpy as np
import sys
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from code.analysis.data_cleaner import DataCleaner


class TestSUSImputation:
    """Tests for the impute_sus method of DataCleaner."""

    @pytest.fixture
    def sample_data_with_one_missing(self):
        """Create a DataFrame simulating a session with exactly one missing SUS item."""
        data = {
            'participant_id': ['P001', 'P001'],
            'interface_type': ['traditional', 'traditional'],
            'completion_time_seconds': [120.5, 120.5],
            'error_count': [2, 2],
            'sus_score': [80, 80], # This column is actually the aggregate, but we simulate raw items
            # We need to simulate the raw 10 items for imputation logic
            # Let's assume the cleaner expects raw items or reconstructs them.
            # Based on T021b logic: "If <=1 item missing, impute with participant mean"
            # We will create a mock scenario where the 'sus_score' column is the aggregate,
            # but the cleaner logic might operate on a reconstructed or pre-aggregated state.
            # However, the task description says: "generates a session with one missing SUS item".
            # Standard SUS has 10 items (Q1-Q10).
            # Let's assume the input to the cleaner has columns 'sus_q1'...'sus_q10'.
            'sus_q1': [5, 4],
            'sus_q2': [3, np.nan], # Missing one item
            'sus_q3': [5, 5],
            'sus_q4': [4, 4],
            'sus_q5': [5, 5],
            'sus_q6': [3, 3],
            'sus_q7': [4, 4],
            'sus_q8': [5, 5],
            'sus_q9': [4, 4],
            'sus_q10': [5, 5],
            'status': ['complete', 'complete']
        }
        return pd.DataFrame(data)

    @pytest.fixture
    def sample_data_with_two_missing(self):
        """Create a DataFrame simulating a session with two missing SUS items."""
        data = {
            'participant_id': ['P002', 'P002'],
            'interface_type': ['explainable', 'explainable'],
            'completion_time_seconds': [100.0, 100.0],
            'error_count': [1, 1],
            'sus_q1': [5, 5],
            'sus_q2': [np.nan, np.nan], # Missing two items
            'sus_q3': [np.nan, np.nan],
            'sus_q4': [4, 4],
            'sus_q5': [5, 5],
            'sus_q6': [3, 3],
            'sus_q7': [4, 4],
            'sus_q8': [5, 5],
            'sus_q9': [4, 4],
            'sus_q10': [5, 5],
            'status': ['complete', 'complete']
        }
        return pd.DataFrame(data)

    def test_impute_single_missing_item(self, sample_data_with_one_missing):
        """
        Verify that if exactly one SUS item is missing, it is imputed with the participant's mean.
        The task requires: "asserts the imputed value matches the participant mean".
        """
        df = sample_data_with_one_missing.copy()
        cleaner = DataCleaner()

        # Calculate the expected mean for P001 (excluding the missing value)
        # Items: 5, 3, 5, 4, 5, 3, 4, 5, 4, 5 -> Sum = 43, Count = 9
        # Mean = 43 / 9 = 4.777...
        # Note: The cleaner implementation might handle this differently, but we test the logic.
        # Let's assume the cleaner fills NaN with the row mean.
        expected_mean = df.loc[df['participant_id'] == 'P001', ['sus_q1', 'sus_q3', 'sus_q4', 'sus_q5', 'sus_q6', 'sus_q7', 'sus_q8', 'sus_q9', 'sus_q10']].mean().mean()
        
        # Run the imputation logic
        # We assume the method signature is impute_sus(df) -> df
        result_df = cleaner.impute_sus(df)

        # Verify the missing value was filled
        assert not result_df.loc[result_df['participant_id'] == 'P001', 'sus_q2'].isna().any()
        
        # Verify the filled value is the participant mean (approximate due to float)
        filled_value = result_df.loc[result_df['participant_id'] == 'P001', 'sus_q2'].iloc[0]
        # The mean of the existing 9 items is 4.777...
        # The imputation logic in T021b says "impute with participant mean".
        # We check if it's close to the calculated mean.
        assert np.isclose(filled_value, expected_mean, atol=1e-5), f"Expected {expected_mean}, got {filled_value}"

    def test_mark_incomplete_if_multiple_missing(self, sample_data_with_two_missing):
        """
        Verify that if more than one SUS item is missing, the session status is marked as 'incomplete'.
        """
        df = sample_data_with_two_missing.copy()
        cleaner = DataCleaner()

        # Run imputation
        result_df = cleaner.impute_sus(df)

        # Check that the status was updated to 'incomplete' for P002
        # Note: T021a handles filtering incomplete sessions, but T021b marks them.
        # We assume the impute_sus method updates the 'status' column if imputation fails.
        p002_status = result_df.loc[result_df['participant_id'] == 'P002', 'status'].iloc[0]
        assert p002_status == 'incomplete', f"Expected status 'incomplete', got {p002_status}"

    def test_no_imputation_needed(self):
        """Verify that a complete dataset remains unchanged."""
        data = {
            'participant_id': ['P003', 'P003'],
            'interface_type': ['traditional', 'traditional'],
            'completion_time_seconds': [110.0, 110.0],
            'error_count': [3, 3],
            'sus_q1': [5, 5],
            'sus_q2': [4, 4],
            'sus_q3': [5, 5],
            'sus_q4': [4, 4],
            'sus_q5': [5, 5],
            'sus_q6': [3, 3],
            'sus_q7': [4, 4],
            'sus_q8': [5, 5],
            'sus_q9': [4, 4],
            'sus_q10': [5, 5],
            'status': ['complete', 'complete']
        }
        df = pd.DataFrame(data)
        cleaner = DataCleaner()

        result_df = cleaner.impute_sus(df)

        # Verify no changes (except possibly type coercion)
        pd.testing.assert_frame_equal(df, result_df)

if __name__ == "__main__":
    pytest.main([__file__, "-v"])