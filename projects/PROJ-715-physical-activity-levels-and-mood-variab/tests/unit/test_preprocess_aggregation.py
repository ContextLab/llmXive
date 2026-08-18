import pytest
import pandas as pd
import numpy as np
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

def test_zero_steps_handling():
    """Test that zero steps are recorded as 0."""
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
    assert result['total_steps'].iloc[0] == 0
