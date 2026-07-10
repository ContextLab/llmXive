"""
Unit tests for data validation logic (T017).
"""
import pytest
from pathlib import Path
from unittest.mock import Mock, patch
import mne
import numpy as np

from code.data.download import (
    DownloadValidationError, 
    validate_auditory_dataset, 
    validate_visual_dataset,
    ERR_SAMPLING_RATE_LOW,
    ERR_ODDBALL_TRIALS_LOW,
    ERR_STANDARD_TRIALS_LOW
)

class MockRaw:
    """Mock MNE Raw object for testing."""
    def __init__(self, sfreq=1000, events=None, event_ids=None):
        self.info = {'sfreq': sfreq}
        self._events = events
        self._event_ids = event_ids or {}
    
    def set_montage(self, *args, **kwargs):
        pass

def create_mock_events(n_standard=400, n_oddball=150):
    """Helper to create mock events array and IDs."""
    # Create a simple events array: [time, 0, type]
    # Type 1 = Standard, Type 2 = Oddball
    n_total = n_standard + n_oddball
    times = np.arange(n_total) * 0.5 # 0.5s spacing
    types = np.array([1] * n_standard + [2] * n_oddball)
    events = np.column_stack([times, np.zeros(n_total, dtype=int), types])
    event_ids = {'Standard': 1, 'Oddball': 2}
    return events, event_ids

@patch('code.data.download.mne')
def test_valid_auditory_dataset(mock_mne):
    """Test successful validation of a valid auditory dataset."""
    # Setup mock
    mock_raw = MockRaw(sfreq=1000)
    events, event_ids = create_mock_events(n_standard=400, n_oddball=150)
    
    # Mock mne.io.read_raw_fif to return our mock raw
    mock_mne.io.read_raw_fif.return_value = mock_raw
    mock_mne.events_from_annotations.return_value = (events, event_ids)
    
    # Mock Path.exists
    with patch('pathlib.Path.exists', return_value=True):
        # Mock _load_raw_data_from_path to return our mock raw
        with patch('code.data.download._load_raw_data_from_path', return_value=mock_raw):
            # We need to patch the internal helper that loads data
            # But since we are testing the validation logic, we can mock the raw loading directly
            pass

    # Re-run logic with direct mock injection for the internal function
    with patch('code.data.download._load_raw_data_from_path', return_value=mock_raw):
        with patch('mne.events_from_annotations', return_value=(events, event_ids)):
            result = validate_auditory_dataset(Path("/fake/path"))
            
    assert result['valid'] is True
    assert result['n_standard'] == 400
    assert result['n_oddball'] == 150
    assert result['sfreq'] == 1000

@patch('code.data.download._load_raw_data_from_path')
@patch('mne.events_from_annotations')
def test_sampling_rate_failure(mock_events, mock_load):
    """Test validation failure when sampling rate is too low."""
    mock_raw = MockRaw(sfreq=250) # Below 500 Hz
    events, event_ids = create_mock_events()
    
    mock_load.return_value = mock_raw
    mock_events.return_value = (events, event_ids)
    
    with pytest.raises(DownloadValidationError) as exc_info:
        validate_auditory_dataset(Path("/fake/path"))
    
    assert exc_info.value.error_code == ERR_SAMPLING_RATE_LOW
    assert "500 Hz" in str(exc_info.value)

@patch('code.data.download._load_raw_data_from_path')
@patch('mne.events_from_annotations')
def test_oddball_trials_failure(mock_events, mock_load):
    """Test validation failure when oddball trials are too low."""
    mock_raw = MockRaw(sfreq=1000)
    # Create events with only 50 oddballs
    events, event_ids = create_mock_events(n_standard=400, n_oddball=50)
    
    mock_load.return_value = mock_raw
    mock_events.return_value = (events, event_ids)
    
    with pytest.raises(DownloadValidationError) as exc_info:
        validate_auditory_dataset(Path("/fake/path"))
    
    assert exc_info.value.error_code == ERR_ODDBALL_TRIALS_LOW
    assert "100" in str(exc_info.value)

@patch('code.data.download._load_raw_data_from_path')
@patch('mne.events_from_annotations')
def test_standard_trials_failure(mock_events, mock_load):
    """Test validation failure when standard trials are too low."""
    mock_raw = MockRaw(sfreq=1000)
    # Create events with only 200 standards
    events, event_ids = create_mock_events(n_standard=200, n_oddball=150)
    
    mock_load.return_value = mock_raw
    mock_events.return_value = (events, event_ids)
    
    with pytest.raises(DownloadValidationError) as exc_info:
        validate_auditory_dataset(Path("/fake/path"))
    
    assert exc_info.value.error_code == ERR_STANDARD_TRIALS_LOW
    assert "300" in str(exc_info.value)

@patch('code.data.download._load_raw_data_from_path')
@patch('mne.events_from_annotations')
def test_no_events_failure(mock_events, mock_load):
    """Test validation failure when no events are found."""
    mock_raw = MockRaw(sfreq=1000)
    mock_load.return_value = mock_raw
    mock_events.return_value = (np.array([]).reshape(0, 3), {})
    
    with pytest.raises(DownloadValidationError) as exc_info:
        validate_auditory_dataset(Path("/fake/path"))
    
    assert "No events found" in str(exc_info.value)
