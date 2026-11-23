"""
Unit tests for data cleaning logic (T045).

Tests straight-lining detection:
1. Variance < 0.1 exclusion
2. >90% identical ratings exclusion
3. Valid participants are kept
"""
import os
import sys
import pytest
from pathlib import Path
import pandas as pd
import numpy as np

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from data_cleaning import detect_straight_lining, load_survey_data
from config import seed_everything

seed_everything(42)

class TestDataCleaning:
    
    def test_excludes_low_variance(self):
        """Test that participants with variance < 0.1 are excluded."""
        data = {
            'participant_id': [1, 1, 1, 1, 2, 2, 2, 2],
            'rating': [3.0, 3.0, 3.0, 3.0, 1.0, 5.0, 3.0, 4.0] # P1 is straight-lining (var=0), P2 is valid
        }
        df = pd.DataFrame(data)
        
        cleaned_df, excluded_ids = detect_straight_lining(df, variance_threshold=0.1)
        
        assert 1 in excluded_ids, "Participant 1 should be excluded due to low variance"
        assert 2 not in excluded_ids, "Participant 2 should be kept"
        assert len(cleaned_df) == 4, "Should keep 4 rows from participant 2"
    
    def test_excludes_high_identical_ratio(self):
        """Test that participants with >90% identical ratings are excluded."""
        # P1: 9 identical, 1 different (90% -> should be kept if strictly > 90, excluded if >= 90? 
        # Task says >90%. So 9/10 = 0.9 is NOT > 0.9. 
        # Let's make it 10/10 = 1.0 (100%) or 10/11.
        # Let's do 10 identical, 0 different -> 100%
        data = {
            'participant_id': [1] * 10 + [2] * 10,
            'rating': [3.0] * 10 + [1.0, 2.0, 3.0, 4.0, 5.0, 1.0, 2.0, 3.0, 4.0, 5.0]
        }
        df = pd.DataFrame(data)
        
        cleaned_df, excluded_ids = detect_straight_lining(df, identical_ratio_threshold=0.90)
        
        assert 1 in excluded_ids, "Participant 1 (100% identical) should be excluded"
        assert 2 not in excluded_ids, "Participant 2 (mixed) should be kept"
    
    def test_excludes_91_percent_identical(self):
        """Test edge case: 91% identical should be excluded."""
        # 10 items: 9 identical (90%) -> keep. 10 items: 10 identical (100%) -> exclude.
        # Let's try 100 items: 91 identical (91%) -> exclude.
        ids = [1] * 100
        ratings = [3.0] * 91 + [1.0] * 9
        data = {'participant_id': ids, 'rating': ratings}
        df = pd.DataFrame(data)
        
        cleaned_df, excluded_ids = detect_straight_lining(df, identical_ratio_threshold=0.90)
        
        assert 1 in excluded_ids, "Participant with 91% identical ratings should be excluded"
    
    def test_keeps_89_percent_identical(self):
        """Test edge case: 89% identical should be kept."""
        # 100 items: 89 identical (89%) -> keep.
        ids = [1] * 100
        ratings = [3.0] * 89 + [1.0] * 11
        data = {'participant_id': ids, 'rating': ratings}
        df = pd.DataFrame(data)
        
        cleaned_df, excluded_ids = detect_straight_lining(df, identical_ratio_threshold=0.90)
        
        assert 1 not in excluded_ids, "Participant with 89% identical ratings should be kept"
    
    def test_handles_mixed_valid_and_invalid(self):
        """Test dataset with multiple valid and invalid participants."""
        data = {
            'participant_id': [1, 1, 1, 1, 2, 2, 2, 2, 3, 3, 3, 3],
            'rating': [3.0, 3.0, 3.0, 3.0,  # P1: Var=0 (Exclude)
                       1.0, 5.0, 2.0, 4.0,  # P2: Var high (Keep)
                       3.0, 3.0, 3.0, 3.0]  # P3: Var=0 (Exclude)
        }
        df = pd.DataFrame(data)
        
        cleaned_df, excluded_ids = detect_straight_lining(df)
        
        assert 1 in excluded_ids
        assert 3 in excluded_ids
        assert 2 not in excluded_ids
        assert len(cleaned_df) == 4
        assert set(cleaned_df['participant_id'].unique()) == {2}

    def test_empty_dataframe(self):
        """Test handling of empty dataframe."""
        df = pd.DataFrame(columns=['participant_id', 'rating'])
        cleaned_df, excluded_ids = detect_straight_lining(df)
        
        assert len(cleaned_df) == 0
        assert len(excluded_ids) == 0

    def test_non_numeric_ratings(self):
        """Test that non-numeric ratings are dropped."""
        data = {
            'participant_id': [1, 1, 1],
            'rating': [1.0, 'invalid', 3.0]
        }
        df = pd.DataFrame(data)
        
        # Should drop 'invalid' and process the rest. 
        # If only 2 rows left, variance might be calculated or NaN.
        # The function drops NaNs.
        cleaned_df, excluded_ids = detect_straight_lining(df)
        
        # Should have 2 rows left for participant 1
        assert len(cleaned_df) == 2
        assert 1 not in excluded_ids # Variance of 1 and 3 is 2.0, which is > 0.1