import pytest
import pandas as pd
from pathlib import Path
from unittest.mock import patch, MagicMock
import sys
import os

# Add the code directory to the path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from data_loader import (
    compute_file_hash,
    verify_checksum,
    fetch_and_verify_librispeech,
    stratified_sample,
    save_stratified_subset,
    load_librispeech_subset,
    generate_all_distortion_vectors,
    verify_dataset_coverage_for_scenarios
)
from config import get_config

@pytest.fixture
def mock_config():
    config = get_config()
    config['raw_path'] = '/tmp/mock_raw'
    config['derived_path'] = '/tmp/mock_derived'
    config['random_seed'] = 42
    config['sample_size'] = 10
    return config

@pytest.fixture
def sample_dataframe():
    data = {
        'file_id': ['123-456-789', '123-456-790', '124-456-789', '124-456-790'],
        'text': ['Hello', 'World', 'Test', 'Data'],
        'speaker_id': ['123', '123', '124', '124'],
        'snr_bucket': ['SNR_0', 'SNR_1', 'SNR_0', 'SNR_1']
    }
    return pd.DataFrame(data)

def test_compute_file_hash(tmp_path):
    test_file = tmp_path / "test.txt"
    test_file.write_text("Hello World")
    hash1 = compute_file_hash(test_file)
    hash2 = compute_file_hash(test_file)
    assert hash1 == hash2
    assert len(hash1) == 64  # SHA-256 hex length

def test_stratified_sample(mock_config, sample_dataframe):
    sampled = stratified_sample(sample_dataframe, mock_config)
    # Check that sampling occurred
    assert len(sampled) <= len(sample_dataframe)
    # Check that strata are preserved
    assert 'speaker_id' in sampled.columns
    assert 'snr_bucket' in sampled.columns

def test_save_stratified_subset(mock_config, sample_dataframe, tmp_path):
    mock_config['derived_path'] = str(tmp_path)
    output_path = save_stratified_subset(sample_dataframe, mock_config, "test_subset.parquet")
    assert output_path.exists()
    df_loaded = pd.read_parquet(output_path)
    assert len(df_loaded) == len(sample_dataframe)

def test_generate_all_distortion_vectors(mock_config):
    vectors = generate_all_distortion_vectors(mock_config)
    assert len(vectors) > 0
    assert 'snr' in vectors[0]
    assert 'rt60' in vectors[0]
    assert 'vector_id' in vectors[0]

def test_verify_dataset_coverage_for_scenarios(mock_config, sample_dataframe):
    scenarios = generate_all_distortion_vectors(mock_config)
    # Mock the dataframe to have specific snr_buckets
    sample_dataframe['snr_bucket'] = ['SNR_0'] * len(sample_dataframe)
    coverage = verify_dataset_coverage_for_scenarios(sample_dataframe, scenarios)
    assert 'total_scenarios' in coverage
    assert 'covered_scenarios' in coverage
    assert 'missing_scenarios' in coverage

@patch('data_loader.fetch_and_verify_librispeech')
@patch('data_loader.stratified_sample')
@patch('data_loader.save_stratified_subset')
def test_load_librispeech_subset(mock_save, mock_sample, mock_fetch, mock_config):
    mock_fetch.return_value = pd.DataFrame({'file_id': ['1'], 'text': ['test']})
    mock_sample.return_value = pd.DataFrame({'file_id': ['1'], 'text': ['test']})
    
    result = load_librispeech_subset(mock_config)
    assert isinstance(result, pd.DataFrame)
    assert len(result) > 0
    mock_fetch.assert_called_once()
    mock_sample.assert_called_once()
    mock_save.assert_called_once()