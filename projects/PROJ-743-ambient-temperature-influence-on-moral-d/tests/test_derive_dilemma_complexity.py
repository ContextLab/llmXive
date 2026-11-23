import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
import os

from derive_dilemma_complexity import calculate_complexity_score, derive_complexity

@pytest.fixture
def sample_data():
    """Create a mock DataFrame similar to Moral Machine data."""
    data = {
        'participant_id': ['p1', 'p2', 'p3'],
        'dilemma_id': ['d1', 'd2', 'd3'],
        'n_pedestrians': [1, 5, 2],
        'n_passengers': [2, 1, 3],
        'dilemma_type': ['same', 'different', 'sides_conflict'],
        'response_time': [1500, 2000, 1800] # Should NOT be used
    }
    return pd.DataFrame(data)

def test_calculate_complexity_score_basic(sample_data):
    """Test that complexity is calculated based on lives."""
    row = sample_data.iloc[0]
    score = calculate_complexity_score(row)
    # 1 pedestrian + 2 passengers = 3 lives. Base score = 3.
    assert score == 3.0

def test_calculate_complexity_score_sides_conflict(sample_data):
    """Test that sides conflict adds complexity."""
    row = sample_data.iloc[2]
    score = calculate_complexity_score(row)
    # 2 pedestrians + 3 passengers = 5 lives.
    # 'sides_conflict' contains 'sides', so +1.0
    # Total = 6.0
    assert score == 6.0

def test_derive_complexity_independence_from_response_time(sample_data):
    """Verify that response_time is not used in the calculation."""
    # Modify response_time to see if it affects the score
    original_score = calculate_complexity_score(sample_data.iloc[0])
    
    sample_data.loc[0, 'response_time'] = 999999
    new_score = calculate_complexity_score(sample_data.iloc[0])
    
    assert original_score == new_score, "Response time should not affect complexity score"

def test_derive_complexity_column_creation(sample_data):
    """Test that the derive_complexity function adds the correct column."""
    df_result = derive_complexity(sample_data.copy())
    assert 'dilemma_complexity' in df_result.columns
    assert len(df_result) == len(sample_data)
    
    # Check values
    assert df_result.loc[0, 'dilemma_complexity'] == 3.0
    assert df_result.loc[1, 'dilemma_complexity'] == 6.0 # 5+1 = 6, no sides
    assert df_result.loc[2, 'dilemma_complexity'] == 6.0 # 2+3+1 = 6 (sides)

def test_handle_missing_life_columns():
    """Test behavior when no numeric life columns are found."""
    data = {
        'participant_id': ['p1'],
        'dilemma_type': ['unknown'],
        'response_time': [1000]
    }
    df = pd.DataFrame(data)
    row = df.iloc[0]
    score = calculate_complexity_score(row)
    # Fallback to 2.0
    assert score == 2.0
