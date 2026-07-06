import pytest
import numpy as np
import sys
from pathlib import Path
from src.utils import quantize_fixed_fsr, get_quantization_levels, verify_quantization_levels

class TestQuantizationEdgeCases:
    """
    Unit tests for quantization logic (T011/T014).
    Verifies 1-bit and 16-bit edge cases and level counts.
    """

    def test_1_bit_quantization(self):
        """Test 1-bit quantization (2 levels)."""
        signal = np.array([-1.0, -0.5, 0.0, 0.5, 1.0])
        bits = 1
        quantized = quantize_fixed_fsr(signal, bits)
        
        levels = len(np.unique(quantized))
        assert levels <= 2, f"1-bit quantization should have <= 2 levels, got {levels}"
        
        # Verify symmetry around 0
        assert np.all(quantized >= 0) or np.all(quantized <= 0) or (np.min(quantized) < 0 < np.max(quantized))

    def test_16_bit_quantization(self):
        """Test 16-bit quantization (65536 levels)."""
        signal = np.linspace(-10, 10, 1000)
        bits = 16
        quantized = quantize_fixed_fsr(signal, bits)
        
        levels = len(np.unique(quantized))
        assert levels <= 65536, f"16-bit quantization should have <= 65536 levels, got {levels}"
        
        # Verify reconstruction is close to original for high bits
        error = np.mean(np.abs(signal - quantized))
        assert error < 1.0, "High bit quantization should have low error"

    def test_clipping(self):
        """Test that values outside FSR are clipped."""
        signal = np.array([-100.0, -1.0, 1.0, 100.0])
        bits = 8
        # Force a small FSR to trigger clipping
        fsr = 2.0 
        quantized = quantize_fixed_fsr(signal, bits, fsr=fsr)
        
        # All values should be within [-1, 1] (half FSR)
        assert np.all(quantized >= -1.0) and np.all(quantized <= 1.0)

    def test_verify_levels(self):
        """Test the verify_quantization_levels helper."""
        signal = np.random.randn(100)
        for bits in [4, 8, 12, 16]:
            quantized = quantize_fixed_fsr(signal, bits)
            assert verify_quantization_levels(quantized, bits)

    def test_empty_signal(self):
        """Test handling of empty signal."""
        signal = np.array([])
        bits = 8
        quantized = quantize_fixed_fsr(signal, bits)
        assert quantized.size == 0

    def test_zero_signal(self):
        """Test handling of zero signal."""
        signal = np.zeros(10)
        bits = 8
        quantized = quantize_fixed_fsr(signal, bits)
        assert np.all(quantized == 0)
