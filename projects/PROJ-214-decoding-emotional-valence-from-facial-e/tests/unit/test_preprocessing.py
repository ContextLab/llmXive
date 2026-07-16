"""
Unit tests for signal preprocessing functions (filtering, baseline correction).
"""
import pytest
import numpy as np
from scipy.signal import butter, iirnotch
from code.preprocessing import (
    butter_bandpass,
    apply_bandpass_filter,
    apply_notch_filter,
    baseline_correct
)


class TestButterBandpass:
    """Tests for butter_bandpass function."""

    def test_filter_order_and_cutoff(self):
        """Verify filter returns correct order and cutoff values."""
        fs = 512.0
        lowcut = 20.0
        highcut = 450.0
        order = 4

        b, a = butter_bandpass(lowcut, highcut, fs, order)

        assert len(b) == order + 1
        assert len(a) == order + 1
        assert b.dtype == np.float64
        assert a.dtype == np.float64

    def test_invalid_order(self):
        """Verify function handles invalid order gracefully."""
        with pytest.raises(ValueError):
            butter_bandpass(20, 450, 512, -1)


class TestApplyBandpassFilter:
    """Tests for apply_bandpass_filter function."""

    def test_filter_output_shape(self):
        """Verify output shape matches input shape."""
        fs = 512.0
        duration = 1.0
        t = np.linspace(0, duration, int(fs * duration))
        signal = np.sin(2 * np.pi * 100 * t)  # 100Hz sine wave

        filtered = apply_bandpass_filter(signal, fs)

        assert filtered.shape == signal.shape

    def test_filter_rejects_low_frequency(self):
        """Verify low frequency components are attenuated."""
        fs = 512.0
        duration = 2.0
        t = np.linspace(0, duration, int(fs * duration))
        # 5Hz signal (below 20Hz cutoff)
        low_freq = np.sin(2 * np.pi * 5 * t)
        # 100Hz signal (within passband)
        high_freq = np.sin(2 * np.pi * 100 * t)
        mixed = low_freq + high_freq

        filtered = apply_bandpass_filter(mixed, fs)

        # The 5Hz component should be significantly attenuated
        # We check the energy ratio in the low band
        spectrum = np.abs(np.fft.rfft(filtered))
        freqs = np.fft.rfftfreq(len(filtered), 1/fs)

        low_energy = np.sum(spectrum[freqs < 10])
        high_energy = np.sum(spectrum[(freqs >= 80) & (freqs <= 120)])

        # High energy should be much larger than low energy
        assert high_energy > low_energy * 10


class TestApplyNotchFilter:
    """Tests for apply_notch_filter function."""

    def test_notch_output_shape(self):
        """Verify output shape matches input shape."""
        fs = 512.0
        duration = 1.0
        t = np.linspace(0, duration, int(fs * duration))
        signal = np.sin(2 * np.pi * 50 * t)  # 50Hz interference

        filtered = apply_notch_filter(signal, fs)

        assert filtered.shape == signal.shape

    def test_notch_attenuates_50hz(self):
        """Verify 50Hz component is significantly attenuated."""
        fs = 512.0
        duration = 2.0
        t = np.linspace(0, duration, int(fs * duration))
        signal = np.sin(2 * np.pi * 50 * t)

        filtered = apply_notch_filter(signal, fs)

        # Calculate energy before and after
        energy_before = np.sum(signal**2)
        energy_after = np.sum(filtered**2)

        # At least 90% attenuation expected
        assert energy_after < energy_before * 0.1


class TestBaselineCorrect:
    """Tests for baseline_correct function."""

    def test_baseline_correction_zeroes_baseline(self):
        """Verify baseline period is corrected to mean zero."""
        baseline_mean = 5.0
        baseline_length = 100
        signal_length = 500
        signal = np.ones(signal_length) * baseline_mean
        signal[baseline_length:] += 1.0  # Add offset after baseline

        corrected = baseline_correct(signal, baseline_length)

        # The baseline period (first baseline_length samples) should be near zero
        baseline_region = corrected[:baseline_length]
        assert np.abs(np.mean(baseline_region)) < 1e-6

    def test_baseline_correct_preserves_relative_changes(self):
        """Verify relative changes after baseline are preserved."""
        baseline_mean = 2.0
        baseline_length = 100
        signal_length = 500
        signal = np.ones(signal_length) * baseline_mean
        signal[baseline_length:] += 3.0  # Add 3.0 offset after baseline

        corrected = baseline_correct(signal, baseline_length)

        # The post-baseline region should have a mean of ~3.0
        post_baseline = corrected[baseline_length:]
        assert np.abs(np.mean(post_baseline) - 3.0) < 1e-5

    def test_invalid_baseline_length(self):
        """Verify function handles invalid baseline length."""
        signal = np.ones(100)
        with pytest.raises(ValueError):
            baseline_correct(signal, 150)
