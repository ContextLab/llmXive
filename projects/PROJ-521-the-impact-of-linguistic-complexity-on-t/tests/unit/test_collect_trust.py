import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys
import os

# Add code directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))

from collect_trust import process_raw_responses

class TestDataCleaning:
    """Test cases for data cleaning logic in collect_trust.py"""
    
    def test_attention_check_filtering(self):
        """Test that failed attention checks are filtered out"""
        data = {
            'participant_id': ['P1', 'P2', 'P3', 'P4'],
            'text_sample_id': ['T1', 'T2', 'T3', 'T4'],
            'trust_rating': [3, 4, 2, 5],
            'attention_check_status': ['pass', 'fail', 'pass', 'pass']
        }
        df = pd.DataFrame(data)
        
        cleaned_df = process_raw_responses(df)
        
        # Should only have 3 rows (P2 failed)
        assert len(cleaned_df) == 3
        assert 'P2' not in cleaned_df['participant_id'].values
        
    def test_straight_lining_detection_all_ones(self):
        """Test that participants with all 1s are filtered out"""
        data = {
            'participant_id': ['P1', 'P1', 'P1', 'P2', 'P2'],
            'text_sample_id': ['T1', 'T2', 'T3', 'T4', 'T5'],
            'trust_rating': [1, 1, 1, 3, 4],
            'attention_check_status': ['pass', 'pass', 'pass', 'pass', 'pass']
        }
        df = pd.DataFrame(data)
        
        cleaned_df = process_raw_responses(df)
        
        # P1 should be filtered out (all 1s)
        assert len(cleaned_df) == 2
        assert 'P1' not in cleaned_df['participant_id'].values
        
    def test_straight_lining_detection_all_fives(self):
        """Test that participants with all 5s are filtered out"""
        data = {
            'participant_id': ['P1', 'P1', 'P1', 'P2', 'P2'],
            'text_sample_id': ['T1', 'T2', 'T3', 'T4', 'T5'],
            'trust_rating': [5, 5, 5, 3, 4],
            'attention_check_status': ['pass', 'pass', 'pass', 'pass', 'pass']
        }
        df = pd.DataFrame(data)
        
        cleaned_df = process_raw_responses(df)
        
        # P1 should be filtered out (all 5s)
        assert len(cleaned_df) == 2
        assert 'P1' not in cleaned_df['participant_id'].values
        
    def test_valid_ratings_preserved(self):
        """Test that valid ratings (1-5) are preserved"""
        data = {
            'participant_id': ['P1', 'P1', 'P2', 'P2'],
            'text_sample_id': ['T1', 'T2', 'T3', 'T4'],
            'trust_rating': [1, 5, 3, 4],
            'attention_check_status': ['pass', 'pass', 'pass', 'pass']
        }
        df = pd.DataFrame(data)
        
        cleaned_df = process_raw_responses(df)
        
        # All should be preserved
        assert len(cleaned_df) == 4
        
    def test_invalid_ratings_removed(self):
        """Test that invalid ratings (<1 or >5) are removed"""
        data = {
            'participant_id': ['P1', 'P1', 'P2', 'P2'],
            'text_sample_id': ['T1', 'T2', 'T3', 'T4'],
            'trust_rating': [0, 1, 5, 6],
            'attention_check_status': ['pass', 'pass', 'pass', 'pass']
        }
        df = pd.DataFrame(data)
        
        cleaned_df = process_raw_responses(df)
        
        # Only ratings 1 and 5 should remain
        assert len(cleaned_df) == 2
        assert set(cleaned_df['trust_rating']) == {1, 5}
        
    def test_mixed_straight_lining_and_attention_fail(self):
        """Test filtering when both straight-lining and attention fail occur"""
        data = {
            'participant_id': ['P1', 'P1', 'P2', 'P3', 'P3', 'P4'],
            'text_sample_id': ['T1', 'T2', 'T3', 'T4', 'T5', 'T6'],
            'trust_rating': [1, 1, 3, 5, 5, 4],
            'attention_check_status': ['pass', 'pass', 'fail', 'pass', 'pass', 'pass']
        }
        df = pd.DataFrame(data)
        
        cleaned_df = process_raw_responses(df)
        
        # P1: straight-liner (all 1s) -> removed
        # P2: attention fail -> removed
        # P3: straight-liner (all 5s) -> removed
        # P4: valid -> kept
        assert len(cleaned_df) == 1
        assert cleaned_df['participant_id'].iloc[0] == 'P4'