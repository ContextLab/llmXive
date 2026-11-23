import os
import json
import tempfile
from pathlib import Path
import pytest

import mne
import numpy as np

from code.data.preprocess import preprocess_dataset, apply_bandpass_filter, run_ica_artifact_removal, apply_re_reference
from code.config import get_config

@pytest.fixture
def sample_raw_data():
    """Create a sample MNE Raw object for testing."""
    # Create dummy data: 10 channels, 10 seconds, 1000 Hz
    n_channels = 10
    n_times = 10000
    sfreq = 1000.0
    
    info = mne.create_info(n_channels, sfreq, ch_types='eeg')
    data = np.random.randn(n_channels, n_times)
    
    raw = mne.io.RawArray(data, info)
    return raw

@pytest.fixture
def temp_dirs():
    """Create temporary directories for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

def test_apply_bandpass_filter(sample_raw_data):
    """Test that bandpass filter is applied correctly."""
    config = {'filter_lowcut': 1.0, 'filter_highcut': 40.0}
    filtered = apply_bandpass_filter(sample_raw_data, config)
    
    assert filtered is not None
    assert filtered.info['sfreq'] == sample_raw_data.info['sfreq']
    # Check that filtering changed the data (simple check)
    assert not np.allclose(filtered._data, sample_raw_data._data)

def test_run_ica_artifact_removal(sample_raw_data):
    """Test ICA artifact removal."""
    config = {'ica_n_components': 0.99}
    ica_processed = run_ica_artifact_removal(sample_raw_data, config)
    
    assert ica_processed is not None
    assert ica_processed.info['sfreq'] == sample_raw_data.info['sfreq']

def test_apply_re_reference(sample_raw_data):
    """Test re-referencing."""
    config = {}
    referenced = apply_re_reference(sample_raw_data, config)
    
    assert referenced is not None
    assert referenced.info['sfreq'] == sample_raw_data.info['sfreq']

def test_preprocess_dataset_saves_output(sample_raw_data, temp_dirs):
    """Test that preprocess_dataset saves the cleaned data file."""
    input_path = temp_dirs / 'input_raw.fif'
    output_path = temp_dirs / 'cleaned_data.fif'
    log_path = temp_dirs / 'rejection_log.json'
    
    # Save sample data to input path
    sample_raw_data.save(input_path, overwrite=True)
    
    config = {
        'filter_lowcut': 1.0,
        'filter_highcut': 40.0,
        'ica_n_components': 0.99,
        'sampling_rate_threshold': 500,
        'min_oddball_trials': 100,
        'min_standard_trials': 300
    }
    
    # Run preprocessing
    raw_out, stats = preprocess_dataset(input_path, output_path, config, log_path)
    
    # Verify output file exists
    assert output_path.exists(), "Cleaned data file was not saved"
    
    # Verify log file exists
    assert log_path.exists(), "Rejection log was not saved"
    
    # Verify content of log
    with open(log_path, 'r') as f:
        log_data = json.load(f)
    assert 'processing_steps' in log_data
    assert len(log_data['processing_steps']) > 0

def test_preprocess_dataset_integration(sample_raw_data, temp_dirs):
    """Integration test for full pipeline."""
    input_path = temp_dirs / 'input_raw.fif'
    output_path = temp_dirs / 'cleaned_data.fif'
    log_path = temp_dirs / 'rejection_log.json'
    
    sample_raw_data.save(input_path, overwrite=True)
    
    config = {
        'filter_lowcut': 1.0,
        'filter_highcut': 40.0,
        'ica_n_components': 0.99,
        'sampling_rate_threshold': 500,
        'min_oddball_trials': 100,
        'min_standard_trials': 300
    }
    
    raw_out, stats = preprocess_dataset(input_path, output_path, config, log_path)
    
    # Verify the output can be loaded
    loaded_raw = mne.io.read_raw_fif(output_path, preload=True)
    assert loaded_raw is not None
    assert len(loaded_raw.ch_names) == len(sample_raw_data.ch_names)