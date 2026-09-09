"""Test for T013: Epoch Rejection implementation."""
import os
import csv
import pytest
from pathlib import Path
import numpy as np
import mne

# Import the functions we are testing
from code.preprocess import reject_artifacts, load_config
from code.utils.logging import EXCLUSION_LOG_PATH


def test_epoch_rejection_logs_to_csv(tmp_path):
    """Test that rejected epochs are logged to exclusion_log.csv with reason 'amplitude_threshold'."""
    # Create a temporary directory for test data
    test_data_dir = tmp_path / "data" / "raw"
    test_data_dir.mkdir(parents=True)
    test_output_dir = tmp_path / "data" / "processed"
    test_output_dir.mkdir(parents=True)

    # Create a synthetic EEG file with high amplitude epochs
    sfreq = 250  # Sampling frequency
    n_channels = 2
    n_times = 250 * 120  # 2 minutes of data (60000 samples)

    # Create data with some epochs exceeding 100uV
    data = np.random.randn(n_channels, n_times) * 50  # Normal data ~50uV

    # Make epoch 5 exceed threshold (150uV)
    epoch_start = 5 * 250 * 2  # 2-second epoch
    epoch_end = epoch_start + 250 * 2
    data[:, epoch_start:epoch_end] = 150  # Exceeds 100uV threshold

    # Create info structure
    info = mne.create_info(ch_names=[f'EEG{i:03d}' for i in range(n_channels)], sfreq=sfreq, ch_types='eeg')
    info['subject_info'] = {'subject_id': 'test_participant_001'}

    # Create raw object
    raw = mne.io.RawArray(data, info)

    # Save to FIF file
    test_file = test_data_dir / "test_eeg.fif"
    raw.save(test_file, overwrite=True)

    # Temporarily override EXCLUSION_LOG_PATH to use tmp_path
    original_path = EXCLUSION_LOG_PATH
    test_log_path = str(tmp_path / "data" / "processed" / "exclusion_log.csv")

    # Reload module to pick up new path (or patch the function)
    import code.utils.logging as logging_module
    logging_module.EXCLUSION_LOG_PATH = test_log_path

    try:
        # Load config
        config = load_config()
        config["artifact_threshold_uV"] = 100.0

        # Run rejection
        raw_clean = reject_artifacts(raw, threshold=100.0, participant_id="test_participant_001")

        # Verify exclusion log was created
        assert os.path.exists(test_log_path), f"Exclusion log not created at {test_log_path}"

        # Read and verify log contents
        with open(test_log_path, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        assert len(rows) > 0, "Exclusion log is empty"

        # Find the epoch rejection entry
        epoch_rejection_found = False
        for row in rows:
            if row.get('reason') == 'amplitude_threshold':
                epoch_rejection_found = True
                assert row.get('participant_id') == 'test_participant_001', "Participant ID mismatch"
                assert row.get('artifact_type') == 'epoch', "Artifact type should be 'epoch'"
                break

        assert epoch_rejection_found, "No 'amplitude_threshold' entry found in exclusion log"

    finally:
        # Restore original path
        logging_module.EXCLUSION_LOG_PATH = original_path


def test_epoch_rejection_removes_high_amplitude_epochs():
    """Test that epochs exceeding threshold are actually removed from data."""
    sfreq = 250
    n_channels = 2
    n_epochs = 10
    epoch_duration = 2  # seconds
    n_times = n_epochs * epoch_duration * sfreq

    # Create data with normal amplitude
    data = np.random.randn(n_channels, n_times) * 50

    # Make epoch 3 exceed threshold
    epoch_start = 3 * epoch_duration * sfreq
    epoch_end = epoch_start + epoch_duration * sfreq
    data[:, epoch_start:epoch_end] = 150  # Exceeds 100uV

    # Create info and raw
    info = mne.create_info(ch_names=[f'EEG{i:03d}' for i in range(n_channels)], sfreq=sfreq, ch_types='eeg')
    raw = mne.io.RawArray(data, info)

    # Apply rejection
    raw_clean = reject_artifacts(raw, threshold=100.0, participant_id="test")

    # Verify the rejected epoch is removed
    # Original had 10 epochs, should now have 9
    original_n_times = raw.n_times
    clean_n_times = raw_clean.n_times

    # The cleaned data should be shorter by one epoch
    assert clean_n_times == original_n_times - (epoch_duration * sfreq), \
        f"Expected {original_n_times - (epoch_duration * sfreq)} samples, got {clean_n_times}"