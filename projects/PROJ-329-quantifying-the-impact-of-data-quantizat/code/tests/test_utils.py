"""
Tests for src/utils.py quantization and SNR utilities.
"""
import numpy as np
import pytest
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.utils import (
    quantize_fixed_fsr,
    calculate_snr,
    calculate_optimal_fsr,
    get_quantization_levels,
    verify_quantization_levels
)


class TestQuantization:
    """Tests for Fixed FSR quantization logic."""
    
    def test_quantize_basic(self):
        """Test basic quantization with known values."""
        signal = np.array([0.0, 0.5, 1.0, -0.5, -1.0])
        n_bits = 2
        
        quantized = quantize_fixed_fsr(signal, n_bits)
        
        # With 2 bits, we have 4 levels: -1, -0.33, 0.33, 1 (approx)
        # Actually for symmetric 2-bit: levels at -1, -1/3, 1/3, 1
        assert len(quantized) == len(signal)
        assert np.all(np.abs(quantized) <= 1.0)
    
    def test_quantize_1bit(self):
        """Test 1-bit quantization (binary)."""
        signal = np.array([0.5, -0.5, 0.1, -0.1])
        quantized = quantize_fixed_fsr(signal, n_bits=1)
        
        # 1-bit should give 2 levels: -1 and 1 (or similar)
        unique = np.unique(quantized)
        assert len(unique) <= 2
        assert np.all(np.abs(quantized) > 0)
    
    def test_quantize_16bit(self):
        """Test 16-bit quantization preserves precision."""
        signal = np.linspace(-1, 1, 1000)
        quantized = quantize_fixed_fsr(signal, n_bits=16)
        
        # 16-bit should have many levels
        unique_count = len(np.unique(np.round(quantized, decimals=6)))
        expected_levels = get_quantization_levels(16)
        assert unique_count > 100  # Should have many distinct levels
        assert unique_count <= expected_levels
    
    def test_quantize_clipping(self):
        """Test that values outside FSR are clipped."""
        signal = np.array([2.0, -2.0, 0.5])
        # Default FSR will be inferred from max(|signal|) = 2.0
        # So 2.0 and -2.0 should be at the boundaries
        quantized = quantize_fixed_fsr(signal, n_bits=4)
        
        # Max and min should be at boundaries
        assert np.max(quantized) <= 1.0
        assert np.min(quantized) >= -1.0
    
    def test_quantize_custom_fsr(self):
        """Test quantization with custom FSR."""
        signal = np.array([0.1, 0.2, 0.3])
        fsr = 10.0  # Very large FSR
        quantized = quantize_fixed_fsr(signal, n_bits=4, fsr=fsr)
        
        # With large FSR, quantization steps are small
        # Values should be small relative to FSR
        assert np.all(np.abs(quantized) < 1.0)
    
    def test_quantize_invalid_bits(self):
        """Test that invalid bit depths raise errors."""
        signal = np.array([0.5])
        
        with pytest.raises(ValueError):
            quantize_fixed_fsr(signal, n_bits=0)
        
        with pytest.raises(ValueError):
            quantize_fixed_fsr(signal, n_bits=-1)


class TestSNR:
    """Tests for SNR calculation."""
    
    def test_snr_basic(self):
        """Test basic SNR calculation."""
        signal = np.ones(1000) * 0.1
        noise = np.random.randn(1000) * 0.01
        
        snr = calculate_snr(signal, noise)
        
        # SNR should be positive
        assert snr > 0
        # Signal is 10x noise amplitude, so SNR ~ 10
        assert 5 < snr < 20
    
    def test_snr_mismatched_lengths(self):
        """Test that mismatched lengths raise error."""
        signal = np.array([1.0, 2.0])
        noise = np.array([0.1])
        
        with pytest.raises(ValueError):
            calculate_snr(signal, noise)
    
    def test_snr_empty_signal(self):
        """Test that empty signal raises error."""
        signal = np.array([])
        noise = np.array([])
        
        with pytest.raises(ValueError):
            calculate_snr(signal, noise)
    
    def test_snr_zero_noise(self):
        """Test SNR with zero noise returns infinity."""
        signal = np.ones(100) * 0.1
        noise = np.zeros(100)
        
        snr = calculate_snr(signal, noise)
        assert np.isinf(snr)
    
    def test_snr_range_validation(self):
        """Test SNR calculation for expected range [8, 50]."""
        # Create signal with SNR ~ 10
        signal = np.ones(4096) * 0.1
        noise = np.random.randn(4096) * 0.01
        
        snr = calculate_snr(signal, noise)
        
        # Should be in reasonable range
        assert 5 < snr < 20


class TestHelperFunctions:
    """Tests for utility helper functions."""
    
    def test_get_quantization_levels(self):
        """Test level count calculation."""
        assert get_quantization_levels(1) == 2
        assert get_quantization_levels(2) == 4
        assert get_quantization_levels(8) == 256
        assert get_quantization_levels(16) == 65536
        
        with pytest.raises(ValueError):
            get_quantization_levels(0)
    
    def test_calculate_optimal_fsr(self):
        """Test optimal FSR calculation."""
        signal = np.array([0.1, 0.2, 0.3, -0.25])
        fsr = calculate_optimal_fsr(signal, n_bits=8)
        
        # Should be slightly larger than max amplitude
        assert fsr > 0.3
        assert fsr <= 0.33  # With 1.1 margin
    
    def test_verify_quantization_levels(self):
        """Test level verification."""
        signal = np.random.randn(1000)
        quantized = quantize_fixed_fsr(signal, n_bits=4)
        
        is_valid, count = verify_quantization_levels(quantized, n_bits=4)
        
        assert is_valid
        assert count <= 16  # 2^4
    
    def test_verify_quantization_levels_clipped(self):
        """Test verification with clipped signal (fewer levels)."""
        signal = np.array([0.0])  # All zeros
        quantized = quantize_fixed_fsr(signal, n_bits=8)
        
        is_valid, count = verify_quantization_levels(quantized, n_bits=8)
        
        # Should be valid even with fewer levels (due to clipping)
        assert is_valid
        assert count == 1  # Only one level (zero)