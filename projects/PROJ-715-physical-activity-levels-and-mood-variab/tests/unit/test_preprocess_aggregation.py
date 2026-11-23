import pytest
import pandas as pd
import numpy as np
import sys
import os

# Ensure code directory is in path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'code'))

from preprocess import compute_daily_aggregates

def test_aggregation_logic():
    """Test aggregation logic with known inputs."""
    # Mock daily steps
    steps_df = pd.DataFrame({
        'participant_id': ['P1', 'P1', 'P2'],
        'date': pd.to_datetime(['2023-01-01', '2023-01-01', '2023-01-01']),
        'total_steps': [5000, 5000, 0]
    })

    # Mock mood data
    mood_df = pd.DataFrame({
        'participant_id': ['P1', 'P1', 'P1', 'P2', 'P2'],
        'date': pd.to_datetime(['2023-01-01', '2023-01-01', '2023-01-01', '2023-01-01', '2023-01-01']),
        'mood': [5.0, 5.0, 5.0, 3.0, 4.0]
    })

    result = compute_daily_aggregates(steps_df, mood_df)

    # P1: 3 ratings, mean=5, std=0
    p1 = result[result['participant_id'] == 'P1'].iloc[0]
    assert p1['n_mood_ratings'] == 3
    assert p1['mean_mood'] == 5.0
    assert p1['mood_std'] == 0.0
    assert p1['total_steps'] == 5000

    # P2: 2 ratings, mean=3.5, std=0.707...
    p2 = result[result['participant_id'] == 'P2'].iloc[0]
    assert p2['n_mood_ratings'] == 2
    assert p2['mean_mood'] == 3.5
    assert np.isclose(p2['mood_std'], np.std([3, 4]))

def test_insufficient_ratings_excluded():
    """Test that days with <2 ratings are excluded."""
    steps_df = pd.DataFrame({
        'participant_id': ['P1'],
        'date': pd.to_datetime(['2023-01-01']),
        'total_steps': [1000]
    })

    mood_df = pd.DataFrame({
        'participant_id': ['P1'],
        'date': pd.to_datetime(['2023-01-01']),
        'mood': [5.0]
    })

    result = compute_daily_aggregates(steps_df, mood_df)
    assert len(result) == 0

def test_aggregate_handles_zero_steps():
    """Test that days with zero steps are recorded as 0 and not dropped."""
    steps_df = pd.DataFrame({
        'participant_id': ['P1'],
        'date': pd.to_datetime(['2023-01-01']),
        'total_steps': [0]
    })
    mood_df = pd.DataFrame({
        'participant_id': ['P1'],
        'date': pd.to_datetime(['2023-01-01']),
        'mood': [5.0, 6.0]
    })
    result = compute_daily_aggregates(steps_df, mood_df)
    
    # Ensure the row exists
    assert len(result) == 1
    # Ensure total_steps is explicitly 0, not NaN or dropped
    assert result['total_steps'].iloc[0] == 0
    assert result['n_mood_ratings'].iloc[0] == 2
    assert result['mean_mood'].iloc[0] == 5.5

def test_missing_steps_treated_as_zero():
    """Test that missing step counts (NaN in input) are treated as 0."""
    steps_df = pd.DataFrame({
        'participant_id': ['P1'],
        'date': pd.to_datetime(['2023-01-01']),
        'total_steps': [np.nan]
    })
    mood_df = pd.DataFrame({
        'participant_id': ['P1'],
        'date': pd.to_datetime(['2023-01-01']),
        'mood': [5.0, 6.0]
    })
    result = compute_daily_aggregates(steps_df, mood_df)
    
    # Ensure the row exists and steps are 0
    assert len(result) == 1
    assert result['total_steps'].iloc[0] == 0