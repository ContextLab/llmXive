"""
Unit tests for T017b: save_markov_artifacts module.
"""
import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pandas as pd
import pytest

# We need to mock the config to return a temporary directory
@pytest.fixture
def mock_config(tmp_path):
    processed_dir = tmp_path / "processed"
    processed_dir.mkdir()
    
    # Create a mock standardized.csv
    mock_df = pd.DataFrame({
        'stimulus_sequence': ['A', 'B', 'A', 'B', 'C', 'A', 'B', 'C'],
        'surprisal': [0.5, 0.6, 0.5, 0.6, 0.7, 0.5, 0.6, 0.7],
        'participant_id': [1, 1, 1, 1, 1, 1, 1, 1],
        'duration_estimate': [100, 110, 105, 115, 120, 100, 110, 120]
    })
    mock_csv_path = processed_dir / "standardized.csv"
    mock_df.to_csv(mock_csv_path, index=False)

    with patch('code.save_markov_artifacts.get_data_dir') as mock_get_dir:
        mock_get_dir.return_value = tmp_path
        yield tmp_path

def test_load_standardized_data(mock_config):
    from code.save_markov_artifacts import load_standardized_data
    
    df = load_standardized_data()
    assert len(df) == 8
    assert 'stimulus_sequence' in df.columns
    assert 'participant_id' in df.columns

def test_compute_transition_matrices(mock_config):
    from code.save_markov_artifacts import load_standardized_data, compute_transition_matrices
    
    df = load_standardized_data()
    result = compute_transition_matrices(df)
    
    assert 'sequence_alphabet' in result
    assert 'global_transition_matrix' in result
    assert 'participant_transition_matrices' in result
    assert 'A' in result['sequence_alphabet']
    assert 'B' in result['sequence_alphabet']
    
    # Check that probabilities sum to 1 (approximately)
    global_matrix = result['global_transition_matrix']
    for start, transitions in global_matrix.items():
        total = sum(transitions.values())
        # Allow for small floating point errors
        assert abs(total - 1.0) < 1e-6 or total == 0.0, f"Probabilities for {start} do not sum to 1: {total}"

def test_save_markov_artifacts(mock_config):
    from code.save_markov_artifacts import load_standardized_data, compute_transition_matrices, save_markov_artifacts
    
    df = load_standardized_data()
    transition_data = compute_transition_matrices(df)
    
    saved_files = save_markov_artifacts(transition_data, version="test_v1")
    
    assert len(saved_files) == 3
    for file_path in saved_files:
        assert os.path.exists(file_path)
        with open(file_path, 'r') as f:
            data = json.load(f)
            assert isinstance(data, dict)

def test_run_t017b(mock_config):
    from code.save_markov_artifacts import run_t017b
    
    result = run_t017b(seed=42)
    
    assert result['status'] == 'success'
    assert 'files_saved' in result
    assert len(result['files_saved']) == 3

def test_missing_standardized_data(tmp_path):
    from code.save_markov_artifacts import load_standardized_data
    
    with patch('code.save_markov_artifacts.get_data_dir') as mock_get_dir:
        mock_get_dir.return_value = tmp_path
        # No standardized.csv created
        with pytest.raises(FileNotFoundError):
            load_standardized_data()

def test_missing_columns(tmp_path):
    from code.save_markov_artifacts import load_standardized_data
    
    processed_dir = tmp_path / "processed"
    processed_dir.mkdir()
    
    # Create a CSV missing a required column
    mock_df = pd.DataFrame({
        'stimulus_sequence': ['A', 'B'],
        'surprisal': [0.5, 0.6]
        # Missing participant_id
    })
    mock_df.to_csv(processed_dir / "standardized.csv", index=False)

    with patch('code.save_markov_artifacts.get_data_dir') as mock_get_dir:
        mock_get_dir.return_value = tmp_path
        with pytest.raises(ValueError):
            load_standardized_data()
