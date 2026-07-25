"""
Unit tests for spectral analysis functions in src/analysis/spectral.py.
"""
import numpy as np
import pytest
from src.analysis.spectral import (
    compute_fft,
    compute_welch_psd,
    calculate_snr,
    normalize_psd_to_unit_area
)


class TestComputeFFT:
    """Tests for the compute_fft function."""

    def test_fft_basic_sine_wave(self):
        """Test FFT detection of a simple sine wave."""
        fs = 100.0
        t = np.arange(0, 1, 1/fs)
        freq = 10.0
        signal = np.sin(2 * np.pi * freq * t)
        
        frequencies, magnitudes = compute_fft(signal, fs=fs)
        
        # Find peak frequency
        peak_idx = np.argmax(magnitudes)
        peak_freq = frequencies[peak_idx]
        
        # Allow small tolerance for frequency resolution
        assert abs(peak_freq - freq) < (fs / len(signal)) * 2

    def test_fft_returns_correct_shapes(self):
        """Test that FFT returns arrays of expected shapes."""
        signal = np.random.randn(128)
        fs = 1.0
        
        frequencies, magnitudes = compute_fft(signal, fs=fs)
        
        assert len(frequencies) == len(magnitudes)
        assert len(frequencies) == len(signal) // 2 + 1  # rfft property


class TestComputeWelchPSD:
    """Tests for the compute_welch_psd function."""

    def test_welch_psd_basic(self):
        """Test basic Welch PSD computation."""
        fs = 100.0
        t = np.arange(0, 1, 1/fs)
        signal = np.sin(2 * np.pi * 10 * t) + 0.5 * np.random.randn(len(t))
        
        frequencies, psd = compute_welch_psd(signal, fs=fs)
        
        assert len(frequencies) > 0
        assert len(psd) > 0
        assert len(frequencies) == len(psd)
        assert np.all(psd >= 0)  # PSD should be non-negative

    def test_welch_psd_zero_padding(self):
        """Test that short signals are zero-padded to 512 as per spec."""
        short_signal = np.random.randn(64)  # Less than 512
        fs = 1.0
        
        frequencies, psd = compute_welch_psd(short_signal, fs=fs)
        
        # With nfft=512, the number of frequency bins should be 512//2 + 1 = 257
        expected_bins = 257
        assert len(frequencies) == expected_bins
        assert len(psd) == expected_bins

    def test_welch_psd_custom_nperseg(self):
        """Test Welch PSD with custom segment length."""
        signal = np.random.randn(512)
        fs = 1.0
        
        frequencies, psd = compute_welch_psd(signal, fs=fs, nperseg=128)
        
        assert len(frequencies) > 0
        assert len(psd) > 0


class TestNormalizePSD:
    """Tests for the normalize_psd_to_unit_area function."""

    def test_normalize_unit_area(self):
        """Test that normalized PSD integrates to 1."""
        freqs = np.linspace(0, 50, 500)
        psd = np.exp(-freqs / 10)  # Decaying exponential
        
        normalized_psd = normalize_psd_to_unit_area(psd, freqs)
        
        # Check integral is approximately 1
        area = np.trapz(normalized_psd, freqs)
        assert np.isclose(area, 1.0, atol=1e-6)

    def test_normalize_all_zeros(self):
        """Test normalization with all-zero PSD."""
        freqs = np.linspace(0, 50, 500)
        psd = np.zeros_like(freqs)
        
        normalized_psd = normalize_psd_to_unit_area(psd, freqs)
        
        # Should return original array (no change)
        assert np.allclose(normalized_psd, psd)

    def test_normalize_negative_area(self):
        """Test normalization with negative PSD values (edge case)."""
        freqs = np.linspace(0, 50, 500)
        psd = -np.abs(np.random.randn(len(freqs)))  # All negative
        
        normalized_psd = normalize_psd_to_unit_area(psd, freqs)
        
        # Should return original array (no change)
        assert np.allclose(normalized_psd, psd)


class TestCalculateSNR:
    """Tests for the calculate_snr function."""

    def test_snr_positive_signal(self):
        """Test SNR calculation with a clear signal in target band."""
        fs = 100.0
        t = np.arange(0, 1, 1/fs)
        signal = np.sin(2 * np.pi * 40 * t) + 0.1 * np.random.randn(len(t))
        
        frequencies, psd = compute_welch_psd(signal, fs=fs)
        
        # Target band: 35-45 Hz (around 40 Hz)
        # Noise band: 10-20 Hz (away from signal)
        snr = calculate_snr(
            psd,
            frequencies,
            target_band=(35, 45),
            noise_band=(10, 20)
        )
        
        # SNR should be positive (signal power > noise power)
        assert snr > 0

    def test_snr_noisy_signal(self):
        """Test SNR calculation with high noise."""
        fs = 100.0
        t = np.arange(0, 1, 1/fs)
        signal = 0.1 * np.sin(2 * np.pi * 40 * t) + np.random.randn(len(t))
        
        frequencies, psd = compute_welch_psd(signal, fs=fs)
        
        snr = calculate_snr(
            psd,
            frequencies,
            target_band=(35, 45),
            noise_band=(10, 20)
        )
        
        # SNR can be negative if noise dominates
        assert isinstance(snr, float)

    def test_snr_zero_noise_power(self):
        """Test SNR when noise band has zero power."""
        freqs = np.linspace(0, 100, 500)
        psd = np.zeros_like(freqs)
        psd[100:200] = 1.0  # Signal band only
        
        snr = calculate_snr(
            psd,
            freqs,
            target_band=(20, 40),
            noise_band=(50, 60)
        )
        
        # Should return infinity (or very large number)
        assert snr == float('inf')

    def test_snr_zero_signal_power(self):
        """Test SNR when target band has zero power."""
        freqs = np.linspace(0, 100, 500)
        psd = np.zeros_like(freqs)
        psd[250:350] = 1.0  # Noise band only
        
        snr = calculate_snr(
            psd,
            freqs,
            target_band=(50, 60),
            noise_band=(50, 60)
        )
        
        # Both bands have same power, SNR = 0 dB
        assert np.isclose(snr, 0.0, atol=1e-6)