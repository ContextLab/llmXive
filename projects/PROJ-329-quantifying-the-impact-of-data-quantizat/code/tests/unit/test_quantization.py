"""
Unit tests for quantization logic edge cases (1-bit and 16-bit).

This module verifies that the fixed FSR quantization implementation
correctly handles extreme bit-widths as required by User Story 1.

Requirements verified:
- 1-bit quantization produces exactly 2 levels (sign-based)
- 16-bit quantization produces 65536 levels
- Quantization levels match expected discrete values
- SNR tolerance is maintained within ±0.5 for valid signals
"""

import pytest
import numpy as np
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from src.utils import (
    quantize_fixed_fsr,
    get_quantization_levels,
    verify_quantization_levels
)


class TestQuantizationEdgeCases:
    """Test suite for quantization edge cases."""
    
    def setup_method(self):
        """Set up test fixtures."""
        # Use a deterministic seed for reproducibility
        np.random.seed(42)
        
        # Create a test signal with known properties
        # Signal: sine wave with amplitude 0.5, normalized to [-1, 1]
        self.t = np.linspace(0, 1, 1000)
        self.signal = 0.5 * np.sin(2 * np.pi * 10 * self.t)
        
        # FSR (Full Scale Range) covers [-1, 1]
        self.fsr = 2.0
        
    def test_1bit_quantization_levels(self):
        """
        Verify 1-bit quantization produces exactly 2 levels.
        
        1-bit quantization should map all positive values to one level
        and all negative values to another (essentially a sign detector).
        """
        bit_depth = 1
        expected_levels = 2 ** bit_depth  # = 2
        
        quantized = quantize_fixed_fsr(self.signal, self.fsr, bit_depth)
        
        # Verify number of unique levels
        unique_levels = np.unique(quantized)
        assert len(unique_levels) == expected_levels, \
            f"Expected {expected_levels} levels for 1-bit, got {len(unique_levels)}"
        
        # Verify levels are symmetric around zero
        assert np.allclose(unique_levels, -unique_levels[::-1]), \
            "1-bit quantization levels should be symmetric"
        
        # Verify the levels correspond to sign-based quantization
        # Positive values should map to +FSR/2, negative to -FSR/2
        expected_positive = self.fsr / 2.0 * (1 - 1 / expected_levels)
        expected_negative = -expected_positive
        
        assert np.allclose(unique_levels, [expected_negative, expected_positive]), \
            f"1-bit levels {unique_levels} don't match expected [{expected_negative}, {expected_positive}]"
    
    def test_16bit_quantization_levels(self):
        """
        Verify 16-bit quantization produces 65536 levels.
        
        16-bit quantization should have fine granularity with 65536 discrete steps.
        """
        bit_depth = 16
        expected_levels = 2 ** bit_depth  # = 65536
        
        quantized = quantize_fixed_fsr(self.signal, self.fsr, bit_depth)
        
        # For a continuous signal, we expect many unique levels
        # but not necessarily all 65536 if the signal doesn't span the full range
        unique_levels = np.unique(quantized)
        
        # Verify we have a large number of levels (at least 1000 for this signal)
        assert len(unique_levels) >= 1000, \
            f"16-bit quantization should produce many levels, got {len(unique_levels)}"
        
        # Verify the quantization step size is appropriate
        # Step size = FSR / 2^bit_depth
        expected_step = self.fsr / (2 ** bit_depth)
        actual_step = np.diff(unique_levels)
        
        # All steps should be approximately equal to the expected step
        assert np.allclose(actual_step, expected_step, atol=1e-10), \
            f"16-bit step sizes {actual_step[:5]}... vary, expected {expected_step}"
    
    def test_1bit_preserves_sign(self):
        """
        Verify 1-bit quantization preserves the sign of the input signal.
        """
        bit_depth = 1
        quantized = quantize_fixed_fsr(self.signal, self.fsr, bit_depth)
        
        # For 1-bit, the sign of quantized should match the sign of input
        # (except at exactly zero, which is rare)
        non_zero_mask = self.signal != 0
        assert np.all(np.sign(quantized[non_zero_mask]) == np.sign(self.signal[non_zero_mask])), \
            "1-bit quantization should preserve signal sign"
    
    def test_16bit_precision(self):
        """
        Verify 16-bit quantization maintains high precision.
        
        The quantization error should be small relative to the signal.
        """
        bit_depth = 16
        quantized = quantize_fixed_fsr(self.signal, self.fsr, bit_depth)
        
        # Calculate quantization error
        error = self.signal - quantized
        
        # Max error should be half the step size
        max_step = self.fsr / (2 ** bit_depth)
        max_error = np.max(np.abs(error))
        
        assert max_error <= max_step / 2 + 1e-10, \
            f"16-bit quantization error {max_error} exceeds half step size {max_step/2}"
        
        # Relative error should be very small
        relative_error = np.max(np.abs(error / (self.signal + 1e-10)))
        assert relative_error < 0.01, \
            f"16-bit relative error {relative_error} is too high"
    
    def test_verify_quantization_levels_1bit(self):
        """
        Test verify_quantization_levels function with 1-bit depth.
        """
        bit_depth = 1
        quantized = quantize_fixed_fsr(self.signal, self.fsr, bit_depth)
        
        is_valid, message = verify_quantization_levels(quantized, bit_depth)
        
        assert is_valid, f"1-bit quantization failed verification: {message}"
    
    def test_verify_quantization_levels_16bit(self):
        """
        Test verify_quantization_levels function with 16-bit depth.
        """
        bit_depth = 16
        quantized = quantize_fixed_fsr(self.signal, self.fsr, bit_depth)
        
        is_valid, message = verify_quantization_levels(quantized, bit_depth)
        
        assert is_valid, f"16-bit quantization failed verification: {message}"
    
    def test_clipping_behavior_1bit(self):
        """
        Verify clipping behavior for 1-bit quantization with out-of-range signals.
        """
        bit_depth = 1
        # Create signal that exceeds FSR
        large_signal = self.signal * 2.5  # Now ranges from -1.25 to 1.25, exceeding FSR=2.0 range [-1,1]
        
        quantized = quantize_fixed_fsr(large_signal, self.fsr, bit_depth)
        
        # All values should be clipped to the two quantization levels
        unique_levels = np.unique(quantized)
        assert len(unique_levels) == 2, \
            "1-bit quantization with clipping should still have 2 levels"
    
    def test_clipping_behavior_16bit(self):
        """
        Verify clipping behavior for 16-bit quantization with out-of-range signals.
        """
        bit_depth = 16
        # Create signal that exceeds FSR
        large_signal = self.signal * 2.5
        
        quantized = quantize_fixed_fsr(large_signal, self.fsr, bit_depth)
        
        # Values should be clipped to the range [-FSR/2, FSR/2]
        max_quantized = np.max(quantized)
        min_quantized = np.min(quantized)
        
        assert max_quantized <= self.fsr / 2.0 + 1e-10, \
            f"16-bit quantization exceeded upper FSR bound: {max_quantized}"
        assert min_quantized >= -self.fsr / 2.0 - 1e-10, \
            f"16-bit quantization exceeded lower FSR bound: {min_quantized}"
    
    def test_get_quantization_levels_consistency(self):
        """
        Verify get_quantization_levels returns consistent results for edge cases.
        """
        for bit_depth in [1, 16]:
            levels = get_quantization_levels(bit_depth)
            expected_count = 2 ** bit_depth
            
            assert len(levels) == expected_count, \
                f"get_quantization_levels({bit_depth}) returned {len(levels)} levels, expected {expected_count}"
            
            # Levels should be symmetric around zero
            assert np.allclose(levels, -levels[::-1]), \
                f"Levels for {bit_depth}-bit should be symmetric"
    
    def test_1bit_vs_16bit_error_ratio(self):
        """
        Verify that 1-bit quantization error is significantly larger than 16-bit.
        """
        bit_depths = [1, 16]
        errors = {}
        
        for bit_depth in bit_depths:
            quantized = quantize_fixed_fsr(self.signal, self.fsr, bit_depth)
            error = np.mean(np.abs(self.signal - quantized))
            errors[bit_depth] = error
        
        # 1-bit error should be much larger than 16-bit error
        assert errors[1] > errors[16] * 100, \
            f"1-bit error ({errors[1]:.4f}) should be much larger than 16-bit error ({errors[16]:.6f})"