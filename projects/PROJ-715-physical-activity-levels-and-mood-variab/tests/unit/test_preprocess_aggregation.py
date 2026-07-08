"""
Unit tests for aggregation logic in preprocess.py.

Tests:
- Handling missing ratings (days with < 2 ratings excluded)
- Handling zero steps (recorded as 0, not null)
- Correct calculation of mean and std
"""

import pytest
import pandas as pd
import numpy as np
from datetime import date

# Import functions to test
from preprocess import parse_step_logs, align_ema_mood, compute_daily_aggregates

# Fixtures
@pytest.fixture
def sample_step_data():
    """Sample raw step data."""
    return pd.DataFrame({
        'participant_id': ['P1', 'P1', 'P1', 'P2', 'P2'],
        'timestamp': pd.to_datetime([
            '2023-01-01 08:00:00',
            '2023-01-01 18:00:00',
            '2023-01-02 10:00:00',
            '2023-01-01 09:00:00',
            '2023-01-01 19:00:00'
        ]),
        'steps': [1000, 2000, 0, 5000, 3000]
    })

@pytest.fixture
def sample_mood_data():
    """Sample raw mood data."""
    return pd.DataFrame({
        'participant_id': ['P1', 'P1', 'P1', 'P1', 'P2', 'P2'],
        'timestamp': pd.to_datetime([
            '2023-01-01 09:00:00',
            '2023-01-01 12:00:00',
            '2023-01-01 18:00:00',
            '2023-01-02 10:00:00',
            '2023-01-01 10:00:00',
            '2023-01-01 14:00:00'
        ]),
        'mood_rating': [3.5, 4.0, 3.0, 5.0, 2.0, 2.5] # P2 has 2 ratings on Jan 1
    })

def test_parse_step_logs_aggregation(sample_step_data):
    """Test that step logs are correctly aggregated to daily totals."""
    result = parse_step_logs(sample_step_data)
    
    # P1 on 2023-01-01 should have 3000 steps (1000 + 2000)
    p1_jan1 = result[(result['participant_id'] == 'P1') & (result['date'] == date(2023, 1, 1))]
    assert len(p1_jan1) == 1
    assert p1_jan1['total_steps'].values[0] == 3000
    
    # P1 on 2023-01-02 should have 0 steps
    p1_jan2 = result[(result['participant_id'] == 'P1') & (result['date'] == date(2023, 1, 2))]
    assert len(p1_jan2) == 1
    assert p1_jan2['total_steps'].values[0] == 0
    
    # P2 on 2023-01-01 should have 8000 steps
    p2_jan1 = result[(result['participant_id'] == 'P2') & (result['date'] == date(2023, 1, 1))]
    assert len(p2_jan1) == 1
    assert p2_jan1['total_steps'].values[0] == 8000

def test_align_ema_mood_filtering(sample_mood_data):
    """Test that mood data is correctly aligned and filtered."""
    result = align_ema_mood(sample_mood_data)
    
    # Should have 5 rows (P1 has 3 on Jan 1, 1 on Jan 2; P2 has 2 on Jan 1)
    assert len(result) == 5
    
    # Check P1 Jan 1
    p1_jan1 = result[(result['participant_id'] == 'P1') & (result['date'] == '2023-01-01')]
    assert len(p1_jan1) == 3
    assert set(p1_jan1['mood']) == {3.5, 4.0, 3.0}

def test_compute_daily_aggregates_zero_steps_and_missing_mood(sample_step_data, sample_mood_data):
    """
    Test aggregation logic:
    1. Days with < 2 mood ratings are excluded.
    2. Days with 0 steps are included with total_steps=0.
    3. Correct mean and std calculation.
    """
    step_df = parse_step_logs(sample_step_data)
    mood_df = align_ema_mood(sample_mood_data)
    
    result = compute_daily_aggregates(step_df, mood_df)
    
    # P1 Jan 2 has 1 mood rating -> should be EXCLUDED
    p1_jan2 = result[(result['participant_id'] == 'P1') & (result['date'] == '2023-01-02')]
    assert len(p1_jan2) == 0, "Day with < 2 mood ratings should be excluded."
    
    # P1 Jan 1: steps=3000, mood=[3.5, 4.0, 3.0] -> mean=3.5, std=0.5
    p1_jan1 = result[(result['participant_id'] == 'P1') & (result['date'] == '2023-01-01')]
    assert len(p1_jan1) == 1
    assert p1_jan1['total_steps'].values[0] == 3000
    assert abs(p1_jan1['mean_mood'].values[0] - 3.5) < 0.01
    # std of [3.5, 4.0, 3.0] is 0.5 (population) or 0.61 (sample). Pandas uses sample by default.
    # We expect sample std: sqrt(((0)^2 + (0.5)^2 + (-0.5)^2)/2) = sqrt(0.5/2) = 0.5
    # Actually: (3.5-3.5)^2 + (4-3.5)^2 + (3-3.5)^2 = 0 + 0.25 + 0.25 = 0.5. 0.5/2 = 0.25. sqrt(0.25)=0.5.
    assert abs(p1_jan1['mood_std'].values[0] - 0.5) < 0.01
    
    # P2 Jan 1: steps=8000, mood=[2.0, 2.5] -> mean=2.25, std=0.3535...
    p2_jan1 = result[(result['participant_id'] == 'P2') & (result['date'] == '2023-01-01')]
    assert len(p2_jan1) == 1
    assert p2_jan1['total_steps'].values[0] == 8000
    assert abs(p2_jan1['mean_mood'].values[0] - 2.25) < 0.01
    assert abs(p2_jan1['mood_std'].values[0] - 0.3535533905932738) < 0.0001

def test_handle_zero_steps_explicitly():
    """Test that days with zero steps are recorded as 0, not null."""
    steps = pd.DataFrame({
        'participant_id': ['P1'],
        'timestamp': pd.to_datetime(['2023-01-01 10:00:00']),
        'steps': [0]
    })
    mood = pd.DataFrame({
        'participant_id': ['P1'],
        'timestamp': pd.to_datetime(['2023-01-01 11:00:00', '2023-01-01 12:00:00']),
        'mood_rating': [3.0, 4.0]
    })
    
    step_df = parse_step_logs(steps)
    mood_df = align_ema_mood(mood)
    result = compute_daily_aggregates(step_df, mood_df)
    
    assert result['total_steps'].values[0] == 0
    assert not pd.isna(result['total_steps'].values[0])