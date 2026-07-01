"""
Unit tests for preprocessing logic using mock data.

This module tests the core preprocessing functions (subsampling, filtering,
epoching, ICA cleaning) without requiring the full dataset download.
It generates synthetic EEG data in memory to validate the pipeline logic.
"""
import os
import tempfile
import numpy as np
import mne
import pytest
from pathlib import Path

# Import the functions to test from the sibling module
from code.preprocess import (
    load_config,
    get_channel_montage,
    subsample_channels,
    apply_filter_and_reference,
    epoch_data,
    run_ica_and_clean,
    save_epochs
)

# Constants for mock data generation
SFREQ = 500  # Hz
N_CHANNELS = 64
N_SECONDS = 2.0
N_EVENTS = 100
SAMPLES = int(SFREQ * N_SECONDS)

def create_mock_raw_data():
    """
    Creates a mock RawArray object with 64 channels for testing.
    Returns a tuple of (RawArray, events array).
    """
    # Create random EEG data (Volts)
    data = np.random.randn(N_CHANNELS, SAMPLES) * 1e-6
    
    # Create standard 64-channel montage names (subset of standard)
    # We use a generic set that includes the target 32 channels
    ch_names = [
        'Fp1', 'Fp2', 'F7', 'F8', 'F3', 'F4', 'Fz', 'FC3', 'FC4', 'FCz',
        'C3', 'C4', 'Cz', 'CP3', 'CP4', 'CPz', 'P3', 'P4', 'Pz', 'PO7',
        'PO8', 'O1', 'O2', 'Oz', 'AF7', 'AF8', 'FT7', 'FT8', 'TP7', 'TP8',
        'PO3', 'PO4', 'F9', 'F10', 'FT9', 'FT10', 'T7', 'T8', 'T9', 'T10',
        'TP9', 'TP10', 'P9', 'P10', 'O9', 'O10', 'Iz', 'AF3', 'AF4', 'AFz',
        'FC5', 'FC1', 'FC2', 'FC6', 'C5', 'C1', 'C2', 'C6', 'CP5', 'CP1',
        'CP2', 'CP6', 'P5', 'P1', 'P2', 'P6', 'O1', 'O2'
    ]
    # Ensure we have unique names if there are duplicates in the list above
    ch_names = list(dict.fromkeys(ch_names))[:N_CHANNELS]
    
    # Create info structure
    info = mne.create_info(ch_names=ch_names, sfreq=SFREQ, ch_types='eeg')
    
    # Add montage
    montage = mne.make_standard_montage('standard_1005')
    info.set_montage(montage, match_case=False, match_alias=True)
    
    raw = mne.io.RawArray(data, info)
    
    # Create events array: [sample, 0, event_id]
    # Standard = 1, Deviant = 2
    event_ids = [1] * (N_EVENTS // 2) + [2] * (N_EVENTS // 2)
    np.random.shuffle(event_ids)
    event_samples = np.linspace(0, SAMPLES - int(SFREQ * 0.5), N_EVENTS, dtype=int)
    events = np.column_stack([event_samples, np.zeros(N_EVENTS, dtype=int), event_ids])
    
    return raw, events

def test_load_config():
    """Test that config loads correctly from the project config file."""
    config = load_config()
    assert config is not None
    assert 'filter' in config
    assert 'ica' in config
    assert 'epoch' in config

def test_get_channel_montage():
    """Test that the correct 32-channel montage is returned."""
    montage = get_channel_montage()
    expected_channels = [
        'Fp1', 'Fp2', 'F7', 'F8', 'F3', 'F4', 'Fz', 'FC3', 'FC4', 'FCz',
        'C3', 'C4', 'Cz', 'CP3', 'CP4', 'CPz', 'P3', 'P4', 'Pz', 'PO7',
        'PO8', 'O1', 'O2', 'Oz', 'AF7', 'AF8', 'FT7', 'FT8', 'TP7', 'TP8',
        'PO3', 'PO4'
    ]
    assert montage == expected_channels
    assert len(montage) == 32

def test_subsample_channels():
    """Test that subsampling reduces channels to the target montage."""
    raw, _ = create_mock_raw_data()
    original_n_channels = len(raw.ch_names)
    
    montage = get_channel_montage()
    raw_subsampled = subsample_channels(raw, montage)
    
    assert len(raw_subsampled.ch_names) == 32
    assert set(raw_subsampled.ch_names).issubset(set(raw.ch_names))
    # Verify all expected channels are present
    for ch in montage:
        assert ch in raw_subsampled.ch_names

def test_apply_filter_and_reference():
    """Test filtering and re-referencing."""
    raw, _ = create_mock_data()
    raw = subsample_channels(raw, get_channel_montage())
    
    # Get config params
    config = load_config()
    low_freq = config['filter']['low']
    high_freq = config['filter']['high']
    
    raw_filtered = apply_filter_and_reference(raw, low_freq, high_freq)
    
    # Verify filtering was applied (check filter attributes)
    assert raw_filtered._filter_status is not None or hasattr(raw_filtered, 'filter_status')
    
    # Verify re-referencing (average reference)
    # The data shape should remain the same, but reference should change
    assert len(raw_filtered.ch_names) == 32

def test_epoch_data():
    """Test epoching creates correct number of epochs."""
    raw, events = create_mock_data()
    raw = subsample_channels(raw, get_channel_montage())
    
    config = load_config()
    tmin = config['epoch']['tmin']
    tmax = config['epoch']['tmax']
    
    epochs = epoch_data(raw, events, tmin, tmax)
    
    # Check epochs object
    assert epochs is not None
    assert len(epochs.event_id) > 0
    # Should have 'standard' (1) and 'deviant' (2) conditions
    assert '1' in epochs.event_id or 'standard' in [str(k) for k in epochs.event_id]
    assert '2' in epochs.event_id or 'deviant' in [str(k) for k in epochs.event_id]

def test_run_ica_and_clean():
    """Test ICA identification and removal of artifacts."""
    raw, events = create_mock_data()
    raw = subsample_channels(raw, get_channel_montage())
    raw = apply_filter_and_reference(raw, 1, 30)
    epochs = epoch_data(raw, events, -0.2, 0.6)
    
    config = load_config()
    threshold = config['ica']['threshold']
    n_components = config['ica']['n_components']
    
    # Run ICA
    ica, n_removed = run_ica_and_clean(epochs, threshold, n_components)
    
    # ICA object should be created
    assert ica is not None
    # n_removed should be an integer >= 0
    assert isinstance(n_removed, int)
    assert n_removed >= 0

def test_save_epochs(tmp_path):
    """Test saving epochs to disk."""
    raw, events = create_mock_data()
    raw = subsample_channels(raw, get_channel_montage())
    raw = apply_filter_and_reference(raw, 1, 30)
    epochs = epoch_data(raw, events, -0.2, 0.6)
    
    output_path = tmp_path / "test_epochs.fif"
    save_epochs(epochs, str(output_path))
    
    # Verify file exists
    assert output_path.exists()
    assert output_path.suffix == '.fif'
    
    # Verify file is loadable
    loaded_epochs = mne.read_epochs(str(output_path))
    assert loaded_epochs is not None
    assert len(loaded_epochs) == len(epochs)

def test_full_preprocessing_pipeline(tmp_path):
    """Test the full preprocessing pipeline end-to-end with mock data."""
    # Create mock data
    raw, events = create_mock_data()
    
    # Get config
    config = load_config()
    montage = get_channel_montage()
    low_freq = config['filter']['low']
    high_freq = config['filter']['high']
    tmin = config['epoch']['tmin']
    tmax = config['epoch']['tmax']
    ica_threshold = config['ica']['threshold']
    ica_n_components = config['ica']['n_components']
    
    # Step 1: Subsample
    raw_sub = subsample_channels(raw, montage)
    assert len(raw_sub.ch_names) == 32
    
    # Step 2: Filter and Reference
    raw_filt = apply_filter_and_reference(raw_sub, low_freq, high_freq)
    
    # Step 3: Epoch
    epochs = epoch_data(raw_filt, events, tmin, tmax)
    assert epochs is not None
    
    # Step 4: ICA Clean
    ica, n_removed = run_ica_and_clean(epochs, ica_threshold, ica_n_components)
    assert ica is not None
    assert isinstance(n_removed, int)
    
    # Step 5: Save
    output_file = tmp_path / "processed_epochs.fif"
    save_epochs(epochs, str(output_file))
    assert output_file.exists()

# Helper to ensure consistent mock data creation
def create_mock_data():
    """Wrapper to ensure consistent mock data creation."""
    return create_mock_raw_data()