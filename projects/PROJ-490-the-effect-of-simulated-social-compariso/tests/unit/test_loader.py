import os
import tempfile
import yaml
from pathlib import Path
import pandas as pd
import pytest

from code.data.loader import load_data_to_raw, write_artifact_hashes_to_state, calculate_file_hash

@pytest.fixture
def sample_dataframe():
    return pd.DataFrame({
        'avatar_condition': [0, 1, 0, 1],
        'pre_self_esteem': [25.0, 30.0, 22.0, 28.0],
        'post_self_esteem': [24.0, 32.0, 21.0, 30.0],
        'comparison_tendency': [3.0, 4.0, 2.0, 4.5]
    })

@pytest.fixture
def temp_dirs():
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        raw_dir = tmp_path / "data" / "raw"
        state_dir = tmp_path / "state" / "projects"
        raw_dir.mkdir(parents=True)
        state_dir.mkdir(parents=True)
        yield tmp_path, raw_dir, state_dir

def test_load_data_to_raw_writes_csv_and_returns_hash(sample_dataframe, temp_dirs):
    tmp_path, raw_dir, _ = temp_dirs
    output_file = raw_dir / "test_data.csv"
    
    info = load_data_to_raw("synthetic", sample_dataframe, output_file)
    
    assert output_file.exists()
    assert info['source_type'] == "synthetic"
    assert info['rows'] == 4
    assert 'hash' in info
    assert len(info['hash']) == 64  # SHA-256 hex length

def test_write_artifact_hashes_to_state_creates_yaml(temp_dirs, sample_dataframe):
    tmp_path, raw_dir, state_dir = temp_dirs
    output_file = raw_dir / "state_test.csv"
    
    # First save data
    info = load_data_to_raw("real", sample_dataframe, output_file)
    state_file = state_dir / "test_project.yaml"
    
    # Then write state
    write_artifact_hashes_to_state(state_file, info)
    
    assert state_file.exists()
    
    with open(state_file, 'r') as f:
        content = yaml.safe_load(f)
    
    assert 'artifact_hashes' in content
    assert 'state_test.csv' in content['artifact_hashes']
    assert content['artifact_hashes']['state_test.csv']['hash'] == info['hash']

def test_calculate_file_hash_consistency(temp_dirs, sample_dataframe):
    tmp_path, raw_dir, _ = temp_dirs
    output_file = raw_dir / "hash_test.csv"
    load_data_to_raw("synthetic", sample_dataframe, output_file)
    
    hash1 = calculate_file_hash(output_file)
    hash2 = calculate_file_hash(output_file)
    
    assert hash1 == hash2