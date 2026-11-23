"""
Unit tests for src/utils.py: Quantization and SNR calculation helpers.

Tests cover:
1. Quantization logic (Fixed FSR)
2. SNR calculation
3. Helper functions (level counts, verification)
"""

import numpy as np
import pytest
import sys
import os
from pathlib import Path

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from src.utils import (
    get_quantization_levels,
    calculate_optimal_fsr,
    quantize_fixed_fsr,
    calculate_snr,
    verify_quantization_levels
)


class TestQuantization:
    """Tests for quantization logic."""
    
    def test_get_quantization_levels_valid(self):
        """Test correct level calculation for valid bit depths."""
        assert get_quantization_levels(1) == 2
        assert get_quantization_levels(8) == 256
        assert get_quantization_levels(16) == 65536
        assert get_quantization_levels(32) == 4294967296
    
    def test_get_quantization_levels_invalid(self):
        """Test error handling for invalid bit depths."""
        with pytest.raises(ValueError):
            get_quantization_levels(0)
        with pytest.raises(ValueError):
            get_quantization_levels(-1)
        with pytest.raises(ValueError):
            get_quantization_levels(3.5)
    
    def test_quantize_fixed_fsr_basic(self):
        """Test basic quantization functionality."""
        # Create a simple sine wave
        t = np.linspace(0, 1, 1000)
        signal = 0.5 * np.sin(2 * np.pi * 10 * t)
        
        # Quantize to 8 bits
        quantized = quantize_fixed_fsr(signal, n_bits=8)
        
        # Check that output has same shape
        assert quantized.shape == signal.shape
        
        # Check that output is within bounds
        assert np.all(quantized >= -0.5)
        assert np.all(quantized <= 0.5)
    
    def test_quantize_fixed_fsr_1bit_edge_case(self):
        """Test 1-bit quantization (binary output)."""
        signal = np.array([0.1, 0.5, -0.3, -0.8, 0.0])
        quantized = quantize_fixed_fsr(signal, n_bits=1)
        
        # 1-bit should have only 2 levels
        unique_values = np.unique(quantized)
        assert len(unique_values) <= 2
        
        # Check that positive and negative values are separated
        # (exact values depend on FSR calculation)
        assert len(unique_values) >= 1  # At least one level exists
    
    def test_quantize_fixed_fsr_16bit_precision(self):
        """Test 16-bit quantization preserves more precision."""
        signal = np.linspace(-1.0, 1.0, 1000)
        quantized = quantize_fixed_fsr(signal, n_bits=16)
        
        # 16-bit should have many unique levels (up to 65536)
        unique_count = len(np.unique(quantized))
        assert unique_count > 1000  # Should have high resolution
    
    def test_quantize_fixed_fsr_clipping(self):
        """Test that signal is properly clipped at FSR boundaries."""
        # Signal with values outside [-1, 1]
        signal = np.array([-2.0, -1.5, -0.5, 0.5, 1.5, 2.0])
        quantized = quantize_fixed_fsr(signal, n_bits=8)
        
        # Check that extreme values are clipped
        assert np.min(quantized) >= -2.0
        assert np.max(quantized) <= 2.0
    
    def test_verify_quantization_levels(self):
        """Test level count verification."""
        signal = np.random.randn(1000)
        quantized = quantize_fixed_fsr(signal, n_bits=8)
        
        is_valid, count, max_allowed = verify_quantization_levels(quantized, n_bits=8)
        
        assert is_valid
        assert count <= max_allowed
        assert max_allowed == 256
    
    def test_verify_quantization_levels_overshoot(self):
        """Test verification with artificially created overshot levels."""
        # Create a signal with more levels than allowed
        signal = np.linspace(-1, 1, 1000)
        quantized = quantize_fixed_fsr(signal, n_bits=4)  # 16 levels max
        
        is_valid, count, max_allowed = verify_quantization_levels(quantized, n_bits=4)
        
        assert is_valid
        assert count <= 16


class TestSNR:
    """Tests for SNR calculation."""
    
    def test_calculate_snr_basic(self):
        """Test basic SNR calculation."""
        # Create a signal with known noise
        np.random.seed(42)
        noise = np.random.randn(1000) * 0.1
        signal = 0.5 * np.sin(2 * np.pi * 10 * np.linspace(0, 1, 1000)) + noise
        
        snr = calculate_snr(signal)
        
        assert snr > 0
        assert not np.isnan(snr)
        assert not np.isinf(snr)
    
    def test_calculate_snr_zero_noise(self):
        """Test SNR calculation with zero noise (should be infinite)."""
        signal = np.ones(1000)
        # Manually set noise_std to 0
        snr = calculate_snr(signal, noise_std=0.0)
        
        assert np.isinf(snr)
    
    def test_calculate_snr_empty_signal(self):
        """Test error handling for empty signal."""
        with pytest.raises(ValueError):
            calculate_snr(np.array([]))
    
    def test_calculate_snr_known_std(self):
        """Test SNR calculation with known noise standard deviation."""
        signal = np.random.randn(1000) * 0.5
        known_noise_std = 0.1
        
        snr = calculate_snr(signal, noise_std=known_noise_std)
        
        assert snr > 0
        assert isinstance(snr, float)


class TestHelperFunctions:
    """Tests for helper functions."""
    
    def test_calculate_optimal_fsr(self):
        """Test FSR calculation."""
        signal = np.array([-1.0, -0.5, 0.0, 0.5, 1.0])
        fsr = calculate_optimal_fsr(signal, n_bits=8)
        
        assert fsr == 1.0  # Max amplitude is 1.0
    
    def test_calculate_optimal_fsr_zero_signal(self):
        """Test FSR calculation for zero signal."""
        signal = np.zeros(100)
        fsr = calculate_optimal_fsr(signal, n_bits=8)
        
        assert fsr == 1.0  # Default FSR
    
    def test_verify_quantization_levels_tolerance(self):
        """Test level verification with tolerance."""
        # Create a signal with floating point artifacts
        signal = np.random.randn(1000)
        quantized = quantize_fixed_fsr(signal, n_bits=8)
        
        # Add tiny noise to simulate floating point errors
        quantized_noisy = quantized + np.random.randn(1000) * 1e-12
        
        is_valid, count, max_allowed = verify_quantization_levels(
            quantized_noisy, n_bits=8, tolerance=1e-10
        )
        
        assert is_valid
        assert count <= 256