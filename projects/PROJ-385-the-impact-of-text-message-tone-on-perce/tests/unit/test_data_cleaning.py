"""
Unit tests for straight-lining detection logic.

This module tests the straight-lining detection logic implemented in
code/03_clean_data.py. It validates that participants with zero variance
across the full set of 24 stimuli are correctly flagged.
"""

import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys

# Add the code directory to the path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import the logic from the cleaning module (or a helper if extracted)
# Since T016 (implementation) is not yet done, we define the logic here
# to test it, assuming the implementation in 03_clean_data.py will match this signature.
# In a real workflow, this logic would be in a shared module or 03_clean_data.py.
# For this test task, we implement the function to be tested.

def detect_straight_liners(ratings_df: pd.DataFrame, stimuli_df: pd.DataFrame) -> pd.DataFrame:
    """
    Detect participants who provided the same rating for all stimuli (straight-lining).

    A participant is flagged as a straight-liner if the variance of their ratings
    across the full set of 24 stimuli is zero.

    Args:
        ratings_df: DataFrame with columns ['participant_id', 'stimulus_id', 'rating']
        stimuli_df: DataFrame with unique stimulus IDs to ensure full coverage check

    Returns:
        DataFrame with columns ['participant_id', 'is_straight_liner']
    """
    if ratings_df.empty:
        return pd.DataFrame(columns=['participant_id', 'is_straight_liner'])

    # Group by participant and calculate variance of ratings
    # We need to ensure we are checking across the full set of stimuli
    # First, check if the participant has ratings for all expected stimuli
    expected_stimuli_count = len(stimuli_df)
    
    participant_stats = ratings_df.groupby('participant_id').agg(
        rating_variance=('rating', 'var'),
        stimulus_count=('stimulus_id', 'nunique')
    ).reset_index()

    # Flag as straight-liner if variance is 0 (or NaN due to single value, but we check count)
    # and they have ratings for all expected stimuli
    participant_stats['is_straight_liner'] = (
        (participant_stats['rating_variance'] == 0) & 
        (participant_stats['stimulus_count'] == expected_stimuli_count)
    )

    # If a participant has all same ratings but missing some stimuli, they are NOT
    # considered a straight-liner for the full set (insufficient data to conclude)
    # However, the task says "zero variance across the full set of 24 stimuli".
    # If they didn't rate all 24, we can't say they zero-var across the full set.
    # So the condition `stimulus_count == expected_stimuli_count` is crucial.

    result = participant_stats[['participant_id', 'is_straight_liner']]
    return result

# Fixtures
@pytest.fixture
def full_stimuli_df():
    """Create a mock stimuli DataFrame with 24 unique IDs."""
    stimuli_ids = [f"S{i:02d}" for i in range(1, 25)]  # S01 to S24
    return pd.DataFrame({'stimulus_id': stimuli_ids})

@pytest.fixture
def clean_ratings_df(full_stimuli_df):
    """Create a valid ratings DataFrame with variance."""
    p_id = "P-ABCD1234"
    data = []
    for i, sid in enumerate(full_stimuli_df['stimulus_id']):
        # Varying ratings
        data.append({
            'participant_id': p_id,
            'stimulus_id': sid,
            'rating': 3 + (i % 3)  # 3, 4, 5, 3, 4, 5...
        })
    return pd.DataFrame(data)

@pytest.fixture
def straight_liner_ratings_df(full_stimuli_df):
    """Create a ratings DataFrame where one participant straight-lines."""
    p_id_clean = "P-CLEAN001"
    p_id_straight = "P-STRAIGHT"
    
    data = []
    # Clean participant
    for i, sid in enumerate(full_stimuli_df['stimulus_id']):
        data.append({
            'participant_id': p_id_clean,
            'stimulus_id': sid,
            'rating': 3 + (i % 3)
        })
    
    # Straight-liner participant (all ratings = 5)
    for sid in full_stimuli_df['stimulus_id']:
        data.append({
            'participant_id': p_id_straight,
            'stimulus_id': sid,
            'rating': 5
        })
    
    return pd.DataFrame(data)

@pytest.fixture
def partial_straight_liner_ratings_df(full_stimuli_df):
    """Create a ratings DataFrame where a participant has zero variance but missing stimuli."""
    p_id_partial = "P-PARTIAL"
    data = []
    # Only rate first 10 stimuli with same value
    for sid in full_stimuli_df['stimulus_id'][:10]:
        data.append({
            'participant_id': p_id_partial,
            'stimulus_id': sid,
            'rating': 4
        })
    return pd.DataFrame(data)

# Tests
def test_detect_straight_liners_identifies_straight_liners(straight_liner_ratings_df, full_stimuli_df):
    """Test that straight-liners are correctly identified."""
    result = detect_straight_liners(straight_liner_ratings_df, full_stimuli_df)
    
    assert 'participant_id' in result.columns
    assert 'is_straight_liner' in result.columns
    
    # Check the straight-liner is flagged
    straight_entry = result[result['participant_id'] == "P-STRAIGHT"]
    assert len(straight_entry) == 1
    assert straight_entry.iloc[0]['is_straight_liner'] is True
    
    # Check the clean participant is not flagged
    clean_entry = result[result['participant_id'] == "P-CLEAN001"]
    assert len(clean_entry) == 1
    assert clean_entry.iloc[0]['is_straight_liner'] is False

def test_detect_straight_liners_ignores_partial_data(partial_straight_liner_ratings_df, full_stimuli_df):
    """Test that participants with zero variance but missing stimuli are NOT flagged."""
    result = detect_straight_liners(partial_straight_liner_ratings_df, full_stimuli_df)
    
    partial_entry = result[result['participant_id'] == "P-PARTIAL"]
    assert len(partial_entry) == 1
    # Should be False because they didn't rate all 24 stimuli
    assert partial_entry.iloc[0]['is_straight_liner'] is False

def test_detect_straight_liners_empty_input(full_stimuli_df):
    """Test behavior with empty ratings DataFrame."""
    empty_df = pd.DataFrame(columns=['participant_id', 'stimulus_id', 'rating'])
    result = detect_straight_liners(empty_df, full_stimuli_df)
    
    assert len(result) == 0
    assert list(result.columns) == ['participant_id', 'is_straight_liner']

def test_detect_straight_liners_single_value_variance_nan(clean_ratings_df, full_stimuli_df):
    """Test that variance calculation handles single value correctly (though not expected in full set)."""
    # This test is more about robustness. If a participant had 1 rating, var is NaN.
    # But our logic requires 24 ratings, so this edge case is covered by count check.
    # We just ensure the function doesn't crash.
    result = detect_straight_liners(clean_ratings_df, full_stimuli_df)
    assert len(result) == 1
    assert result.iloc[0]['is_straight_liner'] is False