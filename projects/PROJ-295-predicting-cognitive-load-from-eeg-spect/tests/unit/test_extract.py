"""
Unit tests for code/features/extract.py
Specifically tests for Welch's PSD calculation and band limits verification.
"""
import numpy as np
import pytest
import mne
from unittest.mock import patch, MagicMock
import sys
import os

# Ensure the code directory is in the path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from features.extract import compute_psd_welch, extract_band_power

# Constants for testing
SAMPLE_RATE = 250.0  # Hz
DURATION = 10.0  # seconds
FREQ_THETA_LOW, FREQ_THETA_HIGH = 4.0, 7.0
FREQ_ALPHA_LOW, FREQ_ALPHA_HIGH = 8.0, 12.0
N_CHANNELS = 2

def generate_mock_raw_data(duration, sfreq, n_channels=1):
    """Generate synthetic EEG-like data for testing."""
    n_samples = int(duration * sfreq)
    # Create random noise with some frequency content
    data = np.random.randn(n_channels, n_samples) * 1e-6  # Microvolts
    info = mne.create_info(ch_names=[f'EEG{i:03d}' for i in range(n_channels)], 
                           sfreq=sfreq, ch_types='eeg')
    raw = mne.io.RawArray(data, info)
    return raw

def test_compute_psd_welch_band_limits():
    """
    Verify that compute_psd_welch respects the specified frequency band limits.
    The test checks that the returned frequencies are within the requested range
    and that the power values correspond to the correct frequency bins.
    """
    raw = generate_mock_raw_data(DURATION, SAMPLE_RATE, N_CHANNELS)
    
    # Define a specific band to test
    fmin = 4.0
    fmax = 12.0
    
    # Compute PSD using Welch's method
    freqs, psd = compute_psd_welch(raw, fmin=fmin, fmax=fmax)
    
    # Assertions
    assert isinstance(freqs, np.ndarray), "freqs should be a numpy array"
    assert isinstance(psd, np.ndarray), "psd should be a numpy array"
    assert len(freqs) == psd.shape[1], "Frequency and power dimensions must match"
    
    # Verify that all returned frequencies are within the specified bounds
    assert np.all(freqs >= fmin), f"Lower frequency bound violated: min(freqs)={freqs.min()}, expected >= {fmin}"
    assert np.all(freqs <= fmax), f"Upper frequency bound violated: max(freqs)={freqs.max()}, expected <= {fmax}"
    
    # Verify that the shape matches expected output (n_channels x n_freqs)
    assert psd.shape[0] == N_CHANNELS, f"Expected {N_CHANNELS} channels in PSD output"
    
    # Verify that PSD values are non-negative (power cannot be negative)
    assert np.all(psd >= 0), "PSD values must be non-negative"

def test_compute_psd_welch_default_range():
    """
    Test that compute_psd_welch works with default range (1-45 Hz) as per pipeline config.
    """
    raw = generate_mock_raw_data(DURATION, SAMPLE_RATE, N_CHANNELS)
    
    # Use default range (1-45 Hz)
    freqs, psd = compute_psd_welch(raw)
    
    assert np.min(freqs) >= 1.0, "Default lower bound should be 1 Hz"
    assert np.max(freqs) <= 45.0, "Default upper bound should be 45 Hz"

def test_extract_band_power_theta():
    """
    Verify extract_band_power correctly isolates theta band (4-7 Hz).
    """
    raw = generate_mock_raw_data(DURATION, SAMPLE_RATE, N_CHANNELS)
    
    theta_power = extract_band_power(raw, FREQ_THETA_LOW, FREQ_THETA_HIGH)
    
    assert isinstance(theta_power, np.ndarray), "Output should be numpy array"
    assert theta_power.shape[0] == N_CHANNELS, "Should have one value per channel"
    assert np.all(theta_power >= 0), "Power values must be non-negative"

def test_extract_band_power_alpha():
    """
    Verify extract_band_power correctly isolates alpha band (8-12 Hz).
    """
    raw = generate_mock_raw_data(DURATION, SAMPLE_RATE, N_CHANNELS)
    
    alpha_power = extract_band_power(raw, FREQ_ALPHA_LOW, FREQ_ALPHA_HIGH)
    
    assert isinstance(alpha_power, np.ndarray), "Output should be numpy array"
    assert alpha_power.shape[0] == N_CHANNELS, "Should have one value per channel"
    assert np.all(alpha_power >= 0), "Power values must be non-negative"

def test_extract_band_power_empty_range():
    """
    Verify behavior when frequency range is invalid or empty.
    """
    raw = generate_mock_raw_data(DURATION, SAMPLE_RATE, N_CHANNELS)
    
    # This should raise an error or return empty/zero depending on implementation
    # For robustness, we expect it to handle invalid ranges gracefully
    with pytest.raises(ValueError):
        extract_band_power(raw, 15.0, 10.0)  # fmin > fmax

def test_compute_psd_welch_frequency_resolution():
    """
    Verify that the frequency resolution is appropriate for the given duration.
    Frequency resolution = 1 / duration
    """
    raw = generate_mock_raw_data(DURATION, SAMPLE_RATE, N_CHANNELS)
    
    freqs, psd = compute_psd_welch(raw)
    
    # Expected resolution
    expected_resolution = 1.0 / DURATION
    
    # Check that the difference between consecutive frequencies is approximately the resolution
    if len(freqs) > 1:
        actual_resolution = np.diff(freqs)
        # Allow small floating point errors
        assert np.allclose(actual_resolution, expected_resolution, atol=1e-6), \
            f"Frequency resolution mismatch: expected ~{expected_resolution}, got {actual_resolution[0]}"

def test_compute_psd_welch_with_realistic_data():
    """
    Test with data that has known spectral characteristics to ensure correctness.
    """
    # Create a signal with a known peak at 10 Hz (alpha)
    n_samples = int(DURATION * SAMPLE_RATE)
    time = np.arange(n_samples) / SAMPLE_RATE
    data = np.sin(2 * np.pi * 10 * time) * 1e-6  # 10 Hz sine wave
    data = np.vstack([data, data * 0.5])  # Two channels with different amplitudes
    
    info = mne.create_info(ch_names=['EEG001', 'EEG002'], sfreq=SAMPLE_RATE, ch_types='eeg')
    raw = mne.io.RawArray(data, info)
    
    freqs, psd = compute_psd_welch(raw, fmin=8.0, fmax=12.0)
    
    # The peak should be around 10 Hz
    peak_idx = np.argmax(psd[0])
    peak_freq = freqs[peak_idx]
    
    # Allow some tolerance due to frequency binning
    assert 9.0 <= peak_freq <= 11.0, f"Peak frequency {peak_freq} is not within expected range [9, 11]"

if __name__ == '__main__':
    pytest.main([__file__, '-v'])