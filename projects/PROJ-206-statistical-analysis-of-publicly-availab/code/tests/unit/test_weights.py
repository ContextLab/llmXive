"""
Unit tests for the weights calculation module.
"""

import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys

# Add code root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from src.data.weights import calculate_historical_rmse, calculate_weights, merge_weights_to_polls


@pytest.fixture
def sample_polls():
    """
    Creates a simple poll dataset spanning two cycles.
    Cycle 2020: Polls from 2016 (historical) and 2020 (current).
    Cycle 2024: Polls from 2020 (historical) and 2024 (current).
    """
    data = {
        'pollster': ['A', 'A', 'A', 'B', 'B', 'A', 'A'],
        'cycle': [2016, 2016, 2020, 2016, 2020, 2020, 2024],
        'candidate': ['Dem', 'Dem', 'Dem', 'Dem', 'Dem', 'Dem', 'Dem'],
        'date': ['2016-01-01', '2016-06-01', '2020-01-01', '2016-02-01', '2020-02-01', '2020-06-01', '2024-01-01'],
        'vote_share': [50.0, 52.0, 48.0, 45.0, 55.0, 49.0, 51.0]
    }
    return pd.DataFrame(data)


@pytest.fixture
def sample_outcomes():
    """
    Election outcomes for 2016, 2020, 2024.
    """
    data = {
        'cycle': [2016, 2020, 2024],
        'candidate': ['Dem', 'Dem', 'Dem'],
        'actual_vote_share': [50.0, 50.0, 50.0]
    }
    return pd.DataFrame(data)


def test_calculate_historical_rmse_strict_split(sample_polls, sample_outcomes):
    """
    Test that RMSE is calculated using strictly previous cycles.
    For Cycle 2020, it should use 2016 data.
    For Cycle 2024, it should use 2016 and 2020 data.
    For Cycle 2016, it should return nothing (no history).
    """
    rmse_df = calculate_historical_rmse(
        sample_polls, 
        sample_outcomes,
        cycle_col='cycle',
        candidate_col='candidate',
        vote_share_col='vote_share',
        actual_share_col='actual_vote_share'
    )
    
    # Check that 2016 is not in the result (no history)
    assert 2016 not in rmse_df['cycle'].values, "Cycle 2016 should not have RMSE (no history)."
    
    # Check that 2020 exists
    assert 2020 in rmse_df['cycle'].values, "Cycle 2020 should have RMSE."
    
    # Check that 2024 exists
    assert 2024 in rmse_df['cycle'].values, "Cycle 2024 should have RMSE."
    
    # Verify specific values for Pollster A in Cycle 2020 (using 2016 data)
    # 2016 Polls for A: 50.0 (Actual 50.0), 52.0 (Actual 50.0)
    # Errors: 0, 2. Squared: 0, 4. Mean: 2. RMSE: sqrt(2) approx 1.414
    a_2020 = rmse_df[(rmse_df['pollster'] == 'A') & (rmse_df['cycle'] == 2020)]
    assert not a_2020.empty
    assert np.isclose(a_2020['rmse'].values[0], np.sqrt(2.0), rtol=1e-4)


def test_calculate_weights_normalization():
    """
    Test that weights sum to 1.0 per cycle.
    """
    data = {
        'pollster': ['A', 'B', 'A'],
        'cycle': [2020, 2020, 2024],
        'rmse': [1.0, 2.0, 1.0],
        'sample_count': [10, 10, 10]
    }
    df = pd.DataFrame(data)
    
    weights_df = calculate_weights(df)
    
    # Check sum for 2020
    sum_2020 = weights_df[weights_df['cycle'] == 2020]['normalized_weight'].sum()
    assert np.isclose(sum_2020, 1.0), f"Cycle 2020 weights sum to {sum_2020}, expected 1.0"
    
    # Check sum for 2024
    sum_2024 = weights_df[weights_df['cycle'] == 2024]['normalized_weight'].sum()
    assert np.isclose(sum_2024, 1.0), f"Cycle 2024 weights sum to {sum_24}, expected 1.0"


def test_calculate_weights_zero_rmse():
    """
    Test that zero RMSE does not cause division by zero.
    """
    data = {
        'pollster': ['A'],
        'cycle': [2020],
        'rmse': [0.0],
        'sample_count': [10]
    }
    df = pd.DataFrame(data)
    
    # Should not raise an error
    weights_df = calculate_weights(df)
    
    assert not weights_df.empty
    assert weights_df['normalized_weight'].values[0] == 1.0 # Single pollster gets 1.0


def test_merge_weights_to_polls(sample_polls, sample_outcomes):
    """
    Test merging weights back to polls.
    """
    rmse_df = calculate_historical_rmse(sample_polls, sample_outcomes)
    weights_df = calculate_weights(rmse_df)
    
    merged = merge_weights_to_polls(sample_polls, weights_df)
    
    # Check that weight column exists
    assert 'normalized_weight' in merged.columns
    
    # Check that 2016 polls (no history) get default weight (and then normalized)
    # In 2016, no one has history. So all get default. Then normalized to 1/N.
    polls_2016 = merged[merged['cycle'] == 2016]
    # Should have weights
    assert not polls_2016['normalized_weight'].isna().any()
    
    # Check that 2020 polls have calculated weights
    polls_2020 = merged[merged['cycle'] == 2020]
    assert not polls_2020['normalized_weight'].isna().any()
    
    # Verify sum of weights for 2020 is 1.0
    sum_2020 = polls_2020['normalized_weight'].sum()
    assert np.isclose(sum_2020, 1.0)