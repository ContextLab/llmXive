import numpy as np
import pytest
from src.analysis.spectral import (
    compute_fft,
    compute_welch_psd,
    normalize_psd_to_unit_area,
    calculate_snr
)

class TestComputeFFT:
    def test_compute_fft_basic(self):
        """Test FFT on a simple sine wave."""
        fs = 100.0
        t = np.linspace(0, 1, int(fs), endpoint=False)
        freq = 10.0
        signal = np.sin(2 * np.pi * freq * t)
        
        frequencies, magnitudes = compute_fft(signal, sample_rate=fs)
        
        # Find the peak frequency
        peak_idx = np.argmax(magnitudes)
        peak_freq = frequencies[peak_idx]
        
        assert np.isclose(peak_freq, freq, atol=1.0), f"Expected peak near {freq} Hz, got {peak_freq}"
        assert len(frequencies) == len(magnitudes)
        assert np.all(frequencies >= 0)

    def test_compute_fft_zero_signal(self):
        """Test FFT on a zero signal."""
        signal = np.zeros(100)
        frequencies, magnitudes = compute_fft(signal, sample_rate=1.0)
        
        assert np.allclose(magnitudes, 0.0)

    def test_compute_fft_dimension_error(self):
        """Test that 2D signal raises error."""
        signal = np.zeros((10, 10))
        with pytest.raises(ValueError):
            compute_fft(signal)

class TestComputeWelchPSD:
    def test_compute_welch_psd_basic(self):
        """Test Welch PSD computation."""
        fs = 100.0
        t = np.linspace(0, 1, int(fs), endpoint=False)
        signal = np.sin(2 * np.pi * 10 * t) + 0.5 * np.random.randn(len(t))
        
        frequencies, psd = compute_welch_psd(signal, fs=fs, nperseg=32)
        
        assert len(frequencies) == len(psd)
        assert np.all(frequencies >= 0)
        assert np.all(psd >= 0)

    def test_compute_welch_psd_zero_padding(self):
        """Test Welch PSD with zero padding logic."""
        signal = np.sin(2 * np.pi * 10 * np.linspace(0, 0.5, 50))
        # seq_len > len(signal) should trigger padding
        frequencies, psd = compute_welch_psd(signal, fs=100.0, seq_len=100, nperseg=32)
        
        assert len(frequencies) == len(psd)
        assert np.all(psd >= 0)

    def test_compute_welch_psd_dimension_error(self):
        """Test that 2D signal raises error."""
        signal = np.zeros((10, 10))
        with pytest.raises(ValueError):
            compute_welch_psd(signal)

class TestNormalizePSD:
    def test_normalize_psd_unit_area(self):
        """Test that normalized PSD integrates to 1."""
        freqs = np.linspace(0, 10, 100)
        psd = np.exp(-freqs) # Simple decaying function
        
        normalized_psd = normalize_psd_to_unit_area(psd, freqs)
        
        area = np.trapz(normalized_psd, freqs)
        assert np.isclose(area, 1.0, atol=1e-5)

    def test_normalize_psd_zero_power(self):
        """Test normalization when total power is zero."""
        freqs = np.linspace(0, 10, 100)
        psd = np.zeros(100)
        
        normalized_psd = normalize_psd_to_unit_area(psd, freqs)
        
        assert np.allclose(normalized_psd, 0.0)

    def test_normalize_psd_dimension_error(self):
        """Test mismatched dimensions."""
        psd = np.zeros(10)
        freqs = np.zeros(5)
        with pytest.raises(ValueError):
            normalize_psd_to_unit_area(psd, freqs)

class TestCalculateSNR:
    def test_calculate_snr_basic(self):
        """Test SNR calculation with a clear peak."""
        # Create a signal with a strong peak at 40 Hz and low noise elsewhere
        freqs = np.linspace(0, 100, 1000)
        psd = np.ones(1000) * 0.1 # Base noise
        # Add a peak at 40 Hz
        peak_indices = (freqs >= 38) & (freqs <= 42)
        psd[peak_indices] = 10.0
        
        snr = calculate_snr(psd, freqs, target_band=(38.0, 42.0), adjacent_band_width=5.0)
        
        assert snr > 0.0 # Should be positive dB
        # Rough check: signal is ~100x noise (10 vs 0.1) -> 20dB. Allow some margin.
        assert snr > 10.0

    def test_calculate_snr_zero_noise(self):
        """Test SNR when noise power is effectively zero."""
        freqs = np.linspace(0, 100, 1000)
        psd = np.zeros(1000)
        psd[400:410] = 1.0 # Peak only in target
        
        # This might return inf or a very large number depending on implementation
        # We just check it doesn't crash
        snr = calculate_snr(psd, freqs, target_band=(38.0, 42.0), adjacent_band_width=5.0)
        assert not np.isnan(snr)

    def test_calculate_snr_missing_target_band(self):
        """Test error when target band has no data."""
        freqs = np.linspace(0, 100, 1000)
        psd = np.ones(1000)
        
        with pytest.raises(ValueError):
            # Target band is way outside range
            calculate_snr(psd, freqs, target_band=(200.0, 210.0))

    def test_calculate_snr_missing_noise_band(self):
        """Test error when noise band has no data."""
        freqs = np.linspace(0, 100, 1000)
        psd = np.ones(1000)
        
        with pytest.raises(ValueError):
            # Noise band would be outside range if target is at edge
            calculate_snr(psd, freqs, target_band=(98.0, 100.0), adjacent_band_width=5.0)

    def test_calculate_snr_dimension_error(self):
        """Test mismatched dimensions."""
        psd = np.zeros(10)
        freqs = np.zeros(5)
        with pytest.raises(ValueError):
            calculate_snr(psd, freqs, target_band=(0, 1))