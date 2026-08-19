"""
Unit tests for EEG helper functions.
"""
import pytest
import numpy as np
import mne
from unittest.mock import patch, MagicMock
from code.utils.eeg_helpers import (
    bandpass_filter,
    notch_filter,
    reject_channels_by_variance,
    apply_ica
)

@pytest.fixture
def sample_raw():
    """Create a minimal mock Raw object for testing."""
    info = mne.create_info(ch_names=['EEG 001', 'EEG 002', 'EEG 003'], sfreq=256, ch_types='eeg')
    data = np.random.randn(3, 1000)
    raw = mne.io.RawArray(data, info)
    return raw

def test_bandpass_filter(sample_raw):
    """Test that bandpass_filter returns a Raw object."""
    result = bandpass_filter(sample_raw, l_freq=1.0, h_freq=40.0)
    assert isinstance(result, mne.io.Raw)
    assert result.ch_names == sample_raw.ch_names

def test_notch_filter(sample_raw):
    """Test that notch_filter returns a Raw object."""
    result = notch_filter(sample_raw, freqs=[50.0])
    assert isinstance(result, mne.io.Raw)
    assert result.ch_names == sample_raw.ch_names

def test_reject_channels_by_variance_no_rejection(sample_raw):
    """Test variance rejection when all channels are normal."""
    # Create data with uniform variance
    data = np.random.randn(3, 1000)
    info = mne.create_info(ch_names=['EEG 001', 'EEG 002', 'EEG 003'], sfreq=256, ch_types='eeg')
    raw = mne.io.RawArray(data, info)
    
    rejected, cleaned = reject_channels_by_variance(raw, threshold=3.0)
    assert rejected == []
    assert cleaned.ch_names == raw.ch_names

def test_reject_channels_by_variance_with_rejection(sample_raw):
    """Test variance rejection when one channel is noisy."""
    data = np.random.randn(3, 1000)
    # Make channel 0 very noisy
    data[0, :] = data[0, :] * 100
    info = mne.create_info(ch_names=['EEG 001', 'EEG 002', 'EEG 003'], sfreq=256, ch_types='eeg')
    raw = mne.io.RawArray(data, info)
    
    rejected, cleaned = reject_channels_by_variance(raw, threshold=2.0)
    assert len(rejected) > 0
    assert 'EEG 001' in rejected
    assert 'EEG 001' not in cleaned.ch_names

@patch('mne.preprocessing.ICA')
def test_apply_ica(mock_ica_class, sample_raw):
    """Test ICA application with mocked ICA object."""
    # Setup mock
    mock_ica = MagicMock()
    mock_ica_class.return_value = mock_ica
    mock_ica.find_bads_eog.return_value = ([], [])
    mock_ica.find_bads_ecg.return_value = ([], [])
    
    result_raw, n_removed = apply_ica(sample_raw, verbose=False)
    
    assert isinstance(result_raw, mne.io.Raw)
    assert n_removed == 0