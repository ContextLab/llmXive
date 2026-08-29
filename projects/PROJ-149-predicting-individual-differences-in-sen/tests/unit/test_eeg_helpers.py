"""
tests/unit/test_eeg_helpers.py
Unit tests for eeg_helpers utilities.
"""
import pytest
import numpy as np
import mne
from code.utils.eeg_helpers import apply_bandpass, apply_notch, reject_channels_by_variance
from code.config import get_filter_params

@pytest.fixture
def dummy_raw():
    """Create a dummy MNE Raw object for testing."""
    info = mne.create_info(ch_names=['EEG 001', 'EEG 002', 'EEG 003', 'EEG 004'], sfreq=250, ch_types='eeg')
    data = np.random.randn(4, 250 * 10) # 10 seconds
    raw = mne.io.RawArray(data, info)
    return raw

def test_apply_bandpass(dummy_raw):
    """Test bandpass filter application."""
    params = get_filter_params()
    filtered = apply_bandpass(dummy_raw, params['l_freq'], params['h_freq'])
    assert filtered is not None
    assert filtered.get_data().shape == dummy_raw.get_data().shape

def test_apply_notch(dummy_raw):
    """Test notch filter application."""
    filtered = apply_notch(dummy_raw, [50.0])
    assert filtered is not None

def test_reject_channels_by_variance(dummy_raw):
    """Test channel rejection based on variance."""
    # Inject high variance in one channel
    data = dummy_raw.get_data()
    data[0, :] *= 100 # High variance
    dummy_raw._data = data
    
    rejected, ratio = reject_channels_by_variance(dummy_raw, threshold_std=3.0)
    assert 'EEG 001' in rejected
    assert ratio > 0.0
