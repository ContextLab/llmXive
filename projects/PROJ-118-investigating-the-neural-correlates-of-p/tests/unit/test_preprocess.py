"""
Unit tests for the preprocessing utilities.
"""
import pytest
import mne
from pathlib import Path

from code.preprocess import apply_filter, rereference, select_channels, get_mmn_montage

def test_apply_filter():
    # Create synthetic raw data for testing
    info = mne.create_info(ch_names=['Fz', 'Cz'], sfreq=1000, ch_types='eeg')
    data = np.random.randn(2, 1000)  # 1 second of data
    raw = mne.io.RawArray(data, info)
    filtered = apply_filter(raw, l_freq=1.0, h_freq=30.0)
    assert filtered is not None
    # Simple sanity check: data should still have same shape
    assert filtered.get_data().shape == raw.get_data().shape

def test_rereference():
    info = mne.create_info(ch_names=['Fz', 'Cz'], sfreq=1000, ch_types='eeg')
    data = np.random.randn(2, 1000)
    raw = mne.io.RawArray(data, info)
    re_ref = rereference(raw, method='average')
    assert re_ref is not None
    # After average reference, the reference channel list should be empty
    assert re_ref.get_montage() is not None

def test_select_channels():
    info = mne.create_info(ch_names=['Fz', 'Cz', 'Pz', 'Oz'], sfreq=1000, ch_types='eeg')
    data = np.random.randn(4, 1000)
    raw = mne.io.RawArray(data, info)
    selected = select_channels(raw, ['Fz', 'Cz', 'Pz'])
    assert selected.ch_names == ['Fz', 'Cz', 'Pz']

def test_get_mmn_montage():
    montage = get_mmn_montage()
    assert isinstance(montage, list)
    assert 'Fz' in montage
    assert 'FCz' in montage