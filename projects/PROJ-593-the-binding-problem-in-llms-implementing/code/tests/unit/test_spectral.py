import numpy as np
import pytest
from src.analysis.spectral import (
    compute_fft,
    compute_welch_psd,
    normalize_psd_to_unit_area,
    calculate_snr
)

class TestComputeFFT:
    def test_fft_basic(self):
        """Test FFT on a simple sine wave."""
        fs = 100.0
        t = np.arange(0, 1, 1/fs)
        freq = 5.0
        signal = np.sin(2 * np.pi * freq * t)
        
        freqs, fft_vals = compute_fft(signal, fs=fs)
        
        # Check that we have the right number of frequency bins
        assert len(freqs) == len(fft_vals)
        assert len(freqs) == len(t) // 2 + 1  # rfft length
        
        # Check that the peak frequency is detected
        # Find the index of the maximum magnitude
        peak_idx = np.argmax(np.abs(fft_vals))
        detected_freq = freqs[peak_idx]
        
        # Allow some tolerance due to spectral leakage
        assert abs(detected_freq - freq) < 1.0

    def test_fft_constant(self):
        """Test FFT on a constant signal."""
        signal = np.ones(100)
        freqs, fft_vals = compute_fft(signal, fs=1.0)
        
        # DC component should be dominant
        assert np.abs(fft_vals[0]) > np.sum(np.abs(fft_vals[1:]))

class TestComputeWelchPSD:
    def test_welch_psd_basic(self):
        """Test Welch PSD on a generated signal."""
        fs = 100.0
        t = np.arange(0, 10, 1/fs)
        freq = 10.0
        signal = np.sin(2 * np.pi * freq * t) + 0.1 * np.random.randn(len(t))
        
        freqs, psd = compute_welch_psd(signal, fs=fs, nperseg=128)
        
        assert len(freqs) == len(psd)
        assert np.all(psd >= 0)
        
        # Check that the peak is near the expected frequency
        peak_idx = np.argmax(psd)
        detected_freq = freqs[peak_idx]
        assert abs(detected_freq - freq) < 2.0  # Wider tolerance for Welch

    def test_welch_psd_padding(self):
        """Test that short signals are padded as per T047 logic."""
        signal = np.sin(2 * np.pi * 5 * np.arange(0, 0.1, 0.01)) # Short signal
        # Length is 10. T047 says pad to 512 if seq_len < 512.
        freqs, psd = compute_welch_psd(signal, fs=100.0)
        
        # The nfft used internally should be 512
        # This results in higher frequency resolution
        assert len(freqs) == 257  # 512 // 2 + 1 for rfft

class TestNormalizePSD:
    def test_normalize_unit_area(self):
        """Test that normalized PSD integrates to 1."""
        psd = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        freqs = np.array([10.0, 20.0, 30.0, 40.0, 50.0])
        
        normalized = normalize_psd_to_unit_area(psd, freqs)
        
        df = freqs[1] - freqs[0]
        total_area = np.sum(normalized) * df
        
        assert np.isclose(total_area, 1.0, atol=1e-5)

    def test_normalize_zero_psd(self):
        """Test normalization with zero PSD."""
        psd = np.zeros(5)
        freqs = np.arange(5)
        
        normalized = normalize_psd_to_unit_area(psd, freqs)
        
        # Should return zeros without error
        assert np.all(normalized == 0)

class TestCalculateSNR:
    def test_snr_calculation(self):
        """Test SNR calculation with known signal and noise."""
        # Create a synthetic PSD with a clear peak
        freqs = np.linspace(0, 100, 1000)
        psd = np.ones_like(freqs) * 0.1  # Baseline noise
        
        # Add a peak at 40Hz
        peak_idx = np.argmin(np.abs(freqs - 40))
        psd[peak_idx-5:peak_idx+5] = 10.0  # Signal power
        
        target_band = (38.0, 42.0)
        noise_band = (30.0, 35.0)
        
        snr = calculate_snr(psd, freqs, target_band, noise_band)
        
        # SNR should be positive and significant
        assert snr > 0
        # Expected: 10 * log10(10.0 / 0.1) = 20 dB
        assert np.isclose(snr, 20.0, atol=1.0)

    def test_snr_negative(self):
        """Test SNR when noise is stronger than signal."""
        freqs = np.linspace(0, 100, 1000)
        psd = np.ones_like(freqs) * 1.0  # High noise
        
        # Weak signal
        peak_idx = np.argmin(np.abs(freqs - 40))
        psd[peak_idx-5:peak_idx+5] = 0.5  # Signal power < noise
        
        target_band = (38.0, 42.0)
        noise_band = (30.0, 35.0)
        
        snr = calculate_snr(psd, freqs, target_band, noise_band)
        
        # SNR should be negative
        assert snr < 0

    def test_snr_missing_band(self):
        """Test SNR when bands are out of range."""
        freqs = np.linspace(0, 50, 100)
        psd = np.ones_like(freqs)
        
        with pytest.raises(ValueError):
            calculate_snr(psd, freqs, (60.0, 70.0), (10.0, 20.0))