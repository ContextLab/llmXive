import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile

from preprocess import (
    load_dataset,
    is_sequential_stimuli,
    has_predictability_manipulation,
    enforce_sampling_limit,
    compute_markov_surprisal
)

@pytest.fixture
def sample_df():
    """Create a sample DataFrame for testing."""
    return pd.DataFrame({
        'duration_estimate': [1.0, 2.0, 3.0, 4.0, 5.0],
        'stimulus_sequence': ['A', 'B', 'A', 'C', 'B'],
        'participant_id': ['P1', 'P1', 'P2', 'P2', 'P1'],
        'condition': ['high', 'low', 'high', 'low', 'high']
    })

@pytest.fixture
def temp_csv(sample_df):
    """Create a temporary CSV file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        csv_path = Path(tmpdir) / "test.csv"
        sample_df.to_csv(csv_path, index=False)
        yield csv_path

def test_load_dataset(temp_csv):
    """Test loading dataset from CSV."""
    df = load_dataset(temp_csv)
    assert len(df) == 5
    assert 'stimulus_sequence' in df.columns

def test_is_sequential_stimuli_true(sample_df):
    """Test sequential stimuli detection (true case)."""
    result = is_sequential_stimuli(sample_df)
    assert result is True

def test_is_sequential_stimuli_false():
    """Test sequential stimuli detection (false case)."""
    df = pd.DataFrame({
        'stimulus_sequence': ['A', 'A', 'A', 'A']
    })
    result = is_sequential_stimuli(df)
    assert result is False

def test_has_predictability_manipulation_true(sample_df):
    """Test predictability manipulation detection (true case)."""
    result = has_predictability_manipulation(sample_df)
    assert result is True

def test_has_predictability_manipulation_false():
    """Test predictability manipulation detection (false case)."""
    df = pd.DataFrame({
        'stimulus_sequence': ['A', 'B', 'C'],
        'other_col': [1, 2, 3]
    })
    result = has_predictability_manipulation(df)
    assert result is False

def test_enforce_sampling_limit_no_change(sample_df):
    """Test sampling limit when data is small."""
    result = enforce_sampling_limit(sample_df, max_trials=100)
    assert len(result) == 5

def test_enforce_sampling_limit_reduction():
    """Test sampling limit when data is large."""
    df = pd.DataFrame({
        'stimulus_sequence': ['A'] * 10000
    })
    result = enforce_sampling_limit(df, max_trials=5000)
    assert len(result) == 5000

def test_compute_markov_surprisal(sample_df):
    """Test Markov surprisal computation."""
    result_df, markov_state = compute_markov_surprisal(sample_df)
    
    assert 'surprisal' in result_df.columns
    assert len(result_df) == len(sample_df)
    assert markov_state['order'] == 1
    assert 'transition_matrix' in markov_state
    assert 'alphabet' in markov_state
    assert len(markov_state['alphabet']) > 0