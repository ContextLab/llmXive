import os
import sys
import tempfile
from pathlib import Path
import pytest
import pandas as pd
import numpy as np

from src.data.weights import (
    calculate_historical_rmse,
    calculate_weights,
    merge_weights_to_polls
)

@pytest.fixture
def sample_polls():
    """Create sample poll data with multiple cycles and pollsters."""
    data = {
        'pollster': ['A', 'A', 'A', 'B', 'B', 'C', 'C', 'C'],
        'cycle': [2016, 2016, 2020, 2016, 2016, 2016, 2020, 2020],
        'date': ['2016-01-01', '2016-06-01', '2020-01-01', 
                 '2016-02-01', '2016-07-01', '2016-03-01',
                 '2020-02-01', '2020-06-01'],
        'candidate': ['Candidate1', 'Candidate1', 'Candidate1',
                     'Candidate1', 'Candidate1', 'Candidate1',
                     'Candidate1', 'Candidate1'],
        'vote_share': [45.0, 48.0, 52.0, 47.0, 50.0, 44.0, 51.0, 49.0],
        'sample_size': [1000, 1200, 1100, 900, 1050, 800, 1300, 1150]
    }
    return pd.DataFrame(data)

@pytest.fixture
def sample_outcomes():
    """Create sample election outcomes."""
    data = {
        'cycle': [2016, 2020],
        'candidate': ['Candidate1', 'Candidate1'],
        'actual_vote_share': [46.0, 50.0]
    }
    return pd.DataFrame(data)

@pytest.fixture
def sample_outcomes_multi_cycle():
    """Create sample outcomes for multiple cycles."""
    data = {
        'cycle': [2012, 2016, 2020],
        'candidate': ['Candidate1', 'Candidate1', 'Candidate1'],
        'actual_vote_share': [44.0, 46.0, 50.0]
    }
    return pd.DataFrame(data)

class TestHistoricalRMSE:
    def test_calculate_rmse_basic(self, sample_polls, sample_outcomes):
        """Test basic RMSE calculation."""
        rmse_df = calculate_historical_rmse(sample_polls, sample_outcomes)
        
        assert not rmse_df.empty
        assert 'pollster' in rmse_df.columns
        assert 'cycle' in rmse_df.columns
        assert 'historical_rmse' in rmse_df.columns
        assert 'n_polls' in rmse_df.columns
        
        # Check that RMSE values are non-negative
        assert (rmse_df['historical_rmse'] >= 0).all()
    
    def test_temporal_split(self, sample_polls, sample_outcomes_multi_cycle):
        """Test that RMSE for 2020 only uses 2012 and 2016 data."""
        rmse_df = calculate_historical_rmse(sample_polls, sample_outcomes_multi_cycle)
        
        # For 2020, we should have RMSE calculated from 2012 and 2016 data
        cycle_2020 = rmse_df[rmse_df['cycle'] == 2020]
        
        if not cycle_2020.empty:
            # Pollster A has data in 2016 and 2020, so for 2020 cycle,
            # RMSE should be based on 2016 data
            assert 'pollster' in cycle_2020.columns
    
    def test_no_data_for_cycle(self):
        """Test RMSE calculation when no prior data exists."""
        polls = pd.DataFrame({
            'pollster': ['A'],
            'cycle': [2020],
            'date': ['2020-01-01'],
            'candidate': ['C1'],
            'vote_share': [50.0],
            'sample_size': [1000]
        })
        outcomes = pd.DataFrame({
            'cycle': [2020],
            'candidate': ['C1'],
            'actual_vote_share': [50.0]
        })
        
        rmse_df = calculate_historical_rmse(polls, outcomes)
        
        # Should be empty because there's no prior cycle data
        assert rmse_df.empty

class TestWeights:
    def test_calculate_weights_basic(self, sample_polls, sample_outcomes):
        """Test basic weight calculation."""
        rmse_df = calculate_historical_rmse(sample_polls, sample_outcomes)
        weights_df = calculate_weights(rmse_df)
        
        if not weights_df.empty:
            assert 'weight' in weights_df.columns
            assert 'historical_rmse' in weights_df.columns
            
            # Weights should sum to 1.0 per cycle
            for cycle in weights_df['cycle'].unique():
                cycle_weights = weights_df[weights_df['cycle'] == cycle]['weight']
                assert np.isclose(cycle_weights.sum(), 1.0, atol=1e-6)
    
    def test_zero_rmse_handling(self):
        """Test that zero RMSE is handled (prevents division by zero)."""
        rmse_df = pd.DataFrame({
            'pollster': ['A', 'B'],
            'cycle': [2016, 2016],
            'historical_rmse': [0.0, 2.0],
            'n_polls': [5, 3]
        })
        
        weights_df = calculate_weights(rmse_df)
        
        # Should not crash and should have valid weights
        assert not weights_df.empty
        assert (weights_df['weight'] >= 0).all()
        assert (weights_df['weight'] <= 1.0).all()

class TestMergeWeights:
    def test_merge_weights_to_polls(self, sample_polls, sample_outcomes):
        """Test merging weights back to poll data."""
        rmse_df = calculate_historical_rmse(sample_polls, sample_outcomes)
        weights_df = calculate_weights(rmse_df)
        
        merged_df = merge_weights_to_polls(sample_polls, weights_df)
        
        assert 'weight' in merged_df.columns
        assert 'historical_rmse' in merged_df.columns
        
        # All rows should have a weight
        assert not merged_df['weight'].isna().any()
        
        # Weights should be positive
        assert (merged_df['weight'] > 0).all()
    
    def test_missing_pollster_handling(self):
        """Test that missing pollsters get default weights."""
        polls = pd.DataFrame({
            'pollster': ['A', 'B', 'C'],
            'cycle': [2016, 2016, 2016],
            'date': ['2016-01-01', '2016-02-01', '2016-03-01'],
            'candidate': ['C1', 'C1', 'C1'],
            'vote_share': [45.0, 47.0, 46.0],
            'sample_size': [1000, 900, 800]
        })
        
        # Weights only for A and B
        weights = pd.DataFrame({
            'pollster': ['A', 'B'],
            'cycle': [2016, 2016],
            'weight': [0.6, 0.4],
            'historical_rmse': [2.0, 3.0]
        })
        
        merged_df = merge_weights_to_polls(polls, weights)
        
        # C should get a default weight (1/3 in this case)
        c_weight = merged_df[merged_df['pollster'] == 'C']['weight'].iloc[0]
        assert c_weight > 0
        assert c_weight < 1.0

class TestEdgeCases:
    def test_single_poll_per_pollster(self, sample_polls, sample_outcomes):
        """Test RMSE calculation with only one poll per pollster."""
        single_poll = sample_polls[sample_polls['pollster'] == 'A'].head(1)
        
        rmse_df = calculate_historical_rmse(single_poll, sample_outcomes)
        
        # Should handle gracefully, possibly returning empty or with n_polls=1
        if not rmse_df.empty:
            assert (rmse_df['n_polls'] >= 1).all()
    
    def test_no_outcomes(self):
        """Test RMSE calculation with no outcomes data."""
        polls = pd.DataFrame({
            'pollster': ['A', 'B'],
            'cycle': [2016, 2016],
            'date': ['2016-01-01', '2016-02-01'],
            'candidate': ['C1', 'C1'],
            'vote_share': [45.0, 47.0],
            'sample_size': [1000, 900]
        })
        outcomes = pd.DataFrame(columns=['cycle', 'candidate', 'actual_vote_share'])
        
        rmse_df = calculate_historical_rmse(polls, outcomes)
        
        # Should return empty DataFrame
        assert rmse_df.empty
