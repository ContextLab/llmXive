"""
Unit tests for T016: Create Cleaned Dataset
"""
import os
import json
import tempfile
import pandas as pd
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Mock config to avoid needing full project setup for unit tests
@pytest.fixture
def mock_config_paths():
    with patch('code.t016_create_cleaned_dataset.get_path') as mock_get_path:
        with patch('code.t016_create_cleaned_dataset.ensure_dirs') as mock_ensure:
            mock_ensure.return_value = True
            
            # Mock input path
            input_path = Path(tempfile.gettempdir()) / "filtered_adress.csv"
            # Mock output path
            output_path = Path(tempfile.gettempdir()) / "cleaned_adress.csv"
            
            def path_side_effect(key):
                if key == "data/interim/filtered_adress.csv":
                    return input_path
                elif key == "data/interim/cleaned_adress.csv":
                    return output_path
                else:
                    return Path(tempfile.gettempdir()) / key
            
            mock_get_path.side_effect = path_side_effect
            yield input_path, output_path

@pytest.fixture
def sample_interim_data(mock_config_paths):
    input_path, _ = mock_config_paths
    data = {
        'participant_id': ['P001', 'P002', 'P003'],
        'label': ['Control', 'AD', 'MCI'],
        'text': ['This is a test transcript.', 'Another test.', 'Third test.']
    }
    df = pd.DataFrame(data)
    df.to_csv(input_path, index=False)
    return df

def test_load_interim_records(mock_config_paths, sample_interim_data):
    from code.t016_create_cleaned_dataset import load_interim_records
    
    df = load_interim_records()
    assert len(df) == 3
    assert 'participant_id' in df.columns
    assert 'label' in df.columns
    assert 'text' in df.columns

def test_apply_t014_t015_logic(mock_config_paths, sample_interim_data):
    from code.t016_create_cleaned_dataset import apply_t014_t015_logic
    
    df = apply_t014_t015_logic(sample_interim_data)
    assert isinstance(df, pd.DataFrame)
    assert df['label'].dtype == object # or str
    assert df['text'].dtype == object

def test_write_cleaned_dataset(mock_config_paths, sample_interim_data):
    from code.t016_create_cleaned_dataset import write_cleaned_dataset
    
    input_path, output_path = mock_config_paths
    df = apply_t014_t015_logic(sample_interim_data)
    
    write_cleaned_dataset(df, output_path)
    
    assert os.path.exists(output_path)
    result_df = pd.read_csv(output_path)
    assert len(result_df) == 3
    assert result_df['label'].iloc[0] == 'Control'

def test_generate_derivation_log(mock_config_paths, sample_interim_data):
    from code.t016_create_cleaned_dataset import generate_derivation_log
    
    input_path, output_path = mock_config_paths
    df = apply_t014_t015_logic(sample_interim_data)
    
    generate_derivation_log(df, output_path)
    
    log_path = output_path.parent / "cleaned_adress_derivation.json"
    assert os.path.exists(log_path)
    
    with open(log_path, 'r') as f:
        log_data = json.load(f)
    
    assert log_data['task_id'] == 'T016'
    assert log_data['record_count'] == 3
    assert 'Control' in log_data['label_distribution']

def test_missing_columns(mock_config_paths):
    from code.t016_create_cleaned_dataset import apply_t014_t015_logic
    
    bad_df = pd.DataFrame({'id': [1], 'text': ['hi']})
    with pytest.raises(ValueError, match="missing required columns"):
        apply_t014_t015_logic(bad_df)

def test_file_not_found(mock_config_paths):
    from code.t016_create_cleaned_dataset import load_interim_records
    
    input_path, _ = mock_config_paths
    # Remove the file created by fixture
    if os.path.exists(input_path):
        os.remove(input_path)
        
    with pytest.raises(FileNotFoundError):
        load_interim_records()
