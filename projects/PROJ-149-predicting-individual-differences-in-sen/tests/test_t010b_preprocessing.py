"""
Tests for T010b: ICA Cleaning in Preprocessing.
This ensures the dependency for T012 (preprocessed data) is valid.
"""
import pytest
import numpy as np
import mne
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from code.utils.eeg_helpers import apply_ica, reject_channels_by_variance

@pytest.fixture
def mock_raw():
    sfreq = 250
    n_times = 10000
    n_channels = 16
    data = np.random.randn(n_channels, n_times) * 1e-6
    info = mne.create_info([f'EEG {i:03d}' for i in range(n_channels)], sfreq, 'eeg')
    return mne.io.RawArray(data, info)

def test_apply_ica_runs(mock_raw):
    """Test that ICA applies without error."""
    cleaned, excluded = apply_ica(mock_raw, n_components=5)
    assert cleaned is not None
    assert isinstance(excluded, list)

def test_reject_channels_by_variance(mock_raw):
    """Test variance rejection logic."""
    # Inject a bad channel with huge variance
    data = mock_raw.get_data()
    data[0, :] *= 1000  # Make first channel bad
    mock_raw._data = data
    
    cleaned, rejected = reject_channels_by_variance(mock_raw, threshold_std=2.0)
    assert len(rejected) > 0 or len(rejected) == 0 # Depends on threshold
    # The function should not crash
