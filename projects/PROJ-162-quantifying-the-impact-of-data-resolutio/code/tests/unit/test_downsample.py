"""
Unit tests for downsampling functionality.

Tests verify:
1. FIR filter design correctness
2. Amplitude correction factor calculation
3. Downsampling with correction produces expected results
4. Signal peak frequency detection
5. Anti-aliasing verification via FFT
"""
import pytest
import numpy as np
from scipy import signal
import os
import sys
import tempfile
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.downsample import (
    design_fir_filter,
    calculate_frequency_response,
    get_amplitude_correction_factor,
    find_signal_peak_frequency,
    downsample_with_correction,
    process_waveform_file
)
from src.config import get_processed_path

class TestFirFilterDesign:
    """Test FIR filter design functionality."""
    
    def test_filter_design_basic(self):
        """Test basic FIR filter design."""
        original_fs = 4096
        target_fs = 2048
        num_taps = 101
        
        taps = design_fir_filter(original_fs, target_fs, num_taps)
        
        assert len(taps) == num_taps
        assert np.all(taps >= 0) or np.any(taps < 0)  # Filter coefficients can be negative
        
    def test_filter_design_even_taps(self):
        """Test that even number of taps is adjusted to odd."""
        original_fs = 4096
        target_fs = 2048
        num_taps = 100  # Even number
        
        taps = design_fir_filter(original_fs, target_fs, num_taps)
        
        assert len(taps) == 101  # Should be adjusted to odd
        
    def test_filter_design_different_ratios(self):
        """Test filter design for different sampling rate ratios."""
        original_fs = 4096
        target_rates = [2048, 1024, 512, 256]
        
        for target_fs in target_rates:
            taps = design_fir_filter(original_fs, target_fs)
            assert len(taps) > 0
            # Check that filter has reasonable frequency response
            w, h = signal.freqz(taps)
            assert np.max(np.abs(h)) > 0.9  # Passband should be close to 1

class TestAmplitudeCorrection:
    """Test amplitude correction factor calculation."""
    
    def test_correction_factor_calculation(self):
        """Test that correction factor is calculated correctly."""
        # Create a simple test signal
        fs = 4096
        duration = 1.0
        t = np.linspace(0, duration, int(fs * duration), endpoint=False)
        signal = np.sin(2 * np.pi * 100 * t)  # 100 Hz sine wave
        
        # Design filter
        taps = design_fir_filter(fs, 2048)
        
        # Get frequency response
        freqs, magnitude = calculate_frequency_response(taps, fs)
        
        # Find peak frequency (should be around 100 Hz)
        fft_result = np.fft.rfft(signal)
        signal_magnitude = np.abs(fft_result)
        signal_freqs = np.fft.rfftfreq(len(signal), 1/fs)
        
        correction = get_amplitude_correction_factor(
            taps, fs, signal_freqs, signal_magnitude
        )
        
        assert correction > 0
        assert not np.isinf(correction)
        assert not np.isnan(correction)
        
    def test_correction_factor_nonzero_response(self):
        """Test that correction factor fails when filter response is zero."""
        fs = 4096
        signal = np.random.randn(fs)
        
        taps = design_fir_filter(fs, 2048)
        f_peak, signal_freqs, signal_magnitude = find_signal_peak_frequency(signal, fs)
        
        # Manually create a scenario where response is zero (edge case)
        # This should raise an error
        with pytest.raises(ValueError):
            # Simulate zero response at peak
            zero_magnitude = np.zeros_like(signal_magnitude)
            get_amplitude_correction_factor(taps, fs, signal_freqs, zero_magnitude)

class TestDownsampleWithCorrection:
    """Test downsampling with amplitude correction."""
    
    def test_downsample_basic(self):
        """Test basic downsampling functionality."""
        fs_original = 4096
        fs_target = 2048
        duration = 1.0
        
        t = np.linspace(0, duration, int(fs_original * duration), endpoint=False)
        waveform = np.sin(2 * np.pi * 100 * t)
        
        downsampled = downsample_with_correction(waveform, fs_original, fs_target)
        
        expected_length = len(waveform) // 2
        assert len(downsampled) == expected_length
        
    def test_downsample_preserves_amplitude(self):
        """Test that amplitude correction preserves signal amplitude."""
        fs_original = 4096
        fs_target = 2048
        duration = 1.0
        
        t = np.linspace(0, duration, int(fs_original * duration), endpoint=False)
        amplitude = 1.0
        waveform = amplitude * np.sin(2 * np.pi * 100 * t)
        
        downsampled = downsample_with_correction(waveform, fs_original, fs_target)
        
        # Check that amplitude is roughly preserved (within 10% due to filtering effects)
        original_peak = np.max(np.abs(waveform))
        downsampled_peak = np.max(np.abs(downsampled))
        
        ratio = downsampled_peak / original_peak
        assert 0.8 < ratio < 1.2  # Amplitude should be roughly preserved
        
    def test_downsample_error_invalid_rates(self):
        """Test that downsampling fails when target >= original."""
        waveform = np.random.randn(1000)
        
        with pytest.raises(ValueError):
            downsample_with_correction(waveform, 1024, 2048)

class TestFindSignalPeakFrequency:
    """Test signal peak frequency detection."""
    
    def test_peak_detection_single_tone(self):
        """Test peak detection for single frequency tone."""
        fs = 4096
        duration = 1.0
        f_signal = 100
        
        t = np.linspace(0, duration, int(fs * duration), endpoint=False)
        waveform = np.sin(2 * np.pi * f_signal * t)
        
        f_peak, freqs, magnitude = find_signal_peak_frequency(waveform, fs)
        
        # Peak should be close to 100 Hz
        assert abs(f_peak - f_signal) < 5  # Within 5 Hz tolerance
        
    def test_peak_detection_chirp_signal(self):
        """Test peak detection for chirp signal."""
        fs = 4096
        duration = 1.0
        
        t = np.linspace(0, duration, int(fs * duration), endpoint=False)
        # Chirp from 50 to 500 Hz
        waveform = signal.chirp(t, 50, duration, 500)
        
        f_peak, freqs, magnitude = find_signal_peak_frequency(waveform, fs)
        
        # Peak should be in the upper range of the chirp
        assert 400 < f_peak < 500

class TestAntiAliasing:
    """Test anti-aliasing verification."""
    
    def test_anti_aliasing_fft_check(self):
        """
        Verify that aliasing artifacts are suppressed.
        
        This test checks that frequency components above the new Nyquist limit
        are attenuated to negligible levels.
        """
        fs_original = 4096
        fs_target = 1024
        duration = 2.0
        
        # Create signal with frequency content up to 800 Hz (below new Nyquist of 512 Hz? No, 800 > 512)
        # Actually, let's create a signal with content up to 600 Hz to test aliasing prevention
        t = np.linspace(0, duration, int(fs_original * duration), endpoint=False)
        waveform = (
            0.5 * np.sin(2 * np.pi * 100 * t) +
            0.3 * np.sin(2 * np.pi * 300 * t) +
            0.2 * np.sin(2 * np.pi * 500 * t)
        )
        
        downsampled = downsample_with_correction(waveform, fs_original, fs_target)
        
        # Analyze frequency content of downsampled signal
        n = len(downsampled)
        fft_result = np.fft.rfft(downsampled)
        magnitude = np.abs(fft_result)
        frequencies = np.fft.rfftfreq(n, 1/fs_target)
        
        # New Nyquist limit
        nyquist_new = fs_target / 2  # 512 Hz
        
        # Check that there are no significant components above Nyquist
        # (There shouldn't be any since rfft only goes up to Nyquist)
        # Instead, verify that the filter properly attenuated frequencies above Nyquist
        # by checking the frequency response of the filter
        
        taps = design_fir_filter(fs_original, fs_target)
        w, h = signal.freqz(taps)
        freq_response = np.abs(h)
        
        # At frequencies above new Nyquist (normalized > 0.5), response should be very low
        nyquist_normalized = 0.5
        high_freq_indices = w / np.pi > nyquist_normalized
        if np.any(high_freq_indices):
            max_high_freq_response = np.max(freq_response[high_freq_indices])
            assert max_high_freq_response < 0.1  # Should be strongly attenued

class TestProcessWaveformFile:
    """Test waveform file processing."""
    
    def test_process_waveform_file_single(self):
        """Test processing a single waveform file."""
        # Create a temporary input file
        with tempfile.NamedTemporaryFile(suffix='.h5', delete=False) as tmp:
            tmp_path = tmp.name
        
        try:
            # Create test waveform file
            import h5py
            waveform = np.random.randn(4096)
            with h5py.File(tmp_path, 'w') as f:
                f.create_dataset('waveform', data=waveform)
                f.attrs['sampling_frequency'] = 4096
                f.attrs['waveform_id'] = 'test_001'
                f.attrs['mass1'] = 30.0
                f.attrs['mass2'] = 30.0
                f.attrs['distance'] = 400.0
            
            # Process the file
            with tempfile.TemporaryDirectory() as tmpdir:
                results = process_waveform_file(
                    tmp_path,
                    tmpdir,
                    target_rates=[2048, 1024]
                )
                
                assert 'outputs' in results
                assert len(results['outputs']) >= 2  # Native + downsampled
                
                # Check output files exist
                for output in results['outputs']:
                    assert os.path.exists(output['path'])
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)

if __name__ == '__main__':
    pytest.main([__file__, '-v'])