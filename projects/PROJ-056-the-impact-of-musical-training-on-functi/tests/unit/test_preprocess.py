"""
Unit tests for preprocessing logic.
Implements T011: Unit test for filtering logic (>=1 year threshold).
"""
import pandas as pd
import pytest
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from data.preprocess import filter_by_training_years

class TestFilterByTrainingYears:
    """Test the filtering logic for years of training."""

    def test_filter_by_training_years(self):
        """
        Implements T011 requirements:
        - Assert that filtering by years_of_training >= 1 works correctly.
        - Assert that 'years_of_training' column exists.
        """
        # Create test data
        data = {
            'subject_id': ['S1', 'S2', 'S3', 'S4'],
            'group': ['musician', 'non_musician', 'musician', 'musician'],
            'years_of_training': [0.5, 2.0, 0.0, 5.0],
            'age': [15, 16, 14, 17],
            'sex': ['M', 'F', 'M', 'F'],
            'motion_score': [0.1, 0.2, 0.1, 0.3],
            'ses_score': [5, 6, 4, 7]
        }
        df = pd.DataFrame(data)

        # Apply filter
        filtered_df = filter_by_training_years(df, min_years=1.0)

        # Assert column exists
        assert 'years_of_training' in filtered_df.columns

        # Assert expected count
        # Expected: S2 (2.0) and S4 (5.0) -> 2 subjects
        expected_count = 2
        assert len(filtered_df[filtered_df['years_of_training'] >= 1]) == expected_count
        
        # Assert all remaining rows satisfy condition
        assert (filtered_df['years_of_training'] >= 1.0).all()

    def test_filter_all_exclude(self):
        """Test case where all subjects are excluded."""
        data = {
            'subject_id': ['S1', 'S2'],
            'group': ['musician', 'musician'],
            'years_of_training': [0.1, 0.5],
            'age': [15, 16],
            'sex': ['M', 'F'],
            'motion_score': [0.1, 0.2],
            'ses_score': [5, 6]
        }
        df = pd.DataFrame(data)
        filtered_df = filter_by_training_years(df, min_years=1.0)
        assert len(filtered_df) == 0

    def test_filter_none_exclude(self):
        """Test case where no subjects are excluded."""
        data = {
            'subject_id': ['S1', 'S2'],
            'group': ['musician', 'musician'],
            'years_of_training': [2.0, 5.0],
            'age': [15, 16],
            'sex': ['M', 'F'],
            'motion_score': [0.1, 0.2],
            'ses_score': [5, 6]
        }
        df = pd.DataFrame(data)
        filtered_df = filter_by_training_years(df, min_years=1.0)
        assert len(filtered_df) == 2
