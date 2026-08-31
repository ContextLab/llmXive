import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import json
import tempfile
import os

# Mock the config module for testing
class MockConfig:
    @staticmethod
    def get_data_dir():
        return Path(tempfile.gettempdir()) / "test_data"
    
    @staticmethod
    def get_processed_dir():
        return Path(tempfile.gettempdir()) / "test_processed"
    
    @staticmethod
    def set_seed(seed):
        np.random.seed(seed)

# Mock the modules
import sys
from unittest.mock import MagicMock

sys.modules['config'] = MagicMock()
sys.modules['config'].get_data_dir = MockConfig.get_data_dir
sys.modules['config'].get_processed_dir = MockConfig.get_processed_dir
sys.modules['config'].set_seed = MockConfig.set_seed

sys.modules['utils'] = MagicMock()
sys.modules['utils'].load_dataset_chunked = MagicMock()

from preprocess import compute_markov_surprisal, enforce_sampling_limit, filter_datasets

def test_compute_markov_surprisal():
    """Test Markov surprisal computation."""
    data = {
        'stimulus_sequence': ['A', 'B', 'A', 'B', 'A', 'C', 'B'],
        'duration_estimate': [1.0, 1.2, 0.9, 1.1, 1.0, 1.3, 1.1],
        'participant_id': [1, 1, 1, 1, 2, 2, 2]
    }
    df = pd.DataFrame(data)
    
    result_df, markov_state = compute_markov_surprisal(df)
    
    assert 'surprisal' in result_df.columns
    assert len(result_df) == len(df)
    assert 'transition_matrix' in markov_state
    assert 'alphabet' in markov_state
    assert 'order' in markov_state
    assert markov_state['order'] == 1
    assert len(markov_state['alphabet']) > 0

def test_enforce_sampling_limit():
    """Test sampling limit enforcement."""
    data = {
        'stimulus_sequence': list(range(10000)),
        'duration_estimate': [1.0] * 10000,
        'participant_id': [1] * 10000
    }
    df = pd.DataFrame(data)
    
    sampled_df, was_sampled = enforce_sampling_limit(df, max_trials=5000)
    
    assert was_sampled is True
    assert len(sampled_df) == 5000

def test_filter_datasets():
    """Test dataset filtering."""
    data = {
        'stimulus_sequence': ['A', 'B', 'A', 'B'],
        'duration_estimate': [1.0, 1.2, 0.9, 1.1],
        'participant_id': [1, 1, 2, 2],
        'extra_col': ['x', 'y', 'z', 'w']
    }
    df = pd.DataFrame(data)
    
    filtered_df = filter_datasets(df)
    
    assert 'stimulus_sequence' in filtered_df.columns
    assert 'duration_estimate' in filtered_df.columns
    assert 'participant_id' in filtered_df.columns
    assert len(filtered_df) == 4

def test_filter_datasets_missing_columns():
    """Test filtering with missing columns."""
    data = {
        'stimulus_sequence': ['A', 'B', 'A', 'B'],
        'duration_estimate': [1.0, 1.2, 0.9, 1.1],
    }
    df = pd.DataFrame(data)
    
    with pytest.raises(ValueError):
        filter_datasets(df)