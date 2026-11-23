"""
Unit tests for data cleaning filters, specifically focusing on age and MMSE filtering logic.
This test suite validates T033a (age) and T033b (MMSE).
"""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys
import os

# Add parent directory to path to allow importing from code/
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.ingestion.validator import clean_data
from code.config import get_mmse_threshold


class TestCleaningFiltersAge:
    """Tests for the age filtering functionality in clean_data."""

    def test_cleaning_filters_age(self):
        """
        Test that records with age < 65 are excluded.
        
        Validates:
        - Records with age < 65 are removed
        - Records with age >= 65 are kept
        - Records with missing age are removed
        """
        # Create test data with various age scenarios
        test_data = pd.DataFrame({
            'participant_id': ['P001', 'P002', 'P003', 'P004', 'P005', 'P006'],
            'age': [60, 65, 70, 59, np.nan, 80],
            'stimulus_type': ['nostalgia', 'control', 'nostalgia', 'control', 'nostalgia', 'control'],
            'perseverative_errors': [10, 12, 8, 15, 11, 9],
            'categories_completed': [5, 4, 6, 3, 5, 6]
        })
        
        # Expected: P002 (65), P003 (70), P006 (80) should remain
        # P001 (60), P004 (59), P005 (NaN) should be excluded
        expected_indices = [1, 2, 5]
        
        # Run the cleaning function
        cleaned_df = clean_data(test_data)
        
        # Verify the number of remaining records
        assert len(cleaned_df) == 3, f"Expected 3 records after age filtering, got {len(cleaned_df)}"
        
        # Verify the correct indices remain
        assert list(cleaned_df.index) == expected_indices, \
            f"Expected indices {expected_indices}, got {list(cleaned_df.index)}"
        
        # Verify all remaining ages are >= 65
        assert all(cleaned_df['age'] >= 65), \
            "All remaining records should have age >= 65"
        
        # Verify no NaN ages remain
        assert not cleaned_df['age'].isna().any(), \
            "No NaN age values should remain after filtering"

    def test_cleaning_filters_age_all_excluded(self):
        """Test behavior when all records fail age filter."""
        test_data = pd.DataFrame({
            'participant_id': ['P001', 'P002'],
            'age': [25, 45],
            'stimulus_type': ['nostalgia', 'control'],
            'perseverative_errors': [10, 12],
            'categories_completed': [5, 4]
        })
        
        cleaned_df = clean_data(test_data)
        
        assert len(cleaned_df) == 0, "All records should be excluded when age < 65"

    def test_cleaning_filters_age_edge_case_65(self):
        """Test that age exactly 65 is kept."""
        test_data = pd.DataFrame({
            'participant_id': ['P001'],
            'age': [65],
            'stimulus_type': ['nostalgia'],
            'perseverative_errors': [10],
            'categories_completed': [5]
        })
        
        cleaned_df = clean_data(test_data)
        
        assert len(cleaned_df) == 1, "Record with age 65 should be kept"
        assert cleaned_df.iloc[0]['age'] == 65

    def test_cleaning_filters_age_preserves_other_data(self):
        """Test that non-age data is preserved after age filtering."""
        test_data = pd.DataFrame({
            'participant_id': ['P001', 'P002'],
            'age': [60, 70],
            'stimulus_type': ['nostalgia', 'control'],
            'perseverative_errors': [10, 12],
            'categories_completed': [5, 4],
            'additional_column': ['A', 'B']
        })
        
        cleaned_df = clean_data(test_data)
        
        assert len(cleaned_df) == 1
        assert cleaned_df.iloc[0]['additional_column'] == 'B'
        assert cleaned_df.iloc[0]['stimulus_type'] == 'control'
        assert cleaned_df.iloc[0]['perseverative_errors'] == 12


class TestCleaningFiltersMMSE:
    """Tests for the MMSE filtering functionality in clean_data."""

    def test_cleaning_filters_mmse(self):
        """
        Test that records with MMSE < 24 are excluded when MMSE column exists.
        
        Validates:
        - Records with MMSE < 24 are removed
        - Records with MMSE >= 24 are kept
        - Records with missing MMSE are removed (if column exists)
        """
        threshold = get_mmse_threshold()
        
        # Create test data with various MMSE scenarios
        test_data = pd.DataFrame({
            'participant_id': ['P001', 'P002', 'P003', 'P004', 'P005', 'P006'],
            'age': [65, 70, 72, 68, 75, 80],
            'stimulus_type': ['nostalgia', 'control', 'nostalgia', 'control', 'nostalgia', 'control'],
            'perseverative_errors': [10, 12, 8, 15, 11, 9],
            'categories_completed': [5, 4, 6, 3, 5, 6],
            'MMSE': [28, 22, 30, 24, 18, np.nan]
        })
        
        # Expected: P001 (28), P003 (30), P004 (24) should remain
        # P002 (22), P005 (18), P006 (NaN) should be excluded
        expected_indices = [0, 2, 3]
        
        # Run the cleaning function
        cleaned_df = clean_data(test_data)
        
        # Verify the number of remaining records
        assert len(cleaned_df) == 3, f"Expected 3 records after MMSE filtering, got {len(cleaned_df)}"
        
        # Verify the correct indices remain
        assert list(cleaned_df.index) == expected_indices, \
            f"Expected indices {expected_indices}, got {list(cleaned_df.index)}"
        
        # Verify all remaining MMSE scores are >= threshold
        assert all(cleaned_df['MMSE'] >= threshold), \
            f"All remaining records should have MMSE >= {threshold}"
        
        # Verify no NaN MMSE values remain
        assert not cleaned_df['MMSE'].isna().any(), \
            "No NaN MMSE values should remain after filtering"

    def test_cleaning_filters_mmse_all_excluded(self):
        """Test behavior when all records fail MMSE filter."""
        test_data = pd.DataFrame({
            'participant_id': ['P001', 'P002'],
            'age': [70, 75],
            'stimulus_type': ['nostalgia', 'control'],
            'perseverative_errors': [10, 12],
            'categories_completed': [5, 4],
            'MMSE': [15, 20]
        })
        
        cleaned_df = clean_data(test_data)
        
        assert len(cleaned_df) == 0, "All records should be excluded when MMSE < 24"

    def test_cleaning_filters_mmse_edge_case_threshold(self):
        """Test that MMSE exactly at threshold is kept."""
        threshold = get_mmse_threshold()
        test_data = pd.DataFrame({
            'participant_id': ['P001'],
            'age': [70],
            'stimulus_type': ['nostalgia'],
            'perseverative_errors': [10],
            'categories_completed': [5],
            'MMSE': [threshold]
        })
        
        cleaned_df = clean_data(test_data)
        
        assert len(cleaned_df) == 1, f"Record with MMSE {threshold} should be kept"
        assert cleaned_df.iloc[0]['MMSE'] == threshold

    def test_cleaning_filters_mmse_no_column(self):
        """Test that data is preserved when MMSE column is missing."""
        test_data = pd.DataFrame({
            'participant_id': ['P001', 'P002'],
            'age': [70, 75],
            'stimulus_type': ['nostalgia', 'control'],
            'perseverative_errors': [10, 12],
            'categories_completed': [5, 4]
        })
        
        cleaned_df = clean_data(test_data)
        
        # Should return all records since MMSE column doesn't exist
        assert len(cleaned_df) == 2, "All records should be kept when MMSE column is missing"
        assert 'MMSE' not in cleaned_df.columns

    def test_cleaning_filters_mmse_preserves_other_data(self):
        """Test that non-MMSE data is preserved after MMSE filtering."""
        test_data = pd.DataFrame({
            'participant_id': ['P001', 'P002', 'P003'],
            'age': [70, 75, 80],
            'stimulus_type': ['nostalgia', 'control', 'nostalgia'],
            'perseverative_errors': [10, 12, 8],
            'categories_completed': [5, 4, 6],
            'MMSE': [22, 28, 24],
            'additional_column': ['A', 'B', 'C']
        })
        
        cleaned_df = clean_data(test_data)
        
        # Only P002 (28) and P003 (24) should remain
        assert len(cleaned_df) == 2
        # P002 is at index 1, P003 is at index 2
        assert 1 in cleaned_df.index
        assert 2 in cleaned_df.index
        assert cleaned_df.loc[1, 'additional_column'] == 'B'
        assert cleaned_df.loc[2, 'additional_column'] == 'C'