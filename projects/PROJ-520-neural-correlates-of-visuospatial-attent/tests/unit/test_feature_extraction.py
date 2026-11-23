"""
Unit tests for feature extraction module.
"""

import os
import json
import tempfile
from pathlib import Path
import numpy as np
import pytest
import mne

from feature_extraction import (
    load_epochs,
    compute_time_frequency,
    baseline_normalize,
    extract_mean_power,
    run_extraction
)
from config import get_config


@pytest.fixture
def sample_epochs():
    """Create a small sample epochs object for testing."""
    # Create dummy data
    n_epochs = 10
    n_channels = 5
    n_times = 256
    sfreq = 128.0  # Hz

    # Create channel names
    ch_names = ['P3', 'Pz', 'P4', 'F3', 'Fz']
    info = mne.create_info(ch_names=ch_names, sfreq=sfreq, ch_types='eeg')

    # Create random data
    data = np.random.randn(n_epochs, n_channels, n_times) * 1e-6  # in Volts

    # Create events array
    events = np.array([
        [0, 0, 1],
        [128, 0, 1],
        [256, 0, 2],
        [384, 0, 1],
        [512, 0, 2],
        [640, 0, 1],
        [768, 0, 2],
        [896, 0, 1],
        [1024, 0, 2],
        [1152, 0, 1],
    ])

    # Create epochs
    epochs = mne.EpochsArray(data, info, events=events, event_id={'cond1': 1, 'cond2': 2}, tmin=-0.5)

    return epochs


@pytest.fixture
def sample_epochs_file(sample_epochs, tmp_path):
    """Save sample epochs to a temporary FIF file."""
    file_path = tmp_path / "test_epochs.fif"
    sample_epochs.save(file_path, overwrite=True)
    return str(file_path)


def test_load_epochs(sample_epochs_file):
    """Test loading epochs from file."""
    epochs = load_epochs(sample_epochs_file)
    assert epochs is not None
    assert len(epochs) == 10
    assert len(epochs.ch_names) == 5


def test_load_epochs_not_found():
    """Test that loading non-existent file raises error."""
    with pytest.raises(FileNotFoundError):
        load_epochs("non_existent_file.fif")


def test_compute_time_frequency(sample_epochs):
    """Test TFR computation."""
    freqs = np.array([8.0, 10.0, 12.0])
    result = compute_time_frequency(sample_epochs, freqs)

    assert 'power' in result
    assert 'times' in result
    assert 'freqs' in result
    assert 'ch_names' in result

    # Check shapes
    n_epochs = len(sample_epochs)
    n_channels = len(sample_epochs.ch_names)
    n_freqs = len(freqs)
    n_times = len(result['times'])

    assert result['power'].shape == (n_epochs, n_channels, n_freqs, n_times)
    assert len(result['freqs']) == n_freqs


def test_baseline_normalize(sample_epochs):
    """Test baseline normalization."""
    freqs = np.array([8.0, 10.0, 12.0])
    tfr_result = compute_time_frequency(sample_epochs, freqs)

    normalized = baseline_normalize(tfr_result, baseline=(-0.5, 0.0))

    assert 'power' in normalized
    assert normalized['power'].shape == tfr_result['power'].shape

    # Check that values are in dB (should be around 0 for baseline period)
    # Note: This is a sanity check, not a strict assertion
    assert np.all(np.isfinite(normalized['power']))


def test_baseline_normalize_no_baseline_points(sample_epochs):
    """Test that baseline normalization fails gracefully when no baseline points exist."""
    freqs = np.array([8.0, 10.0, 12.0])
    tfr_result = compute_time_frequency(sample_epochs, freqs)

    # Use a baseline period outside the data range
    with pytest.raises(ValueError):
        baseline_normalize(tfr_result, baseline=(5.0, 6.0))


def test_extract_mean_power(sample_epochs):
    """Test mean power extraction."""
    freqs = np.linspace(4.0, 30.0, 27)
    tfr_result = compute_time_frequency(sample_epochs, freqs)
    normalized = baseline_normalize(tfr_result)

    # Extract alpha power for parietal electrodes
    alpha_power = extract_mean_power(normalized, (8.0, 12.0), ['P3', 'Pz', 'P4'])

    assert alpha_power.shape == (len(sample_epochs), 3)
    assert np.all(np.isfinite(alpha_power))

    # Extract beta power for frontal electrodes
    beta_power = extract_mean_power(normalized, (13.0, 30.0), ['F3', 'Fz'])

    assert beta_power.shape == (len(sample_epochs), 2)
    assert np.all(np.isfinite(beta_power))


def test_extract_mean_power_missing_electrodes(sample_epochs):
    """Test handling of missing electrodes."""
    freqs = np.array([8.0, 10.0, 12.0])
    tfr_result = compute_time_frequency(sample_epochs, freqs)
    normalized = baseline_normalize(tfr_result)

    # Try to extract from non-existent electrode - should warn and continue
    # with available electrodes
    power = extract_mean_power(normalized, (8.0, 12.0), ['P3', 'NONEXISTENT'])

    # Should only return data for P3
    assert power.shape == (len(sample_epochs), 1)


def test_run_extraction(sample_epochs_file, tmp_path):
    """Test full extraction pipeline."""
    output_dir = str(tmp_path / "output")

    results = run_extraction(sample_epochs_file, output_dir)

    assert 'feature_matrix' in results
    assert 'conditions' in results
    assert results['feature_matrix'].shape[0] == 10

    # Check that files were saved
    assert os.path.exists(os.path.join(output_dir, 'features_matrix.npy'))
    assert os.path.exists(os.path.join(output_dir, 'feature_extraction_metadata.json'))

    # Check metadata content
    with open(os.path.join(output_dir, 'feature_extraction_metadata.json'), 'r') as f:
        metadata = json.load(f)

    assert 'n_epochs' in metadata
    assert metadata['n_epochs'] == 10
    assert 'alpha_band' in metadata
    assert metadata['alpha_band'] == (8.0, 12.0)