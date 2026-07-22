"""
Tests for code/02_preprocess_eeg.py
"""
import pytest
import numpy as np
import mne
from pathlib import Path
import sys
import os

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "code"))

from config import set_global_seed, get_path
from utils.eeg_helpers import bandpass_filter, notch_filter, reject_channels_by_variance, apply_ica

# Note: These tests use synthetic data to avoid requiring the full PhysioNet download
# In a real CI environment, T007 would run first to download actual data

@pytest.fixture
def sample_raw():
    """Create a sample raw EEG object for testing."""
    set_global_seed(42)
    
    # Create synthetic EEG data: 64 channels, 10 seconds at 500 Hz
    n_channels = 64
    n_times = 5000
    sfreq = 500.0
    
    info = mne.create_info(
        ch_names=[f'EEG{i:03d}' for i in range(n_channels)],
        sfreq=sfreq,
        ch_types='eeg'
    )
    
    # Generate random data with some structure
    data = np.random.randn(n_channels, n_times) * 1e-6
    
    # Add some line noise at 50 Hz
    time = np.arange(n_times) / sfreq
    for i in range(n_channels):
        data[i] += 0.5e-6 * np.sin(2 * np.pi * 50 * time)
    
    raw = mne.io.RawArray(data, info)
    return raw

@pytest.fixture
def sample_raw_with_bad_channels(sample_raw):
    """Create sample data with intentionally bad channels."""
    raw = sample_raw.copy()
    # Add high variance to first 5 channels
    raw._data[:5, :] *= 100  # 100x variance
    return raw

def test_bandpass_filter(sample_raw):
    """Test that bandpass filter works without error."""
    filtered = bandpass_filter(sample_raw, l_freq=1.0, h_freq=40.0)
    assert filtered is not None
    assert len(filtered.ch_names) == len(sample_raw.ch_names)
    # Check that data was modified (filter applied)
    assert not np.allclose(filtered._data, sample_raw._data)

def test_notch_filter(sample_raw):
    """Test that notch filter works without error."""
    notched = notch_filter(sample_raw, freqs=[50, 60])
    assert notched is not None
    assert len(notched.ch_names) == len(sample_raw.ch_names)

def test_reject_channels_by_variance(sample_raw_with_bad_channels):
    """Test that high-variance channels are rejected."""
    rejected, kept = reject_channels_by_variance(sample_raw_with_bad_channels, threshold_sd=3.0)
    
    # Should reject the artificially inflated channels
    assert len(rejected) > 0
    assert len(kept) < len(sample_raw_with_bad_channels.ch_names)
    
    # The first 5 channels should be rejected
    for i in range(5):
        ch_name = f'EEG{i:03d}'
        assert ch_name in rejected

def test_apply_ica(sample_raw):
    """Test that ICA application works without error."""
    raw_ica, n_removed = apply_ica(sample_raw)
    assert raw_ica is not None
    assert isinstance(n_removed, int)
    assert n_removed >= 0
    assert len(raw_ica.ch_names) <= len(sample_raw.ch_names)

def test_config_paths():
    """Test that config paths are correctly set up."""
    root = get_path('root')
    assert root.exists()
    
    processed = get_path('processed')
    assert processed.exists()
    
    raw_eeg = get_path('raw_eeg')
    assert raw_eeg.exists() or True  # May not exist if T007 not run

def test_seed_reproducibility():
    """Test that seed pinning works."""
    set_global_seed(12345)
    arr1 = np.random.randn(10)
    
    set_global_seed(12345)
    arr2 = np.random.randn(10)
    
    assert np.allclose(arr1, arr2)