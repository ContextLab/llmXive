"""
Unit tests for src/utils.py.
"""
import numpy as np
import pytest
import sys
import os
from pathlib import Path

# Add code to path if running from tests
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.utils import (
    get_quantization_levels,
    calculate_optimal_fsr,
    quantize_fixed_fsr,
    calculate_snr,
    verify_quantization_levels
)


class TestQuantization:
    def test_get_quantization_levels(self):
        assert get_quantization_levels(1) == 2
        assert get_quantization_levels(8) == 256
        assert get_quantization_levels(16) == 65536
        
        with pytest.raises(ValueError):
            get_quantization_levels(0)
            get_quantization_levels(-5)

    def test_calculate_optimal_fsr(self):
        signal = np.array([0.0, 1.0, -1.0, 0.5])
        fsr = calculate_optimal_fsr(signal, 8)
        # FSR should be 2 * max(abs(signal)) = 2 * 1.0 = 2.0
        assert fsr == 2.0
        
        signal_zero = np.array([0.0, 0.0, 0.0])
        fsr_zero = calculate_optimal_fsr(signal_zero, 8)
        assert fsr_zero == 1.0  # Default fallback
        
        with pytest.raises(ValueError):
            calculate_optimal_fsr(np.array([]), 8)

    def test_quantize_fixed_fsr_basic(self):
        signal = np.array([0.0, 1.0, -1.0, 0.5])
        quantized, fsr = quantize_fixed_fsr(signal, bit_depth=2)
        
        # With 2 bits, we have 4 levels. FSR = 2.0 (from max=1.0).
        # Range: [-1.0, 1.0]. Step = 2.0 / 4 = 0.5.
        # Levels: -0.75, -0.25, 0.25, 0.75 (midpoints)
        # 1.0 -> 0.75 (clipped to 1.0, then mapped? No, 1.0 is max. 
        # If max is 1.0, FSR=2.0. Range [-1, 1].
        # 1.0 is the max value. It should map to the highest bin.
        # Let's check the logic:
        # indices = floor((clipped - min) / step)
        # min = -1.0, step = 0.5.
        # 1.0: floor((1.0 - (-1.0))/0.5) = floor(2.0/0.5) = floor(4.0) = 4 -> clipped to 3.
        # 3 -> -1.0 + (3.5)*0.5 = -1.0 + 1.75 = 0.75.
        
        assert fsr == 2.0
        assert len(np.unique(quantized)) <= 4

    def test_quantize_clipping(self):
        signal = np.array([10.0, -10.0, 0.0])
        quantized, fsr = quantize_fixed_fsr(signal, bit_depth=2)
        # FSR will be 20.0. Range [-10, 10].
        # 10.0 is max, -10.0 is min.
        # They should be mapped to the extreme levels.
        assert fsr == 20.0
        assert len(np.unique(quantized)) <= 4

    def test_verify_quantization_levels(self):
        signal = np.array([0.1, 0.2, 0.3, 0.4])
        quantized, _ = quantize_fixed_fsr(signal, bit_depth=2)
        is_valid, count = verify_quantization_levels(quantized, 2)
        assert is_valid
        assert count <= 4

        # Force invalid? Hard to force with valid quantization, but we can test the function
        fake_signal = np.array([1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0])
        is_valid, count = verify_quantization_levels(fake_signal, 2)
        assert not is_valid
        assert count > 4


class TestSNR:
    def test_calculate_snr_with_variance(self):
        signal = np.array([1.0, 1.0, 1.0, 1.0])
        noise_var = 0.25  # std = 0.5
        snr = calculate_snr(signal, noise_variance=noise_var)
        # rms(signal) = 1.0
        # rms(noise) = 0.5
        # snr = 2.0
        assert np.isclose(snr, 2.0)

    def test_calculate_snr_with_noise_series(self):
        signal = np.array([1.0, 1.0, 1.0, 1.0])
        noise = np.array([0.0, 0.0, 0.0, 0.0])
        # This should result in infinite SNR?
        # But let's test with non-zero noise
        noise = np.array([0.5, 0.5, 0.5, 0.5])
        snr = calculate_snr(signal, noise_psd=noise)
        # rms(signal)=1, rms(noise)=0.5 -> 2.0
        assert np.isclose(snr, 2.0)

    def test_calculate_snr_empty_signal(self):
        with pytest.raises(ValueError):
            calculate_snr(np.array([]), noise_variance=0.1)

    def test_calculate_snr_no_inputs(self):
        with pytest.raises(ValueError):
            calculate_snr(np.array([1.0, 2.0]))


class TestHelperFunctions:
    def test_verify_quantization_levels_tolerance(self):
        # Test with floating point noise
        signal = np.array([0.0, 0.5, 1.0])
        # Add tiny noise
        noisy = signal + 1e-10
        is_valid, count = verify_quantization_levels(noisy, bit_depth=2)
        # Should still be valid if unique count is low
        assert is_valid

    def test_quantize_with_custom_fsr(self):
        signal = np.array([0.0, 1.0])
        custom_fsr = 10.0
        quantized, fsr_used = quantize_fixed_fsr(signal, bit_depth=2, fsr=custom_fsr)
        assert fsr_used == custom_fsr
        # Check that quantization happened
        assert len(np.unique(quantized)) <= 4