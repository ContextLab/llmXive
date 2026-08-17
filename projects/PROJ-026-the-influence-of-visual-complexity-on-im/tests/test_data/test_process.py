import pytest
import pandas as pd
import numpy as np
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.data.process import filter_trials, calculate_d_score, aggregate_d_scores

class TestFilterTrials:
    """Unit tests for trial filtering logic (T022)"""
    
    @pytest.fixture
    def sample_data(self):
        """Create sample trial data for testing"""
        return pd.DataFrame({
            'participant_id': ['P1', 'P1', 'P1', 'P1', 'P1', 'P2', 'P2'],
            'session_id': ['S1', 'S1', 'S1', 'S1', 'S1', 'S2', 'S2'],
            'reaction_time': [250, 400, 500, 15000, 600, 350, 800],
            'is_correct': [True, True, False, True, True, True, True]
        })
    
    def test_filters_low_reaction_times(self, sample_data):
        """Test that trials < 300ms are removed"""
        filtered = filter_trials(sample_data, min_rt=300.0)
        
        # Should remove the 250ms trial
        assert len(filtered) == 6  # 7 - 1
        assert all(filtered['reaction_time'] >= 300.0)
    
    def test_filters_high_reaction_times(self, sample_data):
        """Test that trials > 10000ms are removed"""
        filtered = filter_trials(sample_data, max_rt=10000.0)
        
        # Should remove the 15000ms trial
        assert len(filtered) == 6  # 7 - 1
        assert all(filtered['reaction_time'] <= 10000.0)
    
    def test_filters_errors(self, sample_data):
        """Test that incorrect trials are removed"""
        filtered = filter_trials(sample_data)
        
        # Should remove the incorrect trial (is_correct=False)
        assert len(filtered) == 5  # 7 - 1 (low RT) - 1 (high RT) - 1 (error)
        assert all(filtered['is_correct'] == True)
    
    def test_combined_filtering(self, sample_data):
        """Test that all filtering rules work together"""
        filtered = filter_trials(sample_data)
        
        expected_count = 5  # Only valid trials remain
        assert len(filtered) == expected_count
        
        # Verify all remaining trials meet criteria
        assert all(filtered['reaction_time'] >= 300.0)
        assert all(filtered['reaction_time'] <= 10000.0)
        assert all(filtered['is_correct'] == True)
    
    def test_empty_dataframe(self):
        """Test filtering on empty dataframe"""
        empty_df = pd.DataFrame(columns=['reaction_time', 'is_correct'])
        filtered = filter_trials(empty_df)
        assert len(filtered) == 0
    
    def test_all_trials_filtered(self):
        """Test when all trials are invalid"""
        invalid_data = pd.DataFrame({
            'reaction_time': [100, 200, 15000],
            'is_correct': [False, False, False]
        })
        filtered = filter_trials(invalid_data)
        assert len(filtered) == 0
    
    def test_default_thresholds(self, sample_data):
        """Test that default thresholds are 300ms and 10000ms"""
        filtered = filter_trials(sample_data)
        
        # With defaults (300, 10000), should filter out:
        # - 250ms (too low)
        # - 15000ms (too high)
        # - one error
        assert len(filtered) == 5

class TestCalculateDScore:
    """Unit tests for D-score calculation"""
    
    def test_insufficient_trials(self):
        """Test that insufficient trials return NaN"""
        trials = pd.DataFrame({
            'reaction_time': [500, 600, 700],
            'is_correct': [True, True, True]
        })
        d_score = calculate_d_score(trials)
        assert np.isnan(d_score)
    
    def test_valid_d_score_calculation(self):
        """Test D-score calculation with sufficient trials"""
        trials = pd.DataFrame({
            'reaction_time': [500, 600, 700, 800, 900, 1000, 1100, 1200, 1300, 1400],
            'is_correct': [True] * 10
        })
        d_score = calculate_d_score(trials)
        
        # Should return a valid float
        assert not np.isnan(d_score)
        assert d_score >= 0
    
    def test_zero_std_returns_zero(self):
        """Test D-score when all reaction times are identical"""
        trials = pd.DataFrame({
            'reaction_time': [500] * 15,
            'is_correct': [True] * 15
        })
        d_score = calculate_d_score(trials)
        assert d_score == 0.0

class TestAggregateDScores:
    """Integration tests for D-score aggregation"""
    
    @pytest.fixture
    def multi_participant_data(self):
        """Create data with multiple participants and sessions"""
        return pd.DataFrame({
            'participant_id': ['P1', 'P1', 'P1', 'P1', 'P1', 'P1', 'P1', 'P1', 'P1', 'P1',
                             'P2', 'P2', 'P2'],
            'session_id': ['S1', 'S1', 'S1', 'S1', 'S1', 'S1', 'S1', 'S1', 'S1', 'S1',
                         'S2', 'S2', 'S2'],
            'reaction_time': [500, 600, 700, 800, 900, 1000, 1100, 1200, 1300, 1400,
                            400, 500, 600],
            'is_correct': [True] * 13
        })
    
    def test_aggregates_correctly(self, multi_participant_data):
        """Test that aggregation produces correct structure"""
        result = aggregate_d_scores(multi_participant_data)
        
        assert len(result) == 2  # Two participant-session combinations
        assert 'participant_id' in result.columns
        assert 'session_id' in result.columns
        assert 'd_score' in result.columns
        assert 'n_trials_valid' in result.columns
        assert 'status' in result.columns
    
    def test_flags_insufficient_trials(self, multi_participant_data):
        """Test that participants with <10 trials are flagged"""
        result = aggregate_d_scores(multi_participant_data)
        
        # P2 has only 3 trials, should be flagged
        p2_row = result[result['participant_id'] == 'P2']
        assert p2_row.iloc[0]['status'] == 'insufficient_trials'
        assert np.isnan(p2_row.iloc[0]['d_score'])
    
    def test_valid_participants_have_scores(self, multi_participant_data):
        """Test that participants with >=10 trials have valid D-scores"""
        result = aggregate_d_scores(multi_participant_data)
        
        # P1 has 10 trials, should be valid
        p1_row = result[result['participant_id'] == 'P1']
        assert p1_row.iloc[0]['status'] == 'valid'
        assert not np.isnan(p1_row.iloc[0]['d_score'])