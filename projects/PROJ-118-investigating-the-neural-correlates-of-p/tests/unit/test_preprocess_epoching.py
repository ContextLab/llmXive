import pytest
import mne
import numpy as np
from pathlib import Path
import sys
import os

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from preprocess import create_epochs, find_events, load_config_and_validate

@pytest.fixture
def mock_raw_data():
    """Create a mock MNE Raw object for testing."""
    # Create dummy data
    n_channels = 32
    n_times = 10000
    sfreq = 500
    info = mne.create_info(ch_names=[f'EEG {i:03d}' for i in range(n_channels)], 
                           sfreq=sfreq, ch_types='eeg')
    data = np.random.randn(n_channels, n_times)
    raw = mne.io.RawArray(data, info)
    
    # Add a stimulus channel
    stim_data = np.zeros((1, n_times))
    # Insert events at known times
    # 1000 samples = 2s, 2000 = 4s, etc.
    stim_data[0, 1000] = 1  # standard
    stim_data[0, 2000] = 2  # deviant
    stim_data[0, 3000] = 1
    stim_data[0, 4000] = 2
    
    stim_info = mne.create_info(ch_names=['STI 014'], sfreq=sfreq, ch_types='stim')
    stim_raw = mne.io.RawArray(stim_data, stim_info)
    raw.add_channels([stim_raw])
    
    return raw

@pytest.fixture
def mock_config():
    """Return a mock configuration dictionary."""
    return {
        'epoch': {
            'tmin': -0.2,
            'tmax': 0.6,
            'baseline': (-0.2, 0)
        }
    }

def test_create_epochs(mock_raw_data, mock_config):
    """Test that create_epochs produces valid epochs with correct labels."""
    events = find_events(mock_raw_data)
    event_id = {'standard': 1, 'deviant': 2}
    
    epochs = create_epochs(mock_raw_data, events, event_id, mock_config)
    
    # Assertions
    assert len(epochs) == 4, f"Expected 4 epochs, got {len(epochs)}"
    assert 'standard' in epochs.event_id
    assert 'deviant' in epochs.event_id
    assert epochs.times[0] == -0.2
    assert epochs.times[-1] == 0.6
    
    # Check that data is loaded
    assert epochs.get_data().shape == (4, 32, 401)  # 4 epochs, 32 ch, 0.8s * 500Hz

def test_find_events(mock_raw_data):
    """Test that find_events correctly identifies stimulus events."""
    events = find_events(mock_raw_data)
    
    # We inserted 4 events: 1, 2, 1, 2
    assert len(events) == 4
    assert events[0, 2] == 1
    assert events[1, 2] == 2
    assert events[2, 2] == 1
    assert events[3, 2] == 2

def test_epoch_creation_with_missing_channels(mock_raw_data, mock_config):
    """Test epoching when some channels are missing."""
    # Remove a channel
    raw = mock_raw_data.copy()
    raw.drop_channels(['EEG 000'])
    
    events = find_events(raw)
    event_id = {'standard': 1, 'deviant': 2}
    
    epochs = create_epochs(raw, events, event_id, mock_config)
    
    assert len(epochs) == 4
    assert len(epochs.ch_names) == 31
