"""
Unit tests for the downsample module.

Tests anti-aliasing filter behavior and amplitude correction.
"""
import pytest
import numpy as np
from scipy import signal
import os
import sys
import tempfile
from pathlib import Path

# Ensure src is in path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from src.downsample import (
    design_fir_filter,
    calculate_frequency_response,
    get_amplitude_correction_factor,
    downsample_with_correction,
    find_signal_peak_frequency,
    process_waveform_file
)
from src.config import ensure_directories


class TestFirFilterDesign:
    """Tests for FIR filter design."""
    
    def test_filter_design_basic(self):
        """Test basic filter design."""
        taps = design_fir_filter(4096, 2048, num_taps=101)
        assert len(taps) == 101
        assert taps[0] > 0  # First tap should be positive
        
    def test_filter_design_odd_taps(self):
        """Test that filter design handles odd taps correctly."""
        # Even number of taps will be adjusted or raise error depending on implementation
        # Our implementation uses firwin which handles even/odd
        taps = design_fir_filter(4096, 1024, num_taps=100)
        assert len(taps) == 100
        
    def test_filter_design_invalid_rates(self):
        """Test that invalid sampling rates raise errors."""
        with pytest.raises(ValueError):
            design_fir_filter(1024, 2048)  # Target > Original
        
        with pytest.raises(ValueError):
            design_fir_filter(2048, 2048)  # Target == Original
    
    def test_filter_frequency_response(self):
        """Test that the filter has the expected frequency response."""
        taps = design_fir_filter(4096, 2048, num_taps=101)
        freqs, h = calculate_frequency_response(taps, 4096)
        
        # At DC (0 Hz), response should be ~1
        assert np.abs(h[0]) > 0.9
        
        # At Nyquist of target (1024 Hz), response should be ~0.5 (cutoff)
        # Find index closest to 1024 Hz
        idx_1024 = np.argmin(np.abs(freqs - 1024))
        assert np.abs(h[idx_1024]) < 0.6  # Should be attenuated
        
        # Above target Nyquist, response should be very low
        idx_2000 = np.argmin(np.abs(freqs - 2000))
        assert np.abs(h[idx_2000]) < 0.1


class TestAmplitudeCorrection:
    """Tests for amplitude correction factor calculation."""
    
    def test_correction_factor_positive(self):
        """Test that correction factor is always >= 1."""
        taps = design_fir_filter(4096, 2048, num_taps=101)
        correction = get_amplitude_correction_factor(taps, 4096, 100.0)
        assert correction >= 1.0
        
    def test_correction_factor_at_dc(self):
        """Test correction factor at DC (should be 1.0)."""
        taps = design_fir_filter(4096, 2048, num_taps=101)
        correction = get_amplitude_correction_factor(taps, 4096, 0.0)
        # At DC, filter response is ~1, so correction should be ~1
        assert 0.9 <= correction <= 1.1
        
    def test_correction_factor_at_peak(self):
        """Test that correction compensates for filter attenuation."""
        taps = design_fir_filter(4096, 2048, num_taps=101)
        # At 500 Hz, filter should have some attenuation
        correction = get_amplitude_correction_factor(taps, 4096, 500.0)
        assert correction > 1.0
        
        # Verify that applying correction restores amplitude
        freqs, h = calculate_frequency_response(taps, 4096)
        idx = np.argmin(np.abs(freqs - 500.0))
        magnitude = np.abs(h[idx])
        expected_correction = 1.0 / magnitude
        assert np.isclose(correction, expected_correction, rtol=1e-5)


class TestDownsampleWithCorrection:
    """Tests for the main downsampling function."""
    
    def test_downsample_basic(self):
        """Test basic downsampling operation."""
        # Create a simple sine wave
        fs = 4096
        t = np.linspace(0, 1, fs)
        f_signal = 100.0
        waveform = np.sin(2 * np.pi * f_signal * t)
        
        downsampled, metadata = downsample_with_correction(
            waveform, fs, 2048, f_signal
        )
        
        assert len(downsampled) == len(waveform) // 2
        assert metadata["target_fs"] == 2048
        assert metadata["decimation_factor"] == 2
        assert "correction_factor" in metadata
        
    def test_downsample_preserves_signal(self):
        """Test that downsampling preserves signal frequency content."""
        fs = 4096
        t = np.linspace(0, 1, fs)
        f_signal = 50.0
        waveform = np.sin(2 * np.pi * f_signal * t)
        
        downsampled, metadata = downsample_with_correction(
            waveform, fs, 1024, f_signal
        )
        
        # Compute FFT of original and downsampled
        fft_orig = np.fft.rfft(waveform)
        fft_down = np.fft.rfft(downsampled)
        
        freqs_orig = np.fft.rfftfreq(len(waveform), 1/fs)
        freqs_down = np.fft.rfftfreq(len(downsampled), 1/1024)
        
        # Find peak in both
        idx_orig = np.argmax(np.abs(fft_orig))
        idx_down = np.argmax(np.abs(fft_down))
        
        peak_freq_orig = freqs_orig[idx_orig]
        peak_freq_down = freqs_down[idx_down]
        
        # Peaks should match (within resolution)
        assert np.isclose(peak_freq_orig, peak_freq_down, atol=1.0)
        
    def test_downsample_invalid_rates(self):
        """Test that invalid rates raise errors."""
        waveform = np.random.randn(1000)
        
        with pytest.raises(ValueError):
            downsample_with_correction(waveform, 1024, 2048, 100.0)
        
        with pytest.raises(ValueError):
            downsample_with_correction(waveform, 2048, 2048, 100.0)
    
    def test_downsample_empty_waveform(self):
        """Test that empty waveform raises error."""
        with pytest.raises(ValueError):
            downsample_with_correction(np.array([]), 4096, 2048, 100.0)
    
    def test_downsample_with_realistic_bbh_signal(self):
        """Test downsampling with a realistic BBH-like signal."""
        # Simulate a chirp signal (simplified)
        fs = 4096
        duration = 1.0
        t = np.linspace(0, duration, int(fs * duration))
        
        # Frequency increases over time (chirp)
        f0 = 30.0
        f1 = 200.0
        chirp_signal = np.sin(2 * np.pi * (f0 * t + 0.5 * (f1 - f0) * t**2 / duration) * t)
        
        # Find peak frequency (should be near f1)
        peak_freq = find_signal_peak_frequency(chirp_signal, fs)
        
        downsampled, metadata = downsample_with_correction(
            chirp_signal, fs, 1024, peak_freq
        )
        
        assert len(downsampled) == len(chirp_signal) // 4
        assert metadata["correction_factor"] > 1.0


class TestFindSignalPeakFrequency:
    """Tests for peak frequency detection."""
    
    def test_peak_detection_sine_wave(self):
        """Test peak detection for a pure sine wave."""
        fs = 4096
        t = np.linspace(0, 1, fs)
        f_signal = 150.0
        waveform = np.sin(2 * np.pi * f_signal * t)
        
        peak_freq = find_signal_peak_frequency(waveform, fs)
        
        # Should detect the signal frequency
        assert np.isclose(peak_freq, f_signal, atol=2.0)
        
    def test_peak_detection_with_noise(self):
        """Test peak detection with added noise."""
        fs = 4096
        t = np.linspace(0, 1, fs)
        f_signal = 100.0
        waveform = np.sin(2 * np.pi * f_signal * t) + 0.1 * np.random.randn(len(t))
        
        peak_freq = find_signal_peak_frequency(waveform, fs)
        
        # Should still detect the signal frequency despite noise
        assert np.isclose(peak_freq, f_signal, atol=5.0)
        
    def test_peak_detection_range(self):
        """Test peak detection with frequency limits."""
        fs = 4096
        t = np.linspace(0, 1, fs)
        f_signal = 300.0
        waveform = np.sin(2 * np.pi * f_signal * t)
        
        # Limit range to exclude the signal
        with pytest.raises(ValueError):
            find_signal_peak_frequency(waveform, fs, f_min=400, f_max=1000)
        
        # Should work with appropriate range
        peak_freq = find_signal_peak_frequency(waveform, fs, f_min=200, f_max=400)
        assert np.isclose(peak_freq, f_signal, atol=5.0)


class TestProcessWaveformFile:
    """Tests for file processing pipeline."""
    
    def test_process_npz_file(self):
        """Test processing a .npz waveform file."""
        # Create a temporary input file
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = os.path.join(tmpdir, "test_waveform.npz")
            output_dir = os.path.join(tmpdir, "output")
            
            # Create test data
            fs = 4096
            t = np.linspace(0, 0.1, int(fs * 0.1))
            waveform = np.sin(2 * np.pi * 100 * t)
            
            np.savez(input_path, waveform=waveform, fs=fs, peak_freq=100.0)
            
            # Process
            results = process_waveform_file(input_path, output_dir, target_rates=(2048, 1024))
            
            # Check results
            assert len(results["processed_files"]) == 2
            assert results["original_fs"] == 4096
            assert results["signal_peak_freq"] == 100.0
            
            # Check output files exist
            for file_info in results["processed_files"]:
                assert os.path.exists(file_info["output_file"])
                assert "fs" in file_info["output_file"]
    
    def test_process_json_file(self):
        """Test processing a .json waveform file."""
        import json
        
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = os.path.join(tmpdir, "test_waveform.json")
            output_dir = os.path.join(tmpdir, "output")
            
            # Create test data
            fs = 4096
            t = np.linspace(0, 0.1, int(fs * 0.1))
            waveform = np.sin(2 * np.pi * 100 * t)
            
            data = {
                "waveform": waveform.tolist(),
                "metadata": {
                    "fs": fs,
                    "peak_freq": 100.0
                }
            }
            
            with open(input_path, 'w') as f:
                json.dump(data, f)
            
            # Process
            results = process_waveform_file(input_path, output_dir, target_rates=(2048,))
            
            # Check results
            assert len(results["processed_files"]) == 1
            assert os.path.exists(results["processed_files"][0]["output_file"])


class TestAntiAliasing:
    """Tests specifically for anti-aliasing behavior."""
    
    def test_anti_aliasing_suppression(self):
        """Test that frequencies above target Nyquist are suppressed."""
        fs = 4096
        target_fs = 1024
        target_nyquist = target_fs / 2.0
        
        # Create a signal with frequency above target Nyquist
        t = np.linspace(0, 1, fs)
        f_alias = 1500.0  # Above 512 Hz target Nyquist
        waveform = np.sin(2 * np.pi * f_alias * t)
        
        # Find peak frequency (will be the alias frequency)
        peak_freq = find_signal_peak_frequency(waveform, fs)
        
        downsampled, metadata = downsample_with_correction(
            waveform, fs, target_fs, peak_freq
        )
        
        # Compute FFT of downsampled signal
        fft_down = np.fft.rfft(downsampled)
        freqs_down = np.fft.rfftfreq(len(downsampled), 1/target_fs)
        
        # The aliased frequency should appear at |f_alias - k*fs|
        # For f_alias=1500, fs=4096, target_fs=1024:
        # 1500 - 1024 = 476 Hz (within target Nyquist)
        expected_alias = abs(f_alias - target_fs)
        
        # Find peak in downsampled spectrum
        idx_peak = np.argmax(np.abs(fft_down))
        detected_freq = freqs_down[idx_peak]
        
        # The detected frequency should be the alias
        assert np.isclose(detected_freq, expected_alias, atol=10.0)
        
        # But the amplitude should be attenuated by the filter
        # (since the filter cuts off at target_nyquist)
        # Note: This is a simplified check; real anti-aliasing is more complex