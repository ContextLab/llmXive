"""
Unit tests for the derive_dilemma_choice module.
Verifies that the dilemma_choice is derived correctly and independently of response_time.
"""

import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys

# Ensure the code directory is in the path
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from derive_dilemma_choice import derive_choice

def test_derive_choice_save_many():
    """Test that choosing the side with more lives results in 'save_many'."""
    data = {
        'participant_id': [1, 2],
        'dilemma_id': [101, 102],
        'lives_pedestrians': [5, 1],
        'lives_passengers': [1, 5],
        'choice': ['pedestrians', 'passengers']
    }
    df = pd.DataFrame(data)
    result = derive_choice(df)

    assert result.shape[0] == 2
    assert result['dilemma_choice'].iloc[0] == 'save_many'  # 5 > 1, chose pedestrians
    assert result['dilemma_choice'].iloc[1] == 'save_many'  # 5 > 1, chose passengers

def test_derive_choice_save_few():
    """Test that choosing the side with fewer lives results in 'save_few'."""
    data = {
        'participant_id': [1, 2],
        'dilemma_id': [101, 102],
        'lives_pedestrians': [1, 5],
        'lives_passengers': [5, 1],
        'choice': ['pedestrians', 'passengers']
    }
    df = pd.DataFrame(data)
    result = derive_choice(df)

    assert result.shape[0] == 2
    assert result['dilemma_choice'].iloc[0] == 'save_few'   # 1 < 5, chose pedestrians
    assert result['dilemma_choice'].iloc[1] == 'save_few'   # 1 < 5, chose passengers

def test_derive_choice_no_action():
    """Test that 'none' choice results in 'no_action'."""
    data = {
        'participant_id': [1],
        'dilemma_id': [101],
        'lives_pedestrians': [5],
        'lives_passengers': [1],
        'choice': ['none']
    }
    df = pd.DataFrame(data)
    result = derive_choice(df)

    assert result['dilemma_choice'].iloc[0] == 'no_action'

def test_derive_choice_independence_from_response_time():
    """Ensure response_time is NOT used in the derivation."""
    data = {
        'participant_id': [1],
        'dilemma_id': [101],
        'lives_pedestrians': [5],
        'lives_passengers': [1],
        'choice': ['pedestrians'],
        'response_time': [1000] # High response time
    }
    df = pd.DataFrame(data)
    result = derive_choice(df)

    # The result should not contain response_time
    assert 'response_time' not in result.columns

    # The choice should be 'save_many' regardless of the response time
    assert result['dilemma_choice'].iloc[0] == 'save_many'

    # Modify response time and ensure result is identical
    df['response_time'] = [9000]
    result2 = derive_choice(df)
    assert result['dilemma_choice'].iloc[0] == result2['dilemma_choice'].iloc[0]

def test_derive_choice_empty_df():
    """Test handling of empty DataFrame."""
    df = pd.DataFrame(columns=['participant_id', 'dilemma_id', 'lives_pedestrians', 'lives_passengers', 'choice'])
    result = derive_choice(df)
    assert result.empty
    assert 'dilemma_choice' in result.columns

def test_derive_choice_unknown_columns():
    """Test behavior when expected columns are missing."""
    data = {
        'participant_id': [1],
        'dilemma_id': [101],
        'random_col': [123]
    }
    df = pd.DataFrame(data)
    result = derive_choice(df)
    # Should fallback to 'unknown'
    assert result['dilemma_choice'].iloc[0] == 'unknown'