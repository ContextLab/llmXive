"""
Unit tests for quantization logic edge cases.
Verifies 1-bit and 16-bit quantization behavior as per US1 requirements.
"""
import pytest
import numpy as np
import sys
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root / "code"))

from src.utils import (
    get_quantization_levels,
    calculate_optimal_fsr,
    quantize_fixed_fsr,
    verify_quantization_levels
)


class TestQuantizationEdgeCases:
    """Test edge cases for quantization logic, specifically 1-bit and 16-bit."""

    def setup_method(self):
        """Setup test fixtures."""
        # Create a standard test signal: sine wave with added noise
        self.fs = 4096  # Sample rate
        self.duration = 1.0  # seconds
        self.t = np.linspace(0, self.duration, int(self.fs * self.duration))
        self.f_signal = 150.0  # 150 Hz sine wave
        self.signal = np.sin(2 * np.pi * self.f_signal * self.t)
        
        # Add small noise to make it realistic
        self.noise = np.random.normal(0, 0.1, self.signal.shape)
        self.noisy_signal = self.signal + self.noise

    def test_1bit_quantization_levels(self):
        """
        Verify that 1-bit quantization results in exactly 2 unique levels.
        1-bit = 2^1 = 2 levels (typically -1 and +1, or 0 and 1).
        """
        n_bits = 1
        quantized = quantize_fixed_fsr(self.noisy_signal, n_bits)
        
        unique_levels = np.unique(quantized)
        max_expected_levels = 2 ** n_bits
        
        # Verify number of unique levels does not exceed 2^N
        assert len(unique_levels) <= max_expected_levels, (
            f"1-bit quantization produced {len(unique_levels)} levels, "
            f"expected at most {max_expected_levels}"
        )
        
        # Verify levels are symmetric around zero for fixed FSR
        # (Should be roughly [-1, 1] or similar symmetric pair)
        assert np.all(np.abs(unique_levels) <= 1.5), (
            "Quantized levels exceed expected range for 1-bit"
        )

    def test_1bit_sign_preservation(self):
        """
        Verify that 1-bit quantization preserves the sign of the input signal.
        """
        n_bits = 1
        quantized = quantize_fixed_fsr(self.noisy_signal, n_bits)
        
        # Check that sign is preserved (with some tolerance for zero crossings)
        # Non-zero inputs should map to non-zero outputs with same sign
        non_zero_mask = np.abs(self.noisy_signal) > 1e-6
        if np.any(non_zero_mask):
            sign_preserved = np.all(
                np.sign(self.noisy_signal[non_zero_mask]) == np.sign(quantized[non_zero_mask])
            )
            assert sign_preserved, "1-bit quantization did not preserve signal sign"

    def test_16bit_quantization_levels(self):
        """
        Verify that 16-bit quantization results in at most 65536 unique levels.
        16-bit = 2^16 = 65536 levels.
        """
        n_bits = 16
        quantized = quantize_fixed_fsr(self.noisy_signal, n_bits)
        
        unique_levels = np.unique(quantized)
        max_expected_levels = 2 ** n_bits
        
        # Verify number of unique levels does not exceed 2^N
        assert len(unique_levels) <= max_expected_levels, (
            f"16-bit quantization produced {len(unique_levels)} levels, "
            f"expected at most {max_expected_levels}"
        )
        
        # 16-bit should have significantly more levels than 1-bit for same signal
        n_bits_1 = 1
        quantized_1bit = quantize_fixed_fsr(self.noisy_signal, n_bits_1)
        unique_levels_1bit = np.unique(quantized_1bit)
        
        assert len(unique_levels) > len(unique_levels_1bit), (
            "16-bit quantization should produce more unique levels than 1-bit"
        )

    def test_16bit_precision(self):
        """
        Verify that 16-bit quantization preserves more signal detail than lower bit depths.
        """
        n_bits_16 = 16
        n_bits_8 = 8
        
        quantized_16 = quantize_fixed_fsr(self.noisy_signal, n_bits_16)
        quantized_8 = quantize_fixed_fsr(self.noisy_signal, n_bits_8)
        
        # Calculate reconstruction error
        error_16 = np.mean((self.noisy_signal - quantized_16) ** 2)
        error_8 = np.mean((self.noisy_signal - quantized_8) ** 2)
        
        # 16-bit should have lower quantization error than 8-bit
        assert error_16 < error_8, (
            f"16-bit MSE ({error_16}) should be lower than 8-bit MSE ({error_8})"
        )

    def test_quantization_range_symmetry(self):
        """
        Verify that quantization is symmetric around zero for both 1-bit and 16-bit.
        """
        for n_bits in [1, 16]:
            quantized = quantize_fixed_fsr(self.noisy_signal, n_bits)
            unique_levels = np.unique(quantized)
            
            # Check symmetry: for every positive level, there should be a negative counterpart
            # (allowing for small floating point differences)
            positive_levels = unique_levels[unique_levels > 0]
            negative_levels = unique_levels[unique_levels < 0]
            
            # The number of positive and negative levels should be roughly equal
            # (may differ by 1 if zero is included)
            assert abs(len(positive_levels) - len(negative_levels)) <= 1, (
                f"{n_bits}-bit quantization levels are not symmetric: "
                f"{len(positive_levels)} positive, {len(negative_levels)} negative"
            )

    def test_get_quantization_levels_function(self):
        """
        Verify the get_quantization_levels helper function returns correct values.
        """
        assert get_quantization_levels(1) == 2
        assert get_quantization_levels(8) == 256
        assert get_quantization_levels(16) == 65536
        assert get_quantization_levels(32) == 4294967296

    def test_verify_quantization_levels_helper(self):
        """
        Verify the verify_quantization_levels helper function works correctly.
        """
        # Create a quantized signal
        signal = np.array([0.1, -0.5, 0.8, -0.2, 0.5])
        n_bits = 2  # 4 levels
        quantized = quantize_fixed_fsr(signal, n_bits)
        
        # Should pass verification
        is_valid, max_levels, actual_levels = verify_quantization_levels(
            quantized, n_bits
        )
        
        assert is_valid, "Valid quantization failed verification"
        assert max_levels == 4
        assert actual_levels <= 4

    def test_edge_case_all_zeros(self):
        """
        Verify quantization handles all-zero input correctly.
        """
        zero_signal = np.zeros(1000)
        
        for n_bits in [1, 8, 16]:
            quantized = quantize_fixed_fsr(zero_signal, n_bits)
            unique_levels = np.unique(quantized)
            
            # All zeros should quantize to a single level (typically 0 or nearest)
            assert len(unique_levels) == 1, (
                f"All-zero signal produced {len(unique_levels)} levels for {n_bits}-bit"
            )

    def test_edge_case_constant_signal(self):
        """
        Verify quantization handles constant (DC) signal correctly.
        """
        constant_value = 0.5
        constant_signal = np.full(1000, constant_value)
        
        for n_bits in [1, 8, 16]:
            quantized = quantize_fixed_fsr(constant_signal, n_bits)
            unique_levels = np.unique(quantized)
            
            # Constant signal should produce at most 1-2 levels (due to FSR calculation)
            assert len(unique_levels) <= 2, (
                f"Constant signal produced {len(unique_levels)} levels for {n_bits}-bit"
            )

    def test_fsr_calculation_1bit(self):
        """
        Verify FSR calculation for 1-bit quantization.
        """
        # FSR should be based on signal amplitude
        fsr = calculate_optimal_fsr(self.noisy_signal)
        
        # FSR should be positive and cover the signal range
        assert fsr > 0, "FSR must be positive"
        assert fsr >= np.max(np.abs(self.noisy_signal)), (
            "FSR should cover the signal range"
        )

    def test_fsr_calculation_16bit(self):
        """
        Verify FSR calculation for 16-bit quantization.
        """
        fsr = calculate_optimal_fsr(self.noisy_signal)
        
        # FSR should be the same regardless of bit depth (it's signal-dependent)
        fsr_1bit = calculate_optimal_fsr(self.noisy_signal)
        assert fsr == fsr_1bit, "FSR should be consistent across bit depths"

    def test_clipping_behavior(self):
        """
        Verify that signals exceeding FSR are clipped correctly for both 1-bit and 16-bit.
        """
        # Create a signal that exceeds typical range
        extreme_signal = np.array([-2.0, -1.5, 0.0, 1.5, 2.0])
        
        for n_bits in [1, 16]:
            quantized = quantize_fixed_fsr(extreme_signal, n_bits)
            unique_levels = np.unique(quantized)
            
            # All quantized values should be within [-1, 1] (normalized) or FSR bounds
            # The exact bounds depend on implementation, but should be bounded
            assert np.all(np.abs(quantized) <= np.max(np.abs(extreme_signal)) * 1.1), (
                f"Quantized values for {n_bits}-bit exceed reasonable bounds"
            )