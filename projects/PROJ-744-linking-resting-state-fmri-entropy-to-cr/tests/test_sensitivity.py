"""
Tests for sensitivity analysis and surrogate data generation (T042, T043, T044).
"""
import numpy as np
import pandas as pd
import pytest
from pathlib import Path
import sys
import os

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'code'))

from sensitivity import generate_phase_randomized_surrogate, run_surrogate_generation, run_surrogate_validation

def test_phase_randomized_surrogate_preserves_spectrum():
    """
    Test that the surrogate preserves the power spectrum of the original time series.
    """
    # Create a simple time series with known spectrum
    np.random.seed(42)
    n = 1000
    t = np.linspace(0, 1, n)
    # Signal with a dominant frequency
    signal = np.sin(2 * np.pi * 5 * t) + 0.5 * np.sin(2 * np.pi * 10 * t) + 0.1 * np.random.randn(n)

    surrogate = generate_phase_randomized_surrogate(signal)

    # Compute power spectra
    fft_signal = np.fft.fft(signal)
    fft_surrogate = np.fft.fft(surrogate)

    power_signal = np.abs(fft_signal) ** 2
    power_surrogate = np.abs(fft_surrogate) ** 2

    # They should be very close (up to numerical precision)
    np.testing.assert_array_almost_equal(power_signal, power_surrogate, decimal=10)

def test_phase_randomized_surrogate_changes_time_structure():
    """
    Test that the surrogate has a different time structure (autocorrelation) than the original.
    """
    np.random.seed(42)
    n = 1000
    # Create a signal with strong autocorrelation
    signal = np.zeros(n)
    for i in range(1, n):
        signal[i] = 0.9 * signal[i-1] + 0.1 * np.random.randn()

    surrogate = generate_phase_randomized_surrogate(signal)

    # Compute autocorrelation
    autocorr_signal = np.correlate(signal - np.mean(signal), signal - np.mean(signal), mode='full')
    autocorr_signal = autocorr_signal[len(autocorr_signal)//2:]
    autocorr_signal = autocorr_signal / autocorr_signal[0]  # Normalize

    autocorr_surrogate = np.correlate(surrogate - np.mean(surrogate), surrogate - np.mean(surrogate), mode='full')
    autocorr_surrogate = autocorr_surrogate[len(autocorr_surrogate)//2:]
    autocorr_surrogate = autocorr_surrogate / autocorr_surrogate[0]  # Normalize

    # The autocorrelation should be different (surrogate should be more like white noise)
    # We check that the first lag autocorrelation is significantly different
    assert abs(autocorr_signal[1]) > abs(autocorr_surrogate[1]), "Surrogate should have lower autocorrelation"

def test_surrogate_generation_integration(tmp_path):
    """
    Integration test for surrogate generation with mock data.
    """
    # This test is simplified because we can't easily load real HCP data in tests.
    # We'll test the logic with synthetic data that mimics the structure.
    # In a real scenario, we would use mock data or a small subset of real data.

    # Create a mock time series
    np.random.seed(42)
    n = 200
    mock_ts = np.sin(2 * np.pi * 0.1 * np.arange(n)) + 0.5 * np.random.randn(n)

    # Test surrogate generation
    surrogate = generate_phase_randomized_surrogate(mock_ts)
    assert surrogate.shape == mock_ts.shape
    assert not np.allclose(surrogate, mock_ts), "Surrogate should be different from original"

def test_surrogate_validation_logic():
    """
    Test the validation logic with mock data.
    """
    # Create mock surrogate results
    data = {
        'subject_id': ['100306', '100306', '100307'],
        'parcel_index': [1, 2, 1],
        'entropy_real': [1.5, 1.6, 1.4],
        'entropy_surrogate_mean': [1.0, 1.1, 0.9],
        'entropy_surrogate_std': [0.1, 0.1, 0.1],
        'num_surrogates': [10, 10, 10]
    }
    df_surrogate = pd.DataFrame(data)

    # Run validation
    df_validation = run_surrogate_validation(df_surrogate, threshold_percent=10.0)

    # Check that difference and pass_flag are computed correctly
    assert 'difference' in df_validation.columns
    assert 'difference_pct' in df_validation.columns
    assert 'pass_flag' in df_validation.columns

    # Check specific values
    # For subject 100306, parcel 1: diff = 1.5 - 1.0 = 0.5, pct = 0.5/1.5*100 = 33.33% -> PASS
    assert df_validation.loc[df_validation['subject_id'] == '100306', 'pass_flag'].iloc[0] == True

    # For subject 100307, parcel 1: diff = 1.4 - 0.9 = 0.5, pct = 0.5/1.4*100 = 35.71% -> PASS
    assert df_validation.loc[df_validation['subject_id'] == '100307', 'pass_flag'].iloc[0] == True
