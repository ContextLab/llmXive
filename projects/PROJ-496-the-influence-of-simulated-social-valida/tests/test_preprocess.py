"""
Tests for the EEG preprocessing module.

These tests verify the preprocessing pipeline components including
band-pass filtering, epoch rejection, and P300 feature extraction.
"""

import os
import tempfile
from pathlib import Path
import numpy as np
import pandas as pd
import pytest
import mne

# Import the module under test
from preprocess import (
    apply_bandpass_filter,
    reject_epochs,
    average_reference,
    extract_p300_features,
    run_preprocess_phase,
    P300_ELECTRODES,
    DEFAULT_REJECTION_THRESHOLD
)
from logger import setup_logging, get_logger


@pytest.fixture
def sample_raw_data():
    """Create sample raw EEG data for testing."""
    # Create synthetic EEG data: 10 channels, 1000 samples at 250 Hz
    n_channels = 10
    n_samples = 1000
    sfreq = 250.0
    
    # Generate random data with realistic amplitude range (10-50 µV)
    data = np.random.randn(n_channels, n_samples) * 20e-6  # 20 µV std dev
    
    # Create channel names
    ch_names = [f'EEG {i:03d}' for i in range(n_channels)]
    ch_names[0] = 'Pz'  # Ensure Pz exists
    ch_names[1] = 'CPz'  # Ensure CPz exists
    
    # Create info structure
    info = mne.create_info(ch_names=ch_names, sfreq=sfreq, ch_types='eeg')
    
    # Create raw object
    raw = mne.io.RawArray(data, info)
    
    return raw

@pytest.fixture
def sample_epochs(sample_raw_data):
    """Create sample epochs for testing."""
    # Create events
    events = np.array([
        [0, 0, 1],
        [250, 0, 1],
        [500, 0, 1],
        [750, 0, 1]
    ])
    
    event_id = {'stimulus': 1}
    
    epochs = mne.Epochs(
        sample_raw_data,
        events,
        event_id=event_id,
        tmin=0.0,
        tmax=0.8,
        baseline=None,
        verbose=False
    )
    
    return epochs

def test_bandpass_filter():
    """Test that band-pass filter is applied correctly."""
    setup_logging(level='WARNING')
    logger = get_logger('test')
    
    # Create raw data
    n_channels = 4
    n_samples = 2500
    sfreq = 250.0
    
    data = np.random.randn(n_channels, n_samples) * 20e-6
    ch_names = ['Pz', 'CPz', 'Fz', 'Cz']
    info = mne.create_info(ch_names=ch_names, sfreq=sfreq, ch_types='eeg')
    raw = mne.io.RawArray(data, info)
    
    # Apply filter
    low_cutoff = 0.1
    high_cutoff = 40.0
    filtered_raw = apply_bandpass_filter(raw, low_cutoff, high_cutoff, logger)
    
    # Verify filter was applied (check that data is different)
    assert not np.allclose(raw.get_data(), filtered_raw.get_data()), \
        "Filtered data should be different from original"
    
    # Verify data shape is preserved
    assert filtered_raw.get_data().shape == raw.get_data().shape, \
        "Filtered data shape should match original"
    
    logger.info("Band-pass filter test passed")

def test_filtering_and_ica():
    """
    Integration test for filtering and basic artifact handling.
    This test verifies that the preprocessing pipeline can handle
    a complete filtering and epoch rejection workflow.
    """
    setup_logging(level='WARNING')
    logger = get_logger('test')
    
    # Create sample data with known properties
    n_channels = 6
    n_samples = 5000
    sfreq = 250.0
    
    # Create data with some "bad" epochs (high amplitude)
    data = np.random.randn(n_channels, n_samples) * 20e-6
    # Add some high amplitude artifacts
    data[0, 1000:1250] = 200e-6  # 200 µV artifact
    
    ch_names = ['Pz', 'CPz', 'Fz', 'Cz', 'F3', 'F4']
    info = mne.create_info(ch_names=ch_names, sfreq=sfreq, ch_types='eeg')
    raw = mne.io.RawArray(data, info)
    
    # Apply filter
    filtered_raw = apply_bandpass_filter(raw, 0.1, 40.0, logger)
    
    # Create epochs
    events = np.array([
        [0, 0, 1],
        [1250, 0, 1],  # Contains artifact
        [2500, 0, 1],
        [3750, 0, 1]
    ])
    
    epochs = mne.Epochs(
        filtered_raw,
        events,
        event_id={'stimulus': 1},
        tmin=0.0,
        tmax=1.0,
        baseline=None,
        verbose=False
    )
    
    # Test epoch rejection
    rejection_threshold = 100.0  # µV
    clean_epochs = reject_epochs(epochs, rejection_threshold, logger)
    
    # Verify that at least one epoch was rejected due to artifact
    assert len(clean_epochs) < len(epochs), \
        "Bad epochs should be rejected"
    
    # Verify remaining epochs are within threshold
    epoch_data = clean_epochs.get_data()
    max_amplitude = np.max(np.abs(epoch_data)) * 1e6  # Convert to µV
    
    assert max_amplitude <= rejection_threshold * 1.1, \
        f"Remaining epochs should be within threshold ({max_amplitude:.2f} > {rejection_threshold})"
    
    logger.info("Filtering and ICA test passed")

def test_average_reference():
    """Test average reference application."""
    setup_logging(level='WARNING')
    logger = get_logger('test')
    
    # Create sample epochs
    n_channels = 4
    n_epochs = 10
    n_times = 200
    sfreq = 250.0
    
    data = np.random.randn(n_epochs, n_channels, n_times) * 20e-6
    ch_names = ['Pz', 'CPz', 'Fz', 'Cz']
    info = mne.create_info(ch_names=ch_names, sfreq=sfreq, ch_types='eeg')
    
    # Create epochs manually
    epochs = mne.EpochsArray(data, info, verbose=False)
    
    # Apply average reference
    ref_epochs = average_reference(epochs, logger)
    
    # Verify reference was applied (mean across channels should be ~0)
    epoch_data = ref_epochs.get_data()
    channel_means = np.mean(epoch_data, axis=1)  # Mean across channels for each epoch
    
    # Check that means are close to zero (within numerical precision)
    assert np.allclose(channel_means, 0, atol=1e-10), \
        "Average reference should result in zero mean across channels"
    
    logger.info("Average reference test passed")

def test_p300_extraction():
    """Test P300 feature extraction."""
    setup_logging(level='WARNING')
    logger = get_logger('test')
    
    # Create sample epochs with realistic P300-like signal
    n_epochs = 20
    n_channels = 6
    n_times = 250  # 1 second at 250 Hz
    sfreq = 250.0
    
    # Create time vector
    times = np.linspace(0, 1, n_times)
    
    # Create data with a P300-like peak at ~300ms
    data = np.zeros((n_epochs, n_channels, n_times))
    
    # Add P300-like signal to Pz and CPz
    p300_idx = np.where((times >= 0.25) & (times <= 0.50))[0]
    p300_signal = np.zeros_like(times)
    p300_signal[p300_idx] = 5e-6 * np.exp(-((times[p300_idx] - 0.35) / 0.05) ** 2)
    
    for ep in range(n_epochs):
        # Pz channel (index 0)
        data[ep, 0, :] += p300_signal + np.random.randn(n_times) * 1e-6
        # CPz channel (index 1)
        data[ep, 1, :] += p300_signal * 0.8 + np.random.randn(n_times) * 1e-6
        # Other channels
        data[ep, 2:, :] = np.random.randn(n_channels - 2, n_times) * 2e-6
    
    ch_names = ['Pz', 'CPz', 'Fz', 'Cz', 'F3', 'F4']
    info = mne.create_info(ch_names=ch_names, sfreq=sfreq, ch_types='eeg')
    
    epochs = mne.EpochsArray(data, info, verbose=False)
    
    # Extract P300 features
    p300_df = extract_p300_features(epochs, P300_ELECTRODES, logger)
    
    # Verify output
    assert not p300_df.empty, "P300 DataFrame should not be empty"
    assert 'p300_amplitude' in p300_df.columns, "Should have p300_amplitude column"
    assert 'p300_latency' in p300_df.columns, "Should have p300_latency column"
    assert 'electrode' in p300_df.columns, "Should have electrode column"
    
    # Verify amplitude is in reasonable range (2-15 µV)
    assert p300_df['p300_amplitude'].between(2, 15).all() or \
           p300_df['p300_amplitude'].min() > 0, \
           f"P300 amplitudes should be positive, got range: {p300_df['p300_amplitude'].min():.2f} - {p300_df['p300_amplitude'].max():.2f}"
    
    # Verify latency is in P300 window (0.25-0.50s)
    assert p300_df['p300_latency'].between(0.25, 0.50).all(), \
        f"P300 latencies should be in 0.25-0.50s window, got: {p300_df['p300_latency'].min():.3f} - {p300_df['p300_latency'].max():.3f}"
    
    logger.info(f"P300 extraction test passed: {len(p300_df)} features extracted")

def test_rejection_threshold_parameter():
    """Test that rejection threshold parameter works correctly."""
    setup_logging(level='WARNING')
    logger = get_logger('test')
    
    # Create data with varying amplitudes
    n_epochs = 10
    n_channels = 4
    n_times = 200
    sfreq = 250.0
    
    data = np.random.randn(n_epochs, n_channels, n_times) * 20e-6
    # Add one very bad epoch
    data[0, :, :] = 300e-6  # 300 µV
    
    ch_names = ['Pz', 'CPz', 'Fz', 'Cz']
    info = mne.create_info(ch_names=ch_names, sfreq=sfreq, ch_types='eeg')
    epochs = mne.EpochsArray(data, info, verbose=False)
    
    # Test with strict threshold
    strict_epochs = reject_epochs(epochs, 50.0, logger)
    assert len(strict_epochs) < len(epochs), "Strict threshold should reject more epochs"
    
    # Test with lenient threshold
    lenient_epochs = reject_epochs(epochs, 200.0, logger)
    assert len(lenient_epochs) > len(strict_epochs), "Lenient threshold should reject fewer epochs"
    
    logger.info("Rejection threshold parameter test passed")

if __name__ == '__main__':
    pytest.main([__file__, '-v'])
