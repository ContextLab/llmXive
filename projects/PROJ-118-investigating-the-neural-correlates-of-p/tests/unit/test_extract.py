"""
Unit tests for code/extract.py (T022).
"""
import pytest
import numpy as np
import mne
from pathlib import Path
import tempfile
import json

# Mock the data_utils import to avoid dependency on full pipeline setup during unit tests
from unittest.mock import patch, MagicMock

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'code'))

from extract import (
    load_epochs,
    compute_average_erps,
    extract_erp_metrics,
    get_subject_epochs_paths
)

@pytest.fixture
def mock_config():
    return {
        'paths': {
            'data_raw': 'data/raw',
            'data_processed': 'data/processed'
        },
        'params': {
            'montage': 'standard_32',
            'filter': [1, 30]
        }
    }

@pytest.fixture
def sample_epochs(tmp_path):
    """Create a dummy MNE epochs file for testing."""
    # Create dummy data
    n_channels = 5
    n_times = 100
    sfreq = 100
    info = mne.create_info(ch_names=[f'EEG {i:03d}' for i in range(n_channels)], 
                           sfreq=sfreq, ch_types='eeg')
    data = np.random.randn(n_channels, n_times)
    events = np.array([[0, 0, 1], [100, 0, 2]]) # 2 events
    event_id = {'standard': 1, 'deviant': 2}
    
    epochs = mne.EpochsArray(data[np.newaxis, ...], info, events=events, event_id=event_id, tmin=0)
    
    # Save to temp file
    fpath = tmp_path / "test_epo.fif"
    epochs.save(fpath, overwrite=True)
    return fpath, epochs

def test_load_epochs(sample_epochs):
    fpath, _ = sample_epochs
    loaded = load_epochs(fpath)
    assert isinstance(loaded, mne.Epochs)
    assert len(loaded) == 2

def test_load_epochs_file_not_found():
    with pytest.raises(FileNotFoundError):
        load_epochs(Path("/nonexistent/path.fif"))

def test_compute_average_erps(sample_epochs):
    fpath, _ = sample_epochs
    epochs = load_epochs(fpath)
    erps = compute_average_erps(epochs, ['standard', 'deviant'])
    
    assert 'standard' in erps
    assert 'deviant' in erps
    assert isinstance(erps['standard'], mne.Evoked)
    assert isinstance(erps['deviant'], mne.Evoked)

def test_extract_erp_metrics(sample_epochs):
    fpath, _ = sample_epochs
    epochs = load_epochs(fpath)
    erps = compute_average_erps(epochs, ['standard'])
    
    # Use channel names from the mock data
    ch_names = [f'EEG {i:03d}' for i in range(5)]
    metrics = extract_erp_metrics(erps['standard'], 'standard', ch_names[:2])
    
    assert metrics['condition'] == 'standard'
    assert 'data' in metrics
    assert ch_names[0] in metrics['data']
    assert len(metrics['data'][ch_names[0]]) == 100 # n_times

def test_get_subject_epochs_paths(tmp_path):
    # Create dummy files
    (tmp_path / "sub-01_epo_raw.fif").touch()
    (tmp_path / "sub-02_epo_raw.fif").touch()
    (tmp_path / "other_file.txt").touch()
    
    subject_ids = ["01", "02", "03"]
    paths = get_subject_epochs_paths(tmp_path, subject_ids)
    
    assert "01" in paths
    assert "02" in paths
    assert "03" not in paths # File doesn't exist
    assert paths["01"].name == "sub-01_epo_raw.fif"

def test_extract_erp_metrics_missing_electrode(sample_epochs):
    fpath, _ = sample_epochs
    epochs = load_epochs(fpath)
    erps = compute_average_erps(epochs, ['standard'])
    
    # Try to extract with a non-existent electrode
    metrics = extract_erp_metrics(erps['standard'], 'standard', ['NON_EXISTENT_CH'])
    
    assert 'data' in metrics
    assert len(metrics['data']) == 0 # Should be empty as channel not found

def test_run_extraction_pipeline_structure(mock_config, sample_epochs, tmp_path):
    # Mock the helper functions to return our sample data
    with patch('extract.load_config_and_validate', return_value=mock_config), \
         patch('extract.get_subject_ids', return_value=['01']), \
         patch('extract.get_subject_epochs_paths', return_value={'01': sample_epochs[0]}):
        
        from extract import run_extraction_pipeline
        results = run_extraction_pipeline(output_dir=tmp_path)
        
        assert '01' in results
        assert 'standard' in results['01']
        assert 'deviant' in results['01']
        assert 'times' in results['01']['standard']
        assert 'data' in results['01']['standard']

def test_save_intermediate_erps(mock_config, sample_epochs, tmp_path):
    with patch('extract.load_config_and_validate', return_value=mock_config), \
         patch('extract.get_subject_ids', return_value=['01']), \
         patch('extract.get_subject_epochs_paths', return_value={'01': sample_epochs[0]}):
        
        from extract import run_extraction_pipeline, save_intermediate_erps
        results = run_extraction_pipeline(output_dir=tmp_path)
        output_file = save_intermediate_erps(results, tmp_path)
        
        assert output_file.exists()
        assert output_file.name == "erp_intermediate.json"
        
        # Verify JSON content
        with open(output_file, 'r') as f:
            data = json.load(f)
        
        assert '01' in data
        assert 'standard' in data['01']
        assert isinstance(data['01']['standard']['times'], list)