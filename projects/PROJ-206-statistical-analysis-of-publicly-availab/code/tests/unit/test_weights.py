"""
test_weights.py - Unit tests for the weights module.

Tests cover:
- Historical RMSE calculation with valid data
- Handling of pollsters with no history (median weight assignment)
- Prevention of division by zero in weight normalization
- Edge cases (single pollster, all NaN RMSE)
"""

import os
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest
import pandas as pd
import numpy as np

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / 'code'))

from src.data.weights import (
    calculate_historical_rmse,
    calculate_weights,
    merge_weights_to_polls
)


@pytest.fixture
def sample_polls():
    """Create a sample poll DataFrame for testing."""
    return pd.DataFrame({
        'date': ['2020-01-01', '2020-02-01', '2020-03-01', '2020-04-01', '2020-05-01'],
        'pollster': ['A', 'A', 'B', 'B', 'C'],
        'vote_share': [50.0, 52.0, 48.0, 51.0, 49.0],
        'sample_size': [1000, 1200, 800, 900, 1100],
        'cycle': [2020, 2020, 2020, 2020, 2020],
        'state': ['US', 'US', 'US', 'US', 'US']
    })


@pytest.fixture
def sample_outcomes():
    """Create a sample election outcomes DataFrame for testing."""
    return pd.DataFrame({
        'cycle': [2016, 2020],
        'actual_vote_share': [48.2, 50.5],
        'candidate': ['D', 'D'],
        'state': ['US', 'US']
    })


@pytest.fixture
def sample_outcomes_multi_cycle():
    """Create sample outcomes for multiple cycles to test out-of-sample logic."""
    return pd.DataFrame({
        'cycle': [2016, 2020, 2024],
        'actual_vote_share': [48.2, 50.5, 51.0],
        'candidate': ['D', 'D', 'R'],
        'state': ['US', 'US', 'US']
    })


def test_calculate_historical_rmse_basic(sample_polls, sample_outcomes):
    """Test basic historical RMSE calculation."""
    rmse_df = calculate_historical_rmse(
        sample_polls, 
        sample_outcomes,
        cycle_col='cycle',
        date_col='date',
        vote_share_col='vote_share',
        actual_col='actual_vote_share',
        pollster_col='pollster'
    )

    assert not rmse_df.empty
    assert 'pollster' in rmse_df.columns
    assert 'cycle' in rmse_df.columns
    assert 'historical_rmse' in rmse_df.columns

    # Check that RMSE is calculated for the correct cycles
    # Since we only have 2020 data and 2016 outcome, 2020 should have RMSE based on 2016
    cycles = rmse_df['cycle'].unique()
    assert 2020 in cycles


def test_calculate_historical_rmse_no_history(sample_polls):
    """Test RMSE calculation when no prior outcomes exist."""
    # Create outcomes only for 2020 (no prior history)
    outcomes_no_history = pd.DataFrame({
        'cycle': [2020],
        'actual_vote_share': [50.5],
        'candidate': ['D'],
        'state': ['US']
    })

    rmse_df = calculate_historical_rmse(
        sample_polls,
        outcomes_no_history,
        cycle_col='cycle',
        date_col='date',
        vote_share_col='vote_share',
        actual_col='actual_vote_share',
        pollster_col='pollster'
    )

    # For 2020, there is no prior history (< 2020), so RMSE should be NaN
    # or the function should handle it gracefully
    assert 'historical_rmse' in rmse_df.columns
    # All RMSE values should be NaN since there's no prior data
    assert rmse_df['historical_rmse'].isna().all()


def test_calculate_weights_no_nan(sample_polls, sample_outcomes_multi_cycle):
    """Test weight calculation when all pollsters have valid RMSE."""
    # Create a mock RMSE DataFrame where all pollsters have valid RMSE
    rmse_df = pd.DataFrame({
        'pollster': ['A', 'A', 'B', 'B', 'C', 'C'],
        'cycle': [2020, 2024, 2020, 2024, 2020, 2024],
        'historical_rmse': [2.0, 1.5, 3.0, 2.5, 1.0, 0.8]
    })

    weights_df = calculate_weights(
        rmse_df,
        cycle_col='cycle',
        rmse_col='historical_rmse',
        pollster_col='pollster'
    )

    assert not weights_df.empty
    assert 'weight' in weights_df.columns

    # Check that weights sum to 1.0 for each cycle
    for cycle in weights_df['cycle'].unique():
        cycle_weights = weights_df[weights_df['cycle'] == cycle]['weight']
        assert np.isclose(cycle_weights.sum(), 1.0, atol=1e-6)


def test_calculate_weights_with_nan_pollsters(sample_polls, sample_outcomes_multi_cycle):
    """Test weight calculation when some pollsters have no history (NaN RMSE)."""
    # Create a mock RMSE DataFrame where pollster C has no history in 2020
    rmse_df = pd.DataFrame({
        'pollster': ['A', 'A', 'B', 'B', 'C', 'C'],
        'cycle': [2020, 2024, 2020, 2024, 2024, 2024],  # C has no 2020 data
        'historical_rmse': [2.0, 1.5, 3.0, 2.5, 1.0, 0.8]
    })

    weights_df = calculate_weights(
        rmse_df,
        cycle_col='cycle',
        rmse_col='historical_rmse',
        pollster_col='pollster'
    )

    assert not weights_df.empty
    assert 'weight' in weights_df.columns

    # Check that weights sum to 1.0 for each cycle
    for cycle in weights_df['cycle'].unique():
        cycle_weights = weights_df[weights_df['cycle'] == cycle]['weight']
        assert np.isclose(cycle_weights.sum(), 1.0, atol=1e-6)

    # Pollster C should have a weight in 2020 (assigned median RMSE)
    c_2020 = weights_df[(weights_df['pollster'] == 'C') & (weights_df['cycle'] == 2020)]
    assert len(c_2020) == 1
    assert c_2020['weight'].iloc[0] > 0


def test_calculate_weights_all_nan():
    """Test weight calculation when all RMSE values are NaN."""
    rmse_df = pd.DataFrame({
        'pollster': ['A', 'B', 'C'],
        'cycle': [2020, 2020, 2020],
        'historical_rmse': [np.nan, np.nan, np.nan]
    })

    weights_df = calculate_weights(
        rmse_df,
        cycle_col='cycle',
        rmse_col='historical_rmse',
        pollster_col='pollster'
    )

    assert not weights_df.empty
    assert 'weight' in weights_df.columns

    # When all RMSE are NaN, they should all get the median (which is NaN -> default 1.0)
    # and then weights should be distributed equally
    cycle_weights = weights_df[weights_df['cycle'] == 2020]['weight']
    expected_weight = 1.0 / 3.0
    for w in cycle_weights:
        assert np.isclose(w, expected_weight, atol=1e-6)


def test_calculate_weights_zero_rmse():
    """Test that division by zero is prevented when RMSE is zero."""
    rmse_df = pd.DataFrame({
        'pollster': ['A', 'B'],
        'cycle': [2020, 2020],
        'historical_rmse': [0.0, 2.0]  # A has perfect RMSE
    })

    weights_df = calculate_weights(
        rmse_df,
        cycle_col='cycle',
        rmse_col='historical_rmse',
        pollster_col='pollster'
    )

    assert not weights_df.empty
    assert 'weight' in weights_df.columns

    # Pollster A should have a very high weight (inverse of near-zero)
    # Pollster B should have a lower weight
    # But weights should still sum to 1.0
    cycle_weights = weights_df[weights_df['cycle'] == 2020]['weight']
    assert np.isclose(cycle_weights.sum(), 1.0, atol=1e-6)

    # A should have a higher weight than B
    a_weight = weights_df[weights_df['pollster'] == 'A']['weight'].iloc[0]
    b_weight = weights_df[weights_df['pollster'] == 'B']['weight'].iloc[0]
    assert a_weight > b_weight


def test_merge_weights_to_polls_basic(sample_polls, sample_outcomes):
    """Test merging weights back to poll data."""
    # First, calculate RMSE and weights
    rmse_df = calculate_historical_rmse(
        sample_polls, 
        sample_outcomes,
        cycle_col='cycle',
        date_col='date',
        vote_share_col='vote_share',
        actual_col='actual_vote_share',
        pollster_col='pollster'
    )

    weights_df = calculate_weights(
        rmse_df,
        cycle_col='cycle',
        rmse_col='historical_rmse',
        pollster_col='pollster'
    )

    # Merge weights to polls
    merged_df = merge_weights_to_polls(
        sample_polls,
        weights_df,
        cycle_col='cycle',
        pollster_col='pollster'
    )

    assert 'weight' in merged_df.columns
    assert len(merged_df) == len(sample_polls)

    # Check that all weights are positive
    assert (merged_df['weight'] > 0).all()


def test_merge_weights_to_polls_missing_pollster(sample_polls, sample_outcomes):
    """Test merging when a pollster has no weights."""
    # Create a poll DataFrame with a new pollster 'D' that has no history
    polls_with_new = sample_polls.copy()
    polls_with_new = pd.concat([polls_with_new, pd.DataFrame({
        'date': ['2020-06-01'],
        'pollster': ['D'],
        'vote_share': [50.0],
        'sample_size': [1000],
        'cycle': [2020],
        'state': ['US']
    })], ignore_index=True)

    rmse_df = calculate_historical_rmse(
        polls_with_new, 
        sample_outcomes,
        cycle_col='cycle',
        date_col='date',
        vote_share_col='vote_share',
        actual_col='actual_vote_share',
        pollster_col='pollster'
    )

    weights_df = calculate_weights(
        rmse_df,
        cycle_col='cycle',
        rmse_col='historical_rmse',
        pollster_col='pollster'
    )

    merged_df = merge_weights_to_polls(
        polls_with_new,
        weights_df,
        cycle_col='cycle',
        pollster_col='pollster'
    )

    # Pollster D should have a weight (assigned via median or equal distribution)
    d_weight = merged_df[merged_df['pollster'] == 'D']['weight'].iloc[0]
    assert d_weight > 0


def test_merge_weights_to_polls_no_weights():
    """Test merging when weights DataFrame is empty."""
    polls_df = pd.DataFrame({
        'date': ['2020-01-01'],
        'pollster': ['A'],
        'vote_share': [50.0],
        'sample_size': [1000],
        'cycle': [2020],
        'state': ['US']
    })

    empty_weights = pd.DataFrame(columns=['pollster', 'cycle', 'weight'])

    merged_df = merge_weights_to_polls(
        polls_df,
        empty_weights,
        cycle_col='cycle',
        pollster_col='pollster'
    )

    # Should have a default weight
    assert 'weight' in merged_df.columns
    assert merged_df['weight'].iloc[0] == 1.0  # Single poll, so weight is 1.0