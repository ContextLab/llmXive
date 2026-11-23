"""
Unit tests for segment length validation in preprocess.py
"""
import os
import tempfile
import json
import numpy as np
import mne
import pytest
from pathlib import Path

from preprocess import (
    validate_segment_length,
    log_artifact_rejection,
    save_exclusion_log_csv
)
from utils.logging import get_logger


def create_test_eeg_file(duration_seconds: float, filename: str):
    """Create a test EEG file with specified duration."""
    sfreq = 250  # Sampling frequency
    n_channels = 10
    n_times = int(duration_seconds * sfreq)
    
    # Generate random data
    data = np.random.randn(n_channels, n_times) * 10e-6  # 10 microvolts RMS
    
    # Create info structure
    info = mne.create_info(
        ch_names=[f'EEG {i:03d}' for i in range(n_channels)],
        sfreq=sfreq,
        ch_types='eeg'
    )
    
    # Create raw object
    raw = mne.io.RawArray(data, info)
    
    # Save to file
    raw.save(filename, overwrite=True)
    
    return raw


def test_segment_length_valid():
    """Test that a segment >= 120 seconds is accepted."""
    with tempfile.NamedTemporaryFile(suffix='.fif', delete=False) as f:
        temp_path = f.name
    
    try:
        # Create a 150-second segment
        create_test_eeg_file(150.0, temp_path)
        raw = mne.io.read_raw_fif(temp_path, preload=True)
        
        # Validate
        result = validate_segment_length(raw, min_duration_seconds=120)
        
        assert result is True, "Segment of 150s should be accepted"
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)


def test_segment_length_invalid():
    """Test that a segment < 120 seconds is rejected."""
    with tempfile.NamedTemporaryFile(suffix='.fif', delete=False) as f:
        temp_path = f.name
    
    try:
        # Create a 60-second segment
        create_test_eeg_file(60.0, temp_path)
        raw = mne.io.read_raw_fif(temp_path, preload=True)
        
        # Validate
        result = validate_segment_length(raw, min_duration_seconds=120)
        
        assert result is False, "Segment of 60s should be rejected"
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)


def test_segment_length_boundary():
    """Test that a segment exactly 120 seconds is accepted."""
    with tempfile.NamedTemporaryFile(suffix='.fif', delete=False) as f:
        temp_path = f.name
    
    try:
        # Create a 120-second segment
        create_test_eeg_file(120.0, temp_path)
        raw = mne.io.read_raw_fif(temp_path, preload=True)
        
        # Validate
        result = validate_segment_length(raw, min_duration_seconds=120)
        
        assert result is True, "Segment of exactly 120s should be accepted"
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)


def test_exclusion_log_created():
    """Test that rejected segments are logged to exclusion_log.csv."""
    with tempfile.TemporaryDirectory() as temp_dir:
        log_file = os.path.join(temp_dir, 'exclusion_log.csv')
        
        with tempfile.NamedTemporaryFile(suffix='.fif', delete=False) as f:
            temp_path = f.name
        
        try:
            # Create a short segment
            create_test_eeg_file(60.0, temp_path)
            raw = mne.io.read_raw_fif(temp_path, preload=True)
            raw.info['subject_info'] = {'his_id': 'test_subject_001'}
            
            # Setup logger with custom log file
            logger = get_logger("test_segment_validation")
            
            # Reject the segment
            validate_segment_length(raw, min_duration_seconds=120, logger=logger)
            
            # Manually trigger log save (in real pipeline, this happens automatically)
            save_exclusion_log_csv(log_file)
            
            # Verify log file exists and contains entry
            assert os.path.exists(log_file), "Exclusion log file should be created"
            
            import pandas as pd
            df = pd.read_csv(log_file)
            
            assert len(df) > 0, "Exclusion log should contain at least one entry"
            assert 'reason' in df.columns, "Log should have 'reason' column"
            assert 'segment_too_short' in df['reason'].values, "Log should contain 'segment_too_short' reason"
            assert 'participant_id' in df.columns, "Log should have 'participant_id' column"
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)