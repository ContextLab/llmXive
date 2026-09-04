import pytest
import pandas as pd
import numpy as np
from preprocess import compute_markov_surprisal, enforce_sampling_limit

def test_markov_surprisal_computation():
    """Test Markov surprisal calculation."""
    df = pd.DataFrame({
        'stimulus_sequence': ['a', 'b', 'a', 'c', 'b', 'a'],
        'duration_estimate': [1, 2, 3, 4, 5, 6],
        'participant_id': [1, 1, 1, 1, 1, 1]
    })
    
    result_df, markov_state = compute_markov_surprisal(df)
    
    assert 'surprisal' in result_df.columns
    assert not result_df['surprisal'].isna().all()
    assert markov_state['order'] == 1
    assert 'transition_matrix' in markov_state
    assert 'alphabet' in markov_state

def test_sampling_limit():
    """Test sampling limit enforcement."""
    df = pd.DataFrame({
        'stimulus_sequence': [f's{i}' for i in range(10000)],
        'duration_estimate': range(10000),
        'participant_id': [1] * 10000
    })
    
    sampled = enforce_sampling_limit(df, max_trials=5000)
    assert len(sampled) == 5000

def test_single_stimulus():
    """Test handling of single stimulus."""
    df = pd.DataFrame({
        'stimulus_sequence': ['a'],
        'duration_estimate': [1],
        'participant_id': [1]
    })
    
    result_df, markov_state = compute_markov_surprisal(df)
    assert result_df['surprisal'].iloc[0] == 0.0  # Or handled appropriately