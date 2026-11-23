"""
Unit tests for Task T014: Segment Length Validation.

This test verifies that segments shorter than 120 seconds are excluded
and logged with reason "segment_too_short" in data/processed/exclusion_log.csv.
"""
import os
import csv
import tempfile
import shutil
from pathlib import Path
import pytest
import numpy as np
import mne

# Add the code directory to the path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from preprocess import validate_segment_length, save_cleaned_data
from utils.logging import get_logger, EXCLUSION_LOG_PATH, save_exclusion_log_csv


@pytest.fixture
def clean_log():
    """Fixture to ensure a clean log state before each test."""
    # Clear the global logger
    from utils.logging import _GLOBAL_LOGGER
    # Reset the global logger
    import utils.logging
    utils.logging._GLOBAL_LOGGER = None
    
    # Remove existing exclusion log if present
    if os.path.exists(EXCLUSION_LOG_PATH):
        os.remove(EXCLUSION_LOG_PATH)
    
    yield
    
    # Cleanup after test
    if os.path.exists(EXCLUSION_LOG_PATH):
        os.remove(EXCLUSION_LOG_PATH)
    
    # Reset logger again
    import utils.logging
    utils.logging._GLOBAL_LOGGER = None


def create_short_eeg_file(duration_sec: float, sfreq: int = 250, ch_names: list | None = None) -> mne.io.Raw:
    """
    Create a synthetic short EEG file for testing.
    
    Args:
        duration_sec: Duration of the recording in seconds.
        sfreq: Sampling frequency in Hz.
        ch_names: List of channel names.
        
    Returns:
        mne.io.Raw: A Raw object with synthetic data.
    """
    if ch_names is None:
        ch_names = ["EEG 001", "EEG 002", "EEG 003"]
    
    n_channels = len(ch_names)
    n_samples = int(duration_sec * sfreq)
    
    # Create random data
    data = np.random.randn(n_channels, n_samples)
    
    # Create info structure
    info = mne.create_info(ch_names=ch_names, sfreq=sfreq, ch_types="eeg")
    
    # Create Raw object
    raw = mne.io.RawArray(data, info)
    
    return raw


@pytest.mark.usefixtures("clean_log")
def test_validate_segment_length_short_segment(clean_log):
    """
    Test that a segment shorter than 120 seconds is rejected.
    """
    # Create a short EEG file (60 seconds)
    duration = 60.0
    raw = create_short_eeg_file(duration)
    
    # Mock config
    config = {"min_length_sec": 120.0}
    
    # Mock logger
    from utils.logging import get_logger
    logger = get_logger("test_logger")
    
    # Run validation
    rejected_segments = validate_segment_length(raw, config, logger)
    
    # Assertions
    assert len(rejected_segments) == 1, "Expected 1 rejected segment."
    assert rejected_segments[0] == "segment_0", "Expected segment_0 to be rejected."
    
    # Verify exclusion log was written
    assert os.path.exists(EXCLUSION_LOG_PATH), "Exclusion log file should exist."
    
    # Read and verify CSV content
    with open(EXCLUSION_LOG_PATH, "r", newline="") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        
        assert len(rows) == 1, "Expected 1 entry in exclusion log."
        entry = rows[0]
        assert entry["reason"] == "segment_too_short", "Expected reason 'segment_too_short'."
        assert entry["participant_id"] == "segment_0", "Expected participant_id 'segment_0'."


@pytest.mark.usefixtures("clean_log")
def test_validate_segment_length_long_segment(clean_log):
    """
    Test that a segment longer than 120 seconds is accepted.
    """
    # Create a long EEG file (180 seconds)
    duration = 180.0
    raw = create_short_eeg_file(duration)
    
    # Mock config
    config = {"min_length_sec": 120.0}
    
    # Mock logger
    logger = get_logger("test_logger")
    
    # Run validation
    rejected_segments = validate_segment_length(raw, config, logger)
    
    # Assertions
    assert len(rejected_segments) == 0, "Expected 0 rejected segments."
    
    # Verify exclusion log exists but is empty (or has headers only)
    assert os.path.exists(EXCLUSION_LOG_PATH), "Exclusion log file should exist."
    
    with open(EXCLUSION_LOG_PATH, "r", newline="") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        assert len(rows) == 0, "Expected no entries in exclusion log for valid segment."


@pytest.mark.usefixtures("clean_log")
def test_validate_segment_length_exact_threshold(clean_log):
    """
    Test that a segment exactly 120 seconds is accepted.
    """
    # Create an EEG file exactly 120 seconds
    duration = 120.0
    raw = create_short_eeg_file(duration)
    
    # Mock config
    config = {"min_length_sec": 120.0}
    
    # Mock logger
    logger = get_logger("test_logger")
    
    # Run validation
    rejected_segments = validate_segment_length(raw, config, logger)
    
    # Assertions
    assert len(rejected_segments) == 0, "Expected 0 rejected segments for exact threshold."
    
    # Verify exclusion log
    with open(EXCLUSION_LOG_PATH, "r", newline="") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        assert len(rows) == 0, "Expected no entries in exclusion log for exact threshold."


@pytest.mark.usefixtures("clean_log")
def test_validate_segment_length_just_under_threshold(clean_log):
    """
    Test that a segment just under 120 seconds is rejected.
    """
    # Create an EEG file 119.9 seconds
    duration = 119.9
    raw = create_short_eeg_file(duration)
    
    # Mock config
    config = {"min_length_sec": 120.0}
    
    # Mock logger
    logger = get_logger("test_logger")
    
    # Run validation
    rejected_segments = validate_segment_length(raw, config, logger)
    
    # Assertions
    assert len(rejected_segments) == 1, "Expected 1 rejected segment."
    
    # Verify exclusion log
    with open(EXCLUSION_LOG_PATH, "r", newline="") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        assert len(rows) == 1, "Expected 1 entry in exclusion log."
        assert rows[0]["reason"] == "segment_too_short"
