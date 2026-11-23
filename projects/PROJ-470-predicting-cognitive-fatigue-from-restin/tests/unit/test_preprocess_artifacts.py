"""
Unit tests for artifact rejection logic in preprocess.py.
"""
import os
import sys
import csv
import numpy as np
import mne
import pytest
from pathlib import Path
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.preprocess import reject_artifacts, load_config
from code.utils.logging import EXCLUSION_LOG_PATH, get_rejection_counts

@pytest.fixture
def clean_logs():
    """Fixture to clean up logs before and after test."""
    if EXCLUSION_LOG_PATH.exists():
        EXCLUSION_LOG_PATH.unlink()
    yield
    # Cleanup after test if needed, though pytest usually handles temp dirs

@pytest.fixture
def mock_raw_signal():
    """Create a mock MNE Raw object."""
    n_channels = 2
    n_times = 256 * 120  # 120 seconds at 256 Hz
    sfreq = 256.0
    
    # Generate noise
    data = np.random.randn(n_channels, n_times)
    info = mne.create_info(ch_names=[f'EEG{i}' for i in range(n_channels)], 
                           sfreq=sfreq, 
                           ch_types='eeg')
    raw = mne.io.RawArray(data, info)
    return raw

def test_amplitude_rejection(mock_raw_signal, clean_logs):
    """Test that signals with amplitude > threshold are rejected."""
    # Modify data to have high amplitude
    mock_raw_signal._data *= 200.0 # Scale to exceed 100uV
    
    config = load_config()
    threshold = config.get('artifact_threshold_uV', 100)
    
    # Should return True (rejected)
    is_rejected = reject_artifacts(mock_raw_signal, threshold, 120, None, "test_participant")
    
    assert is_rejected is True
    
    # Verify log file exists
    assert EXCLUSION_LOG_PATH.exists(), "Exclusion log was not created."
    
    # Verify content
    with open(EXCLUSION_LOG_PATH, 'r') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        assert len(rows) == 1
        assert rows[0]['reason'] == f"amplitude > {threshold}uV"
        assert rows[0]['participant_id'] == "test_participant"

def test_duration_rejection(clean_logs):
    """Test that signals with duration < 120s are rejected."""
    n_channels = 2
    n_times = 256 * 60  # 60 seconds at 256 Hz (less than 120s)
    sfreq = 256.0
    
    data = np.random.randn(n_channels, n_times)
    info = mne.create_info(ch_names=[f'EEG{i}' for i in range(n_channels)], 
                           sfreq=sfreq, 
                           ch_types='eeg')
    raw = mne.io.RawArray(data, info)
    
    config = load_config()
    min_duration = config.get('min_segment_duration_s', 120)
    
    # Should return True (rejected)
    is_rejected = reject_artifacts(raw, 100, min_duration, None, "short_participant")
    
    assert is_rejected is True
    
    # Verify log
    with open(EXCLUSION_LOG_PATH, 'r') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        assert len(rows) == 1
        assert rows[0]['reason'] == f"segment < {min_duration}s"

def test_accept_valid_signal(mock_raw_signal, clean_logs):
    """Test that valid signals are not rejected."""
    # Ensure amplitude is low and duration is sufficient
    # Default mock is 120s. We need to ensure amplitude < 100.
    # Random.randn usually < 4, so safe, but let's be explicit.
    mock_raw_signal._data *= 10.0 
    
    config = load_config()
    threshold = config.get('artifact_threshold_uV', 100)
    min_duration = config.get('min_segment_duration_s', 120)
    
    is_rejected = reject_artifacts(mock_raw_signal, threshold, min_duration, None, "valid_participant")
    
    assert is_rejected is False
    
    # Log should be empty or not contain this rejection
    counts = get_rejection_counts()
    # If log exists, ensure it doesn't have a rejection for this specific reason/participant
    # (Other tests might have run, but we check counts)
    if counts:
        # If there are counts, they shouldn't be from a valid signal
        assert "amplitude > 100uV" not in counts or counts["amplitude > 100uV"] == 0

def test_log_columns(clean_logs, mock_raw_signal):
    """Verify the CSV has the exact required columns."""
    mock_raw_signal._data *= 200.0
    reject_artifacts(mock_raw_signal, 100, 120, None, "col_test")
    
    with open(EXCLUSION_LOG_PATH, 'r') as f:
        reader = csv.DictReader(f)
        assert 'participant_id' in reader.fieldnames
        assert 'reason' in reader.fieldnames
        assert 'timestamp' in reader.fieldnames