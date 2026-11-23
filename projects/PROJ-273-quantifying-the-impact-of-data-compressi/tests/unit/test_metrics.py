import pytest
import numpy as np
import os
import sys
from pathlib import Path

# Ensure src is in path for imports if running via pytest
if "code" not in sys.path:
    code_root = Path(__file__).parent.parent.parent / "code"
    if code_root.exists():
        sys.path.insert(0, str(code_root))

from src.compression.metrics import calculate_snr_degradation, calculate_mse


class TestSNRDegradation:
    """Unit tests for SNR degradation calculation in lossy compression."""

    def test_snr_degradation_positive_for_lossy(self):
        """Test that lossy compression results in positive SNR degradation."""
        # Create a realistic signal (sinusoid + noise)
        fs = 4096
        duration = 1.0
        t = np.linspace(0, duration, int(fs * duration))
        frequency = 100.0
        
        # Original signal: sinusoid
        original_signal = np.sin(2 * np.pi * frequency * t)
        
        # Simulate lossy compression by adding quantization noise
        # Quantization noise typically reduces SNR
        bit_depth = 8
        max_val = 1.0
        levels = 2 ** bit_depth
        step_size = (2 * max_val) / levels
        
        # Quantize
        quantized_signal = np.round(original_signal / step_size) * step_size
        
        # Add small noise to simulate compression artifacts
        noise = np.random.normal(0, step_size / 10, size=quantized_signal.shape)
        compressed_signal = quantized_signal + noise
        
        # Calculate SNR degradation
        snr_degradation = calculate_snr_degradation(original_signal, compressed_signal)
        
        # SNR degradation should be positive (lossy compression reduces quality)
        assert snr_degradation > 0, f"Expected positive SNR degradation, got {snr_degradation}"

    def test_snr_degradation_zero_for_lossless(self):
        """Test that lossless compression results in zero SNR degradation."""
        # Create a signal
        original_signal = np.random.normal(0, 1, 1000)
        
        # Lossless compression/decompression should preserve signal exactly
        # For this test, we simulate it by using the same signal
        reconstructed_signal = original_signal.copy()
        
        snr_degradation = calculate_snr_degradation(original_signal, reconstructed_signal)
        
        # Should be very close to zero (floating point precision)
        assert np.isclose(snr_degradation, 0.0, atol=1e-10), \
            f"Expected ~0 SNR degradation for lossless, got {snr_degradation}"

    def test_snr_degradation_high_for_severe_compression(self):
        """Test that severe compression results in high SNR degradation."""
        # Create a high-quality signal
        fs = 4096
        t = np.linspace(0, 1, fs)
        original_signal = np.sin(2 * np.pi * 100 * t) + 0.5 * np.sin(2 * np.pi * 200 * t)
        
        # Severe quantization (very low bit depth)
        bit_depth = 2  # Only 4 levels
        max_val = np.max(np.abs(original_signal))
        levels = 2 ** bit_depth
        step_size = (2 * max_val) / levels
        
        # Quantize severely
        quantized_signal = np.round(original_signal / step_size) * step_size
        
        snr_degradation = calculate_snr_degradation(original_signal, quantized_signal)
        
        # Severe compression should result in significant SNR degradation
        assert snr_degradation > 5.0, \
            f"Expected high SNR degradation (>5dB) for severe compression, got {snr_degradation}"

    def test_snr_degradation_handles_different_signal_lengths(self):
        """Test that SNR calculation handles signals of different lengths gracefully."""
        # This test ensures the function doesn't crash with mismatched lengths
        # In practice, signals should be the same length, but we test robustness
        original_signal = np.random.normal(0, 1, 1000)
        compressed_signal = original_signal[:500]  # Truncated
        
        # Should handle this case (might return NaN or raise, but shouldn't crash unexpectedly)
        # For this test, we expect it to handle it gracefully
        try:
            snr_degradation = calculate_snr_degradation(original_signal, compressed_signal)
            # If it returns a value, it should be a float
            assert isinstance(snr_degradation, (int, float, np.floating)), \
                f"Expected numeric SNR degradation, got {type(snr_degradation)}"
        except Exception as e:
            # If it raises, that's also acceptable as long as it's a clear error
            assert isinstance(e, (ValueError, IndexError)), \
                f"Unexpected exception type: {type(e)}"

    def test_snr_degradation_with_realistic_gw_signal(self):
        """Test SNR degradation with a realistic gravitational wave-like signal."""
        # Create a chirp-like signal (simplified)
        fs = 4096
        duration = 2.0
        t = np.linspace(0, duration, int(fs * duration))
        
        # Frequency increases over time (chirp)
        f0 = 30.0
        f1 = 200.0
        k = (f1 - f0) / duration
        frequency = f0 + k * t
        
        # Amplitude increases as frequency increases (simplified inspiral)
        amplitude = 1.0 + 0.5 * (t / duration)
        
        original_signal = amplitude * np.sin(2 * np.pi * np.cumsum(frequency) / fs)
        
        # Add realistic noise
        noise = np.random.normal(0, 0.1, size=original_signal.shape)
        noisy_original = original_signal + noise
        
        # Compress with moderate loss (simulating wavelet thresholding)
        # Apply a simple thresholding operation
        threshold = 0.3
        compressed_signal = np.where(np.abs(noisy_original) < threshold, 0, noisy_original)
        
        snr_degradation = calculate_snr_degradation(noisy_original, compressed_signal)
        
        # Should have positive SNR degradation due to information loss
        assert snr_degradation > 0, \
            f"Expected positive SNR degradation for GW-like signal, got {snr_degradation}"
        
        # Should be reasonable (not infinite or extremely large)
        assert snr_degradation < 100, \
            f"Expected reasonable SNR degradation (<100dB), got {snr_degradation}"


class TestMSE:
    """Unit tests for Mean Squared Error calculation."""

    def test_mse_zero_for_identical_signals(self):
        """Test that MSE is zero for identical signals."""
        signal = np.random.normal(0, 1, 1000)
        mse = calculate_mse(signal, signal)
        assert mse == 0.0, f"Expected MSE=0 for identical signals, got {mse}"

    def test_mse_positive_for_different_signals(self):
        """Test that MSE is positive for different signals."""
        signal1 = np.random.normal(0, 1, 1000)
        signal2 = signal1 + np.random.normal(0, 0.5, 1000)
        mse = calculate_mse(signal1, signal2)
        assert mse > 0, f"Expected positive MSE, got {mse}"

    def test_mse_scales_with_difference(self):
        """Test that MSE scales with the magnitude of difference."""
        base_signal = np.random.normal(0, 1, 1000)
        
        # Small difference
        small_diff = base_signal + np.random.normal(0, 0.1, 1000)
        mse_small = calculate_mse(base_signal, small_diff)
        
        # Large difference
        large_diff = base_signal + np.random.normal(0, 1.0, 1000)
        mse_large = calculate_mse(base_signal, large_diff)
        
        assert mse_large > mse_small, \
            f"Expected larger MSE for larger differences: {mse_large} > {mse_small}"

def test_constants_defined():
    """Test that required constants are defined in the metrics module."""
    # This test ensures the module exports expected interfaces
    assert hasattr(sys.modules.get('src.compression.metrics', None), 'calculate_snr_degradation'), \
        "calculate_snr_degradation function should be defined"
    assert hasattr(sys.modules.get('src.compression.metrics', None), 'calculate_mse'), \
        "calculate_mse function should be defined"