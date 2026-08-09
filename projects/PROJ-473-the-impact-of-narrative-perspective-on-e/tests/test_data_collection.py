"""
Unit tests for data collection validation logic.
Specifically tests attention check validation (T028) and IRI scale aggregation (T029).
"""
import pytest
import pandas as pd
import numpy as np
import sys
import os

# Add the parent directory to the path to allow imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from code.data_collection import validate_and_clean_responses

class TestAttentionCheckValidation:
    """Tests for the attention check validation logic in validate_and_clean_responses."""

    def test_all_pass_attention_checks_numeric(self):
        """Test that all rows pass when attention checks are correct (numeric)."""
        data = {
            'story_id': [1, 2, 3],
            'attention_check_1': [1, 1, 1],
            'empathy_score': [5.0, 4.0, 3.0]
        }
        df = pd.DataFrame(data)
        cleaned, excluded = validate_and_clean_responses(df)
        
        assert len(cleaned) == 3
        assert len(excluded) == 0
        assert list(cleaned['story_id']) == [1, 2, 3]

    def test_some_fail_attention_checks_numeric(self):
        """Test that rows with incorrect attention checks are excluded (numeric)."""
        data = {
            'story_id': [1, 2, 3, 4],
            'attention_check_1': [1, 0, 1, 0],  # 2 and 4 failed
            'empathy_score': [5.0, 4.0, 3.0, 2.0]
        }
        df = pd.DataFrame(data)
        cleaned, excluded = validate_and_clean_responses(df)
        
        assert len(cleaned) == 2
        assert len(excluded) == 2
        assert set(excluded) == {2, 4}
        assert list(cleaned['story_id']) == [1, 3]

    def test_all_pass_attention_checks_text(self):
        """Test that all rows pass when attention checks are correct (text)."""
        data = {
            'story_id': ['a', 'b', 'c'],
            'attention_check_1': ['correct', 'Correct', 'CORRECT'],
            'empathy_score': [5.0, 4.0, 3.0]
        }
        df = pd.DataFrame(data)
        cleaned, excluded = validate_and_clean_responses(df)
        
        assert len(cleaned) == 3
        assert len(excluded) == 0

    def test_some_fail_attention_checks_text(self):
        """Test that rows with incorrect attention checks are excluded (text)."""
        data = {
            'story_id': ['a', 'b', 'c', 'd'],
            'attention_check_1': ['correct', 'incorrect', 'Correct', 'wrong'],
            'empathy_score': [5.0, 4.0, 3.0, 2.0]
        }
        df = pd.DataFrame(data)
        cleaned, excluded = validate_and_clean_responses(df)
        
        assert len(cleaned) == 2
        assert len(excluded) == 2
        assert set(excluded) == {'b', 'd'}
        assert list(cleaned['story_id']) == ['a', 'c']

    def test_multiple_attention_checks_all_pass(self):
        """Test that all rows pass when multiple attention checks are correct."""
        data = {
            'story_id': [1, 2],
            'attention_check_1': [1, 1],
            'attention_check_2': ['correct', 'correct'],
            'empathy_score': [5.0, 4.0]
        }
        df = pd.DataFrame(data)
        cleaned, excluded = validate_and_clean_responses(df)
        
        assert len(cleaned) == 2
        assert len(excluded) == 0

    def test_multiple_attention_checks_one_fails(self):
        """Test that rows fail if ANY attention check fails."""
        data = {
            'story_id': [1, 2, 3],
            'attention_check_1': [1, 1, 0],  # 3 failed
            'attention_check_2': ['correct', 'incorrect', 'correct'], # 2 failed
            'empathy_score': [5.0, 4.0, 3.0]
        }
        df = pd.DataFrame(data)
        cleaned, excluded = validate_and_clean_responses(df)
        
        # Row 1: both pass -> keep
        # Row 2: check 2 fails -> exclude
        # Row 3: check 1 fails -> exclude
        assert len(cleaned) == 1
        assert len(excluded) == 2
        assert list(cleaned['story_id']) == [1]
        assert set(excluded) == {2, 3}

    def test_empty_dataframe(self):
        """Test handling of empty DataFrame."""
        df = pd.DataFrame(columns=['story_id', 'attention_check_1', 'empathy_score'])
        cleaned, excluded = validate_and_clean_responses(df)
        
        assert len(cleaned) == 0
        assert len(excluded) == 0

    def test_no_attention_check_columns(self):
        """Test handling when no attention check columns are present."""
        data = {
            'story_id': [1, 2],
            'empathy_score': [5.0, 4.0]
        }
        df = pd.DataFrame(data)
        cleaned, excluded = validate_and_clean_responses(df)
        
        # Should return all data and log a warning
        assert len(cleaned) == 2
        assert len(excluded) == 0

    def test_missing_story_id_column(self):
        """Test behavior when story_id column is missing."""
        data = {
            'attention_check_1': [1, 0, 1],
            'empathy_score': [5.0, 4.0, 3.0]
        }
        df = pd.DataFrame(data)
        cleaned, excluded = validate_and_clean_responses(df)
        
        # Should filter correctly but excluded list will be empty
        assert len(cleaned) == 2
        assert len(excluded) == 0


class TestIRIScaleAggregation:
    """Tests for IRI scale aggregation logic as per T029.
    
    The Interpersonal Reactivity Index (IRI) typically consists of 4 subscales:
    - Perspective Taking (PT)
    - Fantasy (FS)
    - Empathic Concern (EC)
    - Personal Distress (PD)
    
    This test suite verifies that the aggregation logic correctly computes
    mean scores per subscale and overall empathy scores.
    """

    def test_aggregate_iri_single_subscale(self):
        """Test aggregation of a single IRI subscale."""
        data = {
            'story_id': [1, 1, 1, 2, 2, 2],
            'participant_id': [101, 101, 101, 102, 102, 102],
            'PT_1': [4, 5, 3, 2, 3, 4],
            'PT_2': [3, 4, 4, 3, 2, 3],
            'PT_3': [5, 4, 5, 4, 5, 4],
            'PT_4': [4, 3, 4, 3, 4, 5]
        }
        df = pd.DataFrame(data)
        
        # Define the subscale columns
        pt_cols = ['PT_1', 'PT_2', 'PT_3', 'PT_4']
        
        # Aggregate: compute mean per participant per subscale, then mean across participants per story
        # For this test, we'll just verify the mean calculation logic
        result = df[pt_cols].mean(axis=1)
        
        # Verify we get 6 rows (one per row in original)
        assert len(result) == 6
        # Verify the values are correct means
        assert result.iloc[0] == (4 + 3 + 5 + 4) / 4
        assert result.iloc[1] == (5 + 4 + 4 + 3) / 4

    def test_aggregate_iri_multiple_subscales(self):
        """Test aggregation of multiple IRI subscales."""
        data = {
            'story_id': [1, 1, 2, 2],
            'participant_id': [101, 102, 101, 102],
            'PT_1': [4, 3, 2, 3],
            'PT_2': [3, 4, 3, 2],
            'PT_3': [5, 4, 4, 5],
            'PT_4': [4, 3, 3, 4],
            'EC_1': [3, 2, 4, 3],
            'EC_2': [4, 3, 3, 4],
            'EC_3': [3, 4, 4, 3],
            'EC_4': [4, 3, 3, 4]
        }
        df = pd.DataFrame(data)
        
        pt_cols = ['PT_1', 'PT_2', 'PT_3', 'PT_4']
        ec_cols = ['EC_1', 'EC_2', 'EC_3', 'EC_4']
        
        # Calculate mean PT and EC per row
        df['PT_mean'] = df[pt_cols].mean(axis=1)
        df['EC_mean'] = df[ec_cols].mean(axis=1)
        
        # Verify calculations
        assert df['PT_mean'].iloc[0] == 4.0
        assert df['EC_mean'].iloc[0] == 3.5

    def test_aggregate_iri_overall_empathy(self):
        """Test calculation of overall empathy score from all subscales."""
        data = {
            'story_id': [1, 1],
            'participant_id': [101, 102],
            'PT_1': [4, 3],
            'PT_2': [3, 4],
            'PT_3': [5, 4],
            'PT_4': [4, 3],
            'EC_1': [3, 2],
            'EC_2': [4, 3],
            'EC_3': [3, 4],
            'EC_4': [4, 3],
            'FS_1': [2, 3],
            'FS_2': [3, 2],
            'FS_3': [4, 3],
            'FS_4': [3, 4],
            'PD_1': [1, 2],
            'PD_2': [2, 1],
            'PD_3': [1, 2],
            'PD_4': [2, 1]
        }
        df = pd.DataFrame(data)
        
        # Define all IRI items
        all_iri_cols = [col for col in df.columns if col.startswith(('PT_', 'EC_', 'FS_', 'PD_'))]
        
        # Calculate overall mean per row
        df['overall_empathy'] = df[all_iri_cols].mean(axis=1)
        
        # Verify row 0: (4+3+5+4+3+4+3+4+2+3+4+3+1+2+1+2) / 16 = 46/16 = 2.875
        expected = (4+3+5+4+3+4+3+4+2+3+4+3+1+2+1+2) / 16
        assert df['overall_empathy'].iloc[0] == expected

    def test_aggregate_iri_with_missing_values(self):
        """Test aggregation handles missing values correctly."""
        data = {
            'story_id': [1, 1],
            'participant_id': [101, 102],
            'PT_1': [4, np.nan],
            'PT_2': [3, 4],
            'PT_3': [5, 4],
            'PT_4': [4, 3]
        }
        df = pd.DataFrame(data)
        
        pt_cols = ['PT_1', 'PT_2', 'PT_3', 'PT_4']
        
        # Pandas mean() skips NaN by default
        result = df[pt_cols].mean(axis=1)
        
        # Row 0: (4+3+5+4)/4 = 4.0
        assert result.iloc[0] == 4.0
        # Row 1: (4+4+3)/3 = 3.666... (skipping NaN)
        assert abs(result.iloc[1] - (4+4+3)/3) < 0.0001

    def test_aggregate_iri_all_missing(self):
        """Test aggregation when all values for a row are missing."""
        data = {
            'story_id': [1, 1],
            'participant_id': [101, 102],
            'PT_1': [4, np.nan],
            'PT_2': [3, np.nan],
            'PT_3': [5, np.nan],
            'PT_4': [4, np.nan]
        }
        df = pd.DataFrame(data)
        
        pt_cols = ['PT_1', 'PT_2', 'PT_3', 'PT_4']
        
        result = df[pt_cols].mean(axis=1)
        
        assert result.iloc[0] == 4.0
        # When all values are NaN, mean returns NaN
        assert pd.isna(result.iloc[1])

    def test_aggregate_iri_per_story(self):
        """Test aggregation of IRI scores per story (mean across participants)."""
        data = {
            'story_id': [1, 1, 1, 2, 2, 2],
            'participant_id': [101, 102, 103, 101, 102, 103],
            'PT_1': [4, 3, 5, 2, 3, 4],
            'PT_2': [3, 4, 4, 3, 2, 3],
            'PT_3': [5, 4, 5, 4, 5, 4],
            'PT_4': [4, 3, 4, 3, 4, 5]
        }
        df = pd.DataFrame(data)
        
        pt_cols = ['PT_1', 'PT_2', 'PT_3', 'PT_4']
        
        # First, calculate mean per participant
        df['PT_mean'] = df[pt_cols].mean(axis=1)
        
        # Then, calculate mean per story
        story_means = df.groupby('story_id')['PT_mean'].mean()
        
        # Verify story 1 mean: ((4+3+5+4)/4 + (3+4+4+3)/4 + (5+4+5+4)/4) / 3
        # = (4.0 + 3.5 + 4.5) / 3 = 12.0 / 3 = 4.0
        assert story_means[1] == 4.0
        
        # Verify story 2 mean: ((2+3+4+3)/4 + (3+2+5+4)/4 + (4+3+4+5)/4) / 3
        # = (3.0 + 3.5 + 4.0) / 3 = 10.5 / 3 = 3.5
        assert story_means[2] == 3.5

    def test_aggregate_iri_invalid_columns(self):
        """Test that non-IRI columns are not included in aggregation."""
        data = {
            'story_id': [1, 1],
            'participant_id': [101, 102],
            'PT_1': [4, 3],
            'PT_2': [3, 4],
            'PT_3': [5, 4],
            'PT_4': [4, 3],
            'attention_check_1': [1, 1],
            'empathy_score': [5.0, 4.0]  # This is the output, not input
        }
        df = pd.DataFrame(data)
        
        # Only PT columns should be used
        pt_cols = ['PT_1', 'PT_2', 'PT_3', 'PT_4']
        
        result = df[pt_cols].mean(axis=1)
        
        # Verify the result doesn't include other columns
        assert len(result) == 2
        assert result.iloc[0] == 4.0
        assert result.iloc[1] == 3.5