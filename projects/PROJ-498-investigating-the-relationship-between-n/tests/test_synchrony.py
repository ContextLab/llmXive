import os
import sys
import tempfile
import numpy as np
import pytest
import mne

# Add code to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))

from synchrony import (
    get_region_for_electrode,
    get_all_electrode_pairs,
    get_pair_id,
    is_valid_pair,
    compute_wpli,
    compute_plv,
    compute_synchrony_metrics,
    save_synchrony_metrics
)

def test_get_region_for_electrode():
    assert get_region_for_electrode("F3") == "DLPFC"
    assert get_region_for_electrode("P3") == "Parietal"
    assert get_region_for_electrode("Cz") is None

def test_get_all_electrode_pairs():
    pairs = get_all_electrode_pairs()
    assert len(pairs) > 0
    assert ("F3", "P3") in pairs
    assert ("F4", "P4") in pairs

def test_get_pair_id():
    assert get_pair_id(("F3", "P3")) == "F3-P3"

def test_is_valid_pair():
    assert is_valid_pair(("F3", "P3")) is True
    assert is_valid_pair(("F3", "F4")) is False

def test_compute_wpli_constant_phase():
    # If phase difference is constant (e.g., 0), wPLI should be 1.0
    t = np.linspace(0, 1, 1000)
    sig1 = np.sin(2 * np.pi * 10 * t)
    sig2 = np.sin(2 * np.pi * 10 * t) # Same phase
    wpli = compute_wpli(sig1, sig2)
    assert np.isclose(wpli, 1.0, atol=0.1)

def test_compute_wpli_random_phase():
    # Random phase difference should yield wPLI near 0
    np.random.seed(42)
    t = np.linspace(0, 1, 1000)
    sig1 = np.sin(2 * np.pi * 10 * t + np.random.rand(len(t)))
    sig2 = np.sin(2 * np.pi * 10 * t + np.random.rand(len(t)))
    wpli = compute_wpli(sig1, sig2)
    # Should be significantly less than 1, but not necessarily 0
    assert wpli < 0.8

def test_save_synchrony_metrics(tmp_path):
    output_file = os.path.join(tmp_path, "test.csv")
    metrics = [
        {'pair_id': 'F3-P3', 'band': 'theta', 'value': 0.5},
        {'pair_id': 'F3-P3', 'band': 'gamma', 'value': 0.2}
    ]
    save_synchrony_metrics("sub-01", metrics, output_file)

    assert os.path.exists(output_file)
    with open(output_file, 'r') as f:
        lines = f.readlines()
    assert len(lines) == 3 # Header + 2 data rows
    assert "subject_id" in lines[0]
    assert "sub-01" in lines[1]

def test_compute_synchrony_metrics_mock_epochs():
    # Create mock epochs
    n_channels = 4
    n_times = 1000
    sfreq = 1000
    ch_names = ["F3", "F4", "P3", "P4"]
    info = mne.create_info(ch_names=ch_names, sfreq=sfreq, ch_types='eeg')
    data = np.random.randn(n_channels, n_times)
    events = np.array([[0, 0, 1], [100, 0, 1]])
    event_id = {'stim': 1}
    epochs = mne.EpochsArray(
        data[np.newaxis, :, :], # (n_epochs, n_channels, n_times)
        info,
        events=events,
        event_id=event_id,
        tmin=0
    )
    # Adjust data to be (n_epochs, n_channels, n_times)
    epochs._data = np.tile(data[np.newaxis, :, :], (2, 1, 1))

    metrics = compute_synchrony_metrics(epochs)
    assert len(metrics) > 0
    assert all('subject_id' not in m for m in metrics) # This function doesn't add subject_id
    assert all('pair_id' in m for m in metrics)
    assert all('band' in m for m in metrics)
    assert all('value' in m for m in metrics)