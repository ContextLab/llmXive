"""
Unit tests for preprocessing functions.
Tests for Pipeline A and Pipeline B preprocessing steps.
"""
import numpy as np
import pytest
import mne
from pathlib import Path
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from preprocessing import (
    apply_bandpass, 
    apply_bandpass_alt, 
    apply_notch, 
    apply_notch_alt, 
    apply_car, 
    apply_mastoid_reference, 
    reject_ica_components,
    verify_no_nans,
    process_subject_pipeline_a,
    process_subject_pipeline_b
)
from exceptions import DataIntegrityError

@pytest.fixture
def synthetic_eeg_data():
    """Generate synthetic EEG data for testing."""
    sfreq = 256.0
    n_channels = 32
    n_times = 10000
    
    # Create time vector
    t = np.arange(n_times) / sfreq
    
    # Generate synthetic EEG signal with alpha peak at 10 Hz
    signal = np.zeros((n_channels, n_times))
    for i in range(n_channels):
        # Base signal: 10 Hz alpha + noise
        signal[i] = np.sin(2 * np.pi * 10 * t) + 0.1 * np.random.randn(n_times)
    
    # Create MNE info
    ch_names = [f'EEG{i:03d}' for i in range(n_channels)]
    info = mne.create_info(ch_names=ch_names, sfreq=sfreq, ch_types='eeg')
    
    # Create Raw object
    raw = mne.io.RawArray(signal, info)
    return raw

@pytest.fixture
def synthetic_eog_data():
    """Generate synthetic data with EOG artifacts for ICA testing."""
    sfreq = 256.0
    n_channels = 32
    n_times = 10000
    
    t = np.arange(n_times) / sfreq
    signal = np.zeros((n_channels, n_times))
    
    # Add EOG-like artifact to first few channels
    eog_artifact = 2.0 * np.sin(2 * np.pi * 2 * t)  # 2 Hz blink artifact
    for i in range(4):
        signal[i] = eog_artifact + 0.1 * np.random.randn(n_times)
    
    # Rest of channels: normal EEG
    for i in range(4, n_channels):
        signal[i] = np.sin(2 * np.pi * 10 * t) + 0.1 * np.random.randn(n_times)
    
    ch_names = [f'EEG{i:03d}' for i in range(n_channels)]
    info = mne.create_info(ch_names=ch_names, sfreq=sfreq, ch_types='eeg')
    raw = mne.io.RawArray(signal, info)
    return raw

def test_apply_bandpass():
    """Test bandpass filter application."""
    sfreq = 256.0
    n_channels = 4
    n_times = 1000
    
    t = np.arange(n_times) / sfreq
    # Signal with 10 Hz and 60 Hz components
    signal = np.sin(2 * np.pi * 10 * t) + 0.5 * np.sin(2 * np.pi * 60 * t)
    signal = signal.reshape(1, -1)
    
    # Apply bandpass 1-45 Hz
    filtered = apply_bandpass(signal, sfreq, low=1.0, high=45.0)
    
    # Check dimensions
    assert filtered.shape == signal.shape
    
    # Check that 10 Hz component is preserved (roughly)
    # and 60 Hz is attenuated
    fft_filtered = np.fft.fft(filtered[0])
    freqs = np.fft.fftfreq(n_times, 1/sfreq)
    
    # Find power at 10 Hz and 60 Hz
    idx_10hz = np.argmin(np.abs(freqs - 10))
    idx_60hz = np.argmin(np.abs(freqs - 60))
    
    power_10hz = np.abs(fft_filtered[idx_10hz])
    power_60hz = np.abs(fft_filtered[idx_60hz])
    
    # 10 Hz should have higher power than 60 Hz after filtering
    assert power_10hz > power_60hz * 2  # At least 2x difference

def test_apply_bandpass_alt():
    """Test alternative bandpass filter (Pipeline B)."""
    sfreq = 256.0
    n_channels = 4
    n_times = 1000
    
    t = np.arange(n_times) / sfreq
    signal = np.sin(2 * np.pi * 10 * t) + 0.5 * np.sin(2 * np.pi * 60 * t)
    signal = signal.reshape(1, -1)
    
    # Apply alternative bandpass 0.5-40 Hz
    filtered = apply_bandpass_alt(signal, sfreq, low=0.5, high=40.0)
    
    # Check dimensions
    assert filtered.shape == signal.shape
    
    # Check that 10 Hz component is preserved
    fft_filtered = np.fft.fft(filtered[0])
    freqs = np.fft.fftfreq(n_times, 1/sfreq)
    
    idx_10hz = np.argmin(np.abs(freqs - 10))
    power_10hz = np.abs(fft_filtered[idx_10hz])
    
    # Should have significant power at 10 Hz
    assert power_10hz > 0.1

def test_apply_notch():
    """Test notch filter application."""
    sfreq = 256.0
    n_channels = 4
    n_times = 1000
    
    t = np.arange(n_times) / sfreq
    # Signal with 50 Hz line noise
    signal = np.sin(2 * np.pi * 10 * t) + 0.8 * np.sin(2 * np.pi * 50 * t)
    signal = signal.reshape(1, -1)
    
    # Apply notch filter at 50 Hz
    filtered = apply_notch(signal, sfreq, frequency=50.0)
    
    # Check dimensions
    assert filtered.shape == signal.shape
    
    # Check that 50 Hz component is attenuated
    fft_filtered = np.fft.fft(filtered[0])
    freqs = np.fft.fftfreq(n_times, 1/sfreq)
    
    idx_50hz = np.argmin(np.abs(freqs - 50))
    power_50hz = np.abs(fft_filtered[idx_50hz])
    
    # 50 Hz power should be significantly reduced
    assert power_50hz < 0.5  # Arbitrary threshold for attenuation

def test_apply_notch_alt():
    """Test alternative notch filter."""
    sfreq = 256.0
    n_channels = 4
    n_times = 1000
    
    t = np.arange(n_times) / sfreq
    signal = np.sin(2 * np.pi * 10 * t) + 0.8 * np.sin(2 * np.pi * 50 * t)
    signal = signal.reshape(1, -1)
    
    filtered = apply_notch_alt(signal, sfreq, frequency=50.0)
    
    assert filtered.shape == signal.shape

def test_apply_car():
    """Test Common Average Reference."""
    n_channels = 4
    n_times = 100
    
    # Create signal where all channels have same offset
    signal = np.ones((n_channels, n_times)) * 5.0
    signal += np.random.randn(n_channels, n_times) * 0.1
    
    # Apply CAR
    car_signal = apply_car(signal)
    
    # After CAR, mean across channels should be ~0 at each time point
    channel_means = np.mean(car_signal, axis=0)
    assert np.allclose(channel_means, 0, atol=1e-10)

def test_apply_mastoid_reference():
    """Test mastoid reference application."""
    n_channels = 4
    n_times = 100
    
    # Create signal with mastoid-like channels (last 2)
    signal = np.random.randn(n_channels, n_times)
    # Add common signal to mastoid channels
    common_signal = np.sin(2 * np.pi * 10 * np.arange(n_times) / 256.0)
    signal[-2:, :] += common_signal
    
    # Create info with mastoid channel names
    ch_names = ['EEG000', 'EEG001', 'M1', 'M2']
    info = mne.create_info(ch_names=ch_names, sfreq=256.0, ch_types='eeg')
    
    # Apply mastoid reference
    mastoid_signal = apply_mastoid_reference(signal, info=info, mastoid_ch_names=['M1', 'M2'])
    
    # Check dimensions
    assert mastoid_signal.shape == signal.shape
    
    # The mastoid channels should have reduced common signal
    # (though this is a simplified test)

def test_reject_ica_components_no_eog():
    """Test ICA rejection when no EOG components are found."""
    sfreq = 256.0
    n_channels = 32
    n_times = 5000  # Shorter for faster test
    
    t = np.arange(n_times) / sfreq
    signal = np.zeros((n_channels, n_times))
    
    # Generate clean EEG without EOG artifacts
    for i in range(n_channels):
        signal[i] = np.sin(2 * np.pi * 10 * t) + 0.1 * np.random.randn(n_times)
    
    ch_names = [f'EEG{i:03d}' for i in range(n_channels)]
    info = mne.create_info(ch_names=ch_names, sfreq=sfreq, ch_types='eeg')
    raw = mne.io.RawArray(signal, info)
    
    # Apply ICA rejection
    cleaned_raw, metadata = reject_ica_components(raw, correlation_threshold=0.8)
    
    # Check that no EOG components were rejected
    assert metadata['n_eog_components'] == 0
    assert metadata['n_rejected_components'] == 0
    assert 'None Detected' in str(metadata.get('eog_components', [])) or len(metadata['eog_components']) == 0

def test_reject_ica_components_with_eog():
    """Test ICA rejection with EOG artifacts present."""
    sfreq = 256.0
    n_channels = 32
    n_times = 5000
    
    t = np.arange(n_times) / sfreq
    signal = np.zeros((n_channels, n_times))
    
    # Add strong EOG artifact to first channel
    eog_artifact = 5.0 * np.sin(2 * np.pi * 2 * t)  # 2 Hz blink
    signal[0] = eog_artifact + 0.1 * np.random.randn(n_times)
    
    # Rest of channels: clean EEG
    for i in range(1, n_channels):
        signal[i] = np.sin(2 * np.pi * 10 * t) + 0.1 * np.random.randn(n_times)
    
    ch_names = [f'EEG{i:03d}' for i in range(n_channels)]
    info = mne.create_info(ch_names=ch_names, sfreq=sfreq, ch_types='eeg')
    raw = mne.io.RawArray(signal, info)
    
    # Apply ICA rejection
    cleaned_raw, metadata = reject_ica_components(raw, correlation_threshold=0.5)
    
    # Check that EOG components were detected
    assert metadata['n_eog_components'] > 0
    assert len(metadata['eog_components']) > 0

def test_verify_no_nans():
    """Test NaN verification."""
    # Clean data
    clean_data = np.random.randn(10, 100)
    assert verify_no_nans(clean_data, "test_data") is True
    
    # Data with NaN
    nan_data = clean_data.copy()
    nan_data[0, 0] = np.nan
    
    with pytest.raises(DataIntegrityError):
        verify_no_nans(nan_data, "test_data_with_nan")

def test_process_subject_pipeline_a():
    """Test complete Pipeline A processing."""
    sfreq = 256.0
    n_channels = 16
    n_times = 2000
    
    t = np.arange(n_times) / sfreq
    signal = np.zeros((n_channels, n_times))
    for i in range(n_channels):
        signal[i] = np.sin(2 * np.pi * 10 * t) + 0.1 * np.random.randn(n_times)
    
    ch_names = [f'EEG{i:03d}' for i in range(n_channels)]
    info = mne.create_info(ch_names=ch_names, sfreq=sfreq, ch_types='eeg')
    raw = mne.io.RawArray(signal, info)
    
    # Process with Pipeline A
    processed_raw, metadata = process_subject_pipeline_a(raw)
    
    # Check metadata
    assert metadata['pipeline'] == 'A'
    assert len(metadata['steps']) == 5  # bandpass, notch, car, ica, nan_verify
    
    # Check no NaNs in output
    data = processed_raw.get_data()
    assert not np.any(np.isnan(data))

def test_process_subject_pipeline_b():
    """Test complete Pipeline B processing."""
    sfreq = 256.0
    n_channels = 16
    n_times = 2000
    
    t = np.arange(n_times) / sfreq
    signal = np.zeros((n_channels, n_times))
    for i in range(n_channels):
        signal[i] = np.sin(2 * np.pi * 10 * t) + 0.1 * np.random.randn(n_times)
    
    ch_names = [f'EEG{i:03d}' for i in range(n_channels)]
    info = mne.create_info(ch_names=ch_names, sfreq=sfreq, ch_types='eeg')
    raw = mne.io.RawArray(signal, info)
    
    # Process with Pipeline B
    processed_raw, metadata = process_subject_pipeline_b(raw)
    
    # Check metadata
    assert metadata['pipeline'] == 'B'
    assert len(metadata['steps']) == 4  # bandpass_alt, notch_alt, mastoid, nan_verify
    
    # Check no NaNs in output
    data = processed_raw.get_data()
    assert not np.any(np.isnan(data))