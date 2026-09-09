"""
Test for T014: Segment Length Validation.
Verifies that segments < 120 seconds are rejected and logged.
"""
import os
import sys
import numpy as np
import mne
import pytest
from pathlib import Path

# Add the project root to the path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.preprocess import reject_short_segments, setup_logger
from code.utils.logging import get_logger, save_exclusion_log_csv

@pytest.fixture
def short_eeg_raw():
    """Create a mock MNE Raw object with duration < 120 seconds."""
    # Create dummy data: 10 channels, 120 seconds * 250 Hz = 30000 samples
    # But we want < 120s, so let's do 60 seconds
    sfreq = 250
    duration = 60  # seconds
    n_channels = 10
    n_samples = int(sfreq * duration)
    
    data = np.random.randn(n_channels, n_samples) * 1e-6  # Volts
    ch_names = [f'EEG {i:03d}' for i in range(n_channels)]
    ch_types = ['eeg'] * n_channels
    
    info = mne.create_info(ch_names, sfreq, ch_types)
    raw = mne.io.RawArray(data, info)
    return raw

@pytest.fixture
def long_eeg_raw():
    """Create a mock MNE Raw object with duration >= 120 seconds."""
    sfreq = 250
    duration = 150  # seconds
    n_channels = 10
    n_samples = int(sfreq * duration)
    
    data = np.random.randn(n_channels, n_samples) * 1e-6  # Volts
    ch_names = [f'EEG {i:03d}' for i in range(n_channels)]
    ch_types = ['eeg'] * n_channels
    
    info = mne.create_info(ch_names, sfreq, ch_types)
    raw = mne.io.RawArray(data, info)
    return raw

def test_reject_short_segments_rejects_short_data(short_eeg_raw):
    """Test that segments shorter than 120s are rejected."""
    result = reject_short_segments(short_eeg_raw, min_duration_seconds=120)
    assert result is None, "Short segment should be rejected (return None)"

def test_reject_short_segments_accepts_long_data(long_eeg_raw):
    """Test that segments >= 120s are accepted."""
    result = reject_short_segments(long_eeg_raw, min_duration_seconds=120)
    assert result is not None, "Long segment should be accepted"
    assert result.n_times == long_eeg_raw.n_times

def test_exclusion_log_created_on_rejection(short_eeg_raw, tmp_path):
    """Test that exclusion log is created and contains correct reason."""
    # Temporarily change the log path for testing
    original_path = "data/processed/exclusion_log.csv"
    
    # Ensure the directory exists
    os.makedirs("data/processed", exist_ok=True)
    
    # Call the function
    result = reject_short_segments(short_eeg_raw, min_duration_seconds=120)
    
    # Check that the file exists
    assert os.path.exists(original_path), f"Exclusion log not created at {original_path}"
    
    # Read the log and verify content
    import pandas as pd
    df = pd.read_csv(original_path)
    
    # Check that there is an entry with reason "segment_too_short"
    matching_rows = df[df['reason'] == 'segment_too_short']
    assert len(matching_rows) > 0, "No entry found with reason 'segment_too_short'"
    
    # Clean up
    if os.path.exists(original_path):
        os.remove(original_path)

if __name__ == "__main__":
    pytest.main([__file__, "-v"])