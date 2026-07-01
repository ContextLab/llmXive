import numpy as np
import pytest
from scipy.signal import butter, filtfilt

from preprocess import (
    bandpass_filter,
    compute_kurtosis,
    compute_high_freq_power,
    validate_no_nan,
)


def test_bandpass_filter():
    """Test that bandpass filter produces output without NaNs."""
    sfreq = 100.0
    lowcut = 0.5
    highcut = 45.0
    order = 4

    # Generate a test signal
    t = np.arange(0, 10, 1 / sfreq)
    signal = np.sin(2 * np.pi * 10 * t) + np.random.randn(len(t)) * 0.1
    signal = signal.reshape(1, -1)

    filtered = bandpass_filter(signal, sfreq, lowcut, highcut, order)

    assert filtered.shape == signal.shape
    assert not np.any(np.isnan(filtered))


def test_compute_kurtosis():
    """Test kurtosis calculation on known distribution."""
    # Normal distribution has kurtosis ~3
    data = np.random.randn(10000)
    kurt = compute_kurtosis(data)
    # Allow some tolerance due to randomness
    assert 2.5 < kurt < 3.5


def test_compute_high_freq_power():
    """Test high-frequency power calculation."""
    sfreq = 100.0
    t = np.arange(0, 10, 1 / sfreq)
    # Signal with known high-freq component
    signal = np.sin(2 * np.pi * 40 * t)  # 40 Hz
    power = compute_high_freq_power(signal, sfreq, high_freq_start=30.0)
    # Should be non-zero
    assert power > 0


def test_validate_no_nan():
    """Test NaN validation."""
    clean_data = np.array([1.0, 2.0, 3.0])
    assert validate_no_nan(clean_data) is True

    nan_data = np.array([1.0, np.nan, 3.0])
    assert validate_no_nan(nan_data) is False
