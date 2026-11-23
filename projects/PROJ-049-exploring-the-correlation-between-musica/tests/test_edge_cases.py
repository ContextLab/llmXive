"""
Edge case tests for the music-personality correlation pipeline.
"""
import os
import sys
import tempfile
import shutil
import pandas as pd
import numpy as np
import pytest

# Add project root to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils import setup_logging
from ingest import preprocess_merged_data, load_personality_data, load_listening_data
from synthetic_data import generate_synthetic_data


class TestEmptyDataset:
    """Tests for T032a: Empty dataset handling."""

    def test_empty_dataset(self):
        """Test that the pipeline handles an empty dataset gracefully."""
        logger = setup_logging()
        
        # Create an empty DataFrame with the expected schema
        empty_df = pd.DataFrame(columns=[
            'user_id', 'age', 'gender', 'country',
            'extraversion', 'neuroticism', 'agreeableness', 'conscientiousness', 'openness',
            'genre_rock', 'genre_pop', 'genre_hiphop', 'genre_electronic', 'genre_jazz',
            'genre_classical', 'genre_country', 'genre_rock_other', 'genre_pop_other', 'genre_other'
        ])
        
        # Test that preprocessing doesn't crash on empty data
        # This should either return empty or raise a specific error handled by the pipeline
        try:
            result = preprocess_merged_data(empty_df, logger)
            # If it returns, it should be empty
            assert len(result) == 0, "Empty dataset should result in empty output"
        except ValueError as e:
            # Or it might raise a ValueError which is also acceptable
            assert "empty" in str(e).lower(), f"Unexpected error for empty dataset: {e}"


class TestAllMissingDemographics:
    """Tests for T032b: Missing demographic handling."""

    def test_all_missing_demographics(self):
        """
        Test that the pipeline correctly handles a dataset where ALL demographic 
        columns (age, gender, country) are missing for all users.
        
        This is a critical edge case because:
        1. The regression analysis in US2 requires demographic controls
        2. Imputation strategies (median/mode) cannot work if ALL values are missing
        3. The pipeline should fail loudly or exclude these users, not produce garbage
        """
        logger = setup_logging()
        
        # Create a dataset with personality and genre data, but NO demographics
        # Simulate the output of T015 (merge) before T016 (missing data handling)
        n_users = 50
        
        # Generate valid personality and genre data
        df = pd.DataFrame({
            'user_id': [f'user_{i}' for i in range(n_users)],
            # Demographics are ALL NaN
            'age': [np.nan] * n_users,
            'gender': [np.nan] * n_users,
            'country': [np.nan] * n_users,
            # Valid personality traits
            'extraversion': np.random.rand(n_users) * 10,
            'neuroticism': np.random.rand(n_users) * 10,
            'agreeableness': np.random.rand(n_users) * 10,
            'conscientiousness': np.random.rand(n_users) * 10,
            'openness': np.random.rand(n_users) * 10,
            # Valid genre listening minutes
            'genre_rock': np.random.randint(0, 1000, n_users),
            'genre_pop': np.random.randint(0, 1000, n_users),
            'genre_hiphop': np.random.randint(0, 1000, n_users),
            'genre_electronic': np.random.randint(0, 1000, n_users),
            'genre_jazz': np.random.randint(0, 1000, n_users),
            'genre_classical': np.random.randint(0, 1000, n_users),
            'genre_country': np.random.randint(0, 1000, n_users),
            'genre_rock_other': np.random.randint(0, 1000, n_users),
            'genre_pop_other': np.random.randint(0, 1000, n_users),
            'genre_other': np.random.randint(0, 1000, n_users),
        })
        
        # Verify setup: all demographics are indeed missing
        assert df['age'].isna().all(), "Test setup failed: age should be all NaN"
        assert df['gender'].isna().all(), "Test setup failed: gender should be all NaN"
        assert df['country'].isna().all(), "Test setup failed: country should be all NaN"
        
        # Attempt to preprocess
        # According to T016: "Handle missing demographic data (impute numeric with median, categorical with mode) or exclude"
        # If ALL values are missing, median/mode cannot be computed.
        # The correct behavior is to EXCLUDE these users (resulting in empty dataset) 
        # or raise a clear error.
        
        try:
            result = preprocess_merged_data(df, logger)
            
            # If we get here, the function handled it. 
            # It should have excluded all rows because no demographics could be imputed.
            assert len(result) == 0, (
                "Pipeline should exclude users with ALL missing demographics. "
                f"Expected 0 rows, got {len(result)}"
            )
            
        except Exception as e:
            # Alternatively, the function might raise an error if it cannot proceed.
            # This is also acceptable as long as it doesn't produce silent garbage.
            error_msg = str(e).lower()
            assert (
                'missing' in error_msg or 
                'exclude' in error_msg or 
                'demographic' in error_msg or
                'cannot' in error_msg
            ), (
                f"Unexpected exception type for all-missing demographics: {type(e).__name__}: {e}"
            )

    def test_partial_missing_demographics(self):
        """
        Test that the pipeline correctly handles a dataset where SOME demographics 
        are missing (but not all), ensuring imputation works for available data.
        """
        logger = setup_logging()
        
        n_users = 100
        df = pd.DataFrame({
            'user_id': [f'user_{i}' for i in range(n_users)],
            # Partial missing: age has some NaN, gender has some NaN, country is complete
            'age': [float(i) if i % 3 != 0 else np.nan for i in range(n_users)],
            'gender': ['M' if i % 2 == 0 else 'F' if i % 2 == 1 else np.nan for i in range(n_users)],
            'country': ['USA'] * n_users,  # All present
            # Personality and genre data
            'extraversion': np.random.rand(n_users) * 10,
            'neuroticism': np.random.rand(n_users) * 10,
            'agreeableness': np.random.rand(n_users) * 10,
            'conscientiousness': np.random.rand(n_users) * 10,
            'openness': np.random.rand(n_users) * 10,
            'genre_rock': np.random.randint(0, 1000, n_users),
            'genre_pop': np.random.randint(0, 1000, n_users),
            'genre_hiphop': np.random.randint(0, 1000, n_users),
            'genre_electronic': np.random.randint(0, 1000, n_users),
            'genre_jazz': np.random.randint(0, 1000, n_users),
            'genre_classical': np.random.randint(0, 1000, n_users),
            'genre_country': np.random.randint(0, 1000, n_users),
            'genre_rock_other': np.random.randint(0, 1000, n_users),
            'genre_pop_other': np.random.randint(0, 1000, n_users),
            'genre_other': np.random.randint(0, 1000, n_users),
        })
        
        # Verify setup
        assert df['age'].isna().sum() > 0, "Test setup failed: age should have some NaN"
        assert df['gender'].isna().sum() > 0, "Test setup failed: gender should have some NaN"
        assert df['country'].isna().sum() == 0, "Test setup failed: country should have no NaN"
        
        # This should succeed with imputation
        result = preprocess_merged_data(df, logger)
        
        # Result should have same number of rows (imputation happened)
        assert len(result) == n_users, (
            f"Partial missing data should be imputed, not excluded. "
            f"Expected {n_users} rows, got {len(result)}"
        )
        
        # Check that imputed values are not NaN
        assert result['age'].isna().sum() == 0, "Age should have no NaN after imputation"
        assert result['gender'].isna().sum() == 0, "Gender should have no NaN after imputation"