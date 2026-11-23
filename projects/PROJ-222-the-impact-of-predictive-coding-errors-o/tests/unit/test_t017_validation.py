"""
Unit tests for T017: Standardized Output Generation and Validation.
"""
import pytest
import pandas as pd
import numpy as np
import json
import os
from pathlib import Path
import tempfile
import shutil

# Mock the config to use temporary directories during tests
from unittest.mock import patch, MagicMock

@pytest.fixture
def temp_data_dir():
    """Create a temporary directory structure for testing."""
    temp_root = tempfile.mkdtemp()
    data_dir = Path(temp_root) / "data"
    processed_dir = data_dir / "processed"
    processed_dir.mkdir(parents=True)
    yield data_dir
    shutil.rmtree(temp_root)

@pytest.fixture
def mock_preprocessed_data(temp_data_dir):
    """Create a mock preprocessed_data.csv that satisfies T016 output."""
    processed_dir = temp_data_dir / "processed"
    # Create a dataset with >100 rows
    n_rows = 150
    data = {
        'participant_id': [f'P{i}' for i in range(n_rows)],
        'stimulus_sequence': [np.random.randint(0, 10) for _ in range(n_rows)],
        'duration_estimate': np.random.uniform(0.5, 5.0, n_rows),
        'surprisal': np.random.uniform(0.0, 3.0, n_rows) # Simulating Markov derived values
    }
    df = pd.DataFrame(data)
    file_path = processed_dir / "preprocessed_data.csv"
    df.to_csv(file_path, index=False)
    return file_path

def test_t017_schema_validation(mock_preprocessed_data, temp_data_dir):
    """Test that T017 validates schema correctly."""
    from generate_standardized_output import validate_schema, run_t017
    
    df = pd.read_csv(mock_preprocessed_data)
    
    # Test valid schema
    required = ['participant_id', 'stimulus_sequence', 'duration_estimate', 'surprisal']
    is_valid, missing = validate_schema(df, required)
    assert is_valid
    assert len(missing) == 0
    
    # Test missing column
    is_valid, missing = validate_schema(df, required + ['missing_col'])
    assert not is_valid
    assert 'missing_col' in missing

def test_t017_markov_verification(mock_preprocessed_data, temp_data_dir):
    """Test that T017 verifies Markov derivation."""
    from generate_standardized_output import verify_markov_derivation
    
    df = pd.read_csv(mock_preprocessed_data)
    assert verify_markov_derivation(df) is True
    
    # Test missing surprisal column
    df_no_surprisal = df.drop(columns=['surprisal'])
    assert verify_markov_derivation(df_no_surprisal) is False
    
    # Test non-numeric surprisal
    df['surprisal'] = ['string'] * len(df)
    assert verify_markov_derivation(df) is False

def test_t017_row_count_check(mock_preprocessed_data, temp_data_dir):
    """Test that T017 enforces >= 100 rows."""
    from generate_standardized_output import run_t017
    
    # Mock config to point to temp dir
    with patch('generate_standardized_output.get_data_dir', return_value=temp_data_dir):
        # This should pass because we created 150 rows
        result = run_t017(seed=42)
        assert result['row_count'] >= 100
        assert os.path.exists(temp_data_dir / "processed" / "standardized.csv")

def test_t017_checksum_generation(mock_preprocessed_data, temp_data_dir):
    """Test that T017 generates a valid checksum."""
    from generate_standardized_output import run_t017, compute_sha256
    
    with patch('generate_standardized_output.get_data_dir', return_value=temp_data_dir):
        result = run_t017(seed=42)
        
        output_file = temp_data_dir / "processed" / "standardized.csv"
        expected_checksum = compute_sha256(output_file)
        
        assert result['checksum'] == expected_checksum

def test_t017_fails_on_small_dataset(temp_data_dir):
    """Test that T017 fails if dataset < 100 rows."""
    processed_dir = temp_data_dir / "processed"
    processed_dir.mkdir(parents=True)
    
    # Create small dataset
    data = {
        'participant_id': ['P1', 'P2'],
        'stimulus_sequence': [1, 2],
        'duration_estimate': [1.0, 2.0],
        'surprisal': [0.1, 0.2]
    }
    df = pd.DataFrame(data)
    df.to_csv(processed_dir / "preprocessed_data.csv", index=False)
    
    from generate_standardized_output import run_t017
    
    with patch('generate_standardized_output.get_data_dir', return_value=temp_data_dir):
        with pytest.raises(ValueError, match="less than the required 100"):
            run_t017(seed=42)
