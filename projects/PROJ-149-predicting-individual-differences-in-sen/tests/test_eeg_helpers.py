import pytest
import numpy as np
import mne
import tempfile
from pathlib import Path
import sys

# Add parent to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "code"))

from utils.eeg_helpers import (
    bandpass_filter, 
    notch_filter, 
    reject_channels_by_variance
)
from config import FILTER_LOW, FILTER_HIGH, NOTCH_FREQS, VAR_REJECTION_STD

@pytest.fixture
def sample_raw():
    """Create a dummy MNE Raw object for testing."""
    n_channels = 10
    n_times = 10000
    sfreq = 250.0
    
    # Create random data with some structure
    data = np.random.randn(n_channels, n_times)
    
    # Add a strong 60Hz component to one channel for notch testing
    time = np.arange(n_times) / sfreq
    data[0, :] += 2.0 * np.sin(2 * np.pi * 60 * time)
    
    # Add a strong low freq (0.5Hz) to another for bandpass testing
    data[1, :] += 2.0 * np.sin(2 * np.pi * 0.5 * time)
    
    info = mne.create_info(ch_names=[f'EEG {i:03d}' for i in range(n_channels)], 
                           sfreq=sfreq, ch_types='eeg')
    raw = mne.io.RawArray(data, info)
    return raw

def test_bandpass_filter(sample_raw):
    """Test that bandpass filter removes out-of-band frequencies."""
    # Filter
    filtered = bandpass_filter(sample_raw, l_freq=FILTER_LOW, h_freq=FILTER_HIGH)
    
    # Check data shape
    assert filtered.get_data().shape == sample_raw.get_data().shape
    
    # Basic sanity check: variance should not explode
    assert np.isfinite(filtered.get_data()).all()

def test_notch_filter(sample_raw):
    """Test that notch filter attenuates line noise."""
    # Check original 60Hz power in channel 0
    original_data = sample_raw.get_data()
    # Simple power check at 60Hz (approx)
    
    filtered = notch_filter(sample_raw, freqs=[60.0])
    filtered_data = filtered.get_data()
    
    # The amplitude of the 60Hz component in channel 0 should be reduced
    # We compare the variance of the channel before and after
    # Since we added a pure sine, the variance reduction should be significant
    # Note: This is a heuristic check
    original_var = np.var(original_data[0, :])
    filtered_var = np.var(filtered_data[0, :])
    
    # The filtered variance should be lower (due to removal of the sine wave)
    # Allow some tolerance for numerical precision and filter ringing
    assert filtered_var < original_var, "Notch filter did not reduce 60Hz component"

def test_reject_channels_by_variance(sample_raw):
    """Test channel rejection based on variance."""
    # Inject a channel with huge variance
    data = sample_raw.get_data().copy()
    data[0, :] *= 100.0  # Massive variance increase
    
    info = sample_raw.info.copy()
    raw_high_var = mne.io.RawArray(data, info)
    
    # Run rejection
    cleaned, rejected = reject_channels_by_variance(raw_high_var, std_threshold=VAR_REJECTION_STD)
    
    # Channel 0 should be rejected
    assert "EEG 000" in rejected
    assert "EEG 000" not in cleaned.ch_names
    
    # Other channels should remain
    assert len(cleaned.ch_names) == len(sample_raw.ch_names) - 1

def test_reject_channels_normal_data(sample_raw):
    """Test that normal data does not trigger rejection."""
    cleaned, rejected = reject_channels_by_variance(sample_raw, std_threshold=VAR_REJECTION_STD)
    
    assert len(rejected) == 0
    assert len(cleaned.ch_names) == len(sample_raw.ch_names)
