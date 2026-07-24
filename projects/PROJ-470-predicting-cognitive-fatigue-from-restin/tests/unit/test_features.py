import pytest
import numpy as np
import os
import sys
from pathlib import Path

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'code'))

from features import calculate_lzc, calculate_permutation_entropy

class TestLempezZivComplexity:
    """Unit tests for LZC calculation."""
    
    def test_lzc_white_noise(self):
        """Test LZC on white noise signal."""
        np.random.seed(42)
        signal = np.random.normal(0, 1, 1000)
        lzc_val = calculate_lzc(signal)
        
        # LZC should be a valid float and not NaN
        assert isinstance(lzc_val, float)
        assert not np.isnan(lzc_val)
        # White noise should have relatively high complexity
        assert lzc_val > 0.1
        
    def test_lzc_constant_signal(self):
        """Test LZC on constant signal (should be 0)."""
        signal = np.ones(1000)
        lzc_val = calculate_lzc(signal)
        assert lzc_val == 0.0
        
    def test_lzc_empty_signal(self):
        """Test LZC on empty signal."""
        signal = np.array([])
        lzc_val = calculate_lzc(signal)
        assert lzc_val == 0.0

class TestPermutationEntropy:
    """Unit tests for Permutation Entropy calculation."""
    
    def test_pe_white_noise(self):
        """Test PE on white noise signal with known parameters."""
        # Generate white noise as specified in task:
        # seed=42, amplitude normalized, 256 Hz, 120 seconds
        np.random.seed(42)
        duration = 120  # seconds
        sfreq = 256     # Hz
        n_samples = duration * sfreq
        signal = np.random.normal(0, 1, n_samples)
        
        # Normalize amplitude to unity (already done by normal distribution with std=1)
        signal = signal / np.max(np.abs(signal))
        
        embedding_dim = 3
        time_delay = 1
        
        pe_val = calculate_permutation_entropy(signal, embedding_dim, time_delay)
        
        # Assert output is a valid numeric float and not NaN
        assert isinstance(pe_val, float)
        assert not np.isnan(pe_val)
        # For white noise, PE should be relatively high (close to 1.0 for normalized)
        # but not exactly 1.0 due to finite sample size
        assert pe_val > 0.5
        
    def test_pe_constant_signal(self):
        """Test PE on constant signal (should be 0)."""
        signal = np.ones(1000)
        pe_val = calculate_permutation_entropy(signal, embedding_dim=3, time_delay=1)
        assert pe_val == 0.0
        
    def test_pe_small_signal(self):
        """Test PE on very short signal."""
        signal = np.array([1.0, 2.0, 3.0])
        # With embedding_dim=3, we need at least 3 + (3-1)*1 = 5 samples
        # So this should return 0 or handle gracefully
        pe_val = calculate_permutation_entropy(signal, embedding_dim=3, time_delay=1)
        # Should not crash, might return 0
        assert isinstance(pe_val, float)
        
    def test_pe_embedding_parameters(self):
        """Test PE with different embedding parameters."""
        np.random.seed(42)
        signal = np.random.normal(0, 1, 1000)
        
        # Test with different embedding dimensions
        pe1 = calculate_permutation_entropy(signal, embedding_dim=3, time_delay=1)
        pe2 = calculate_permutation_entropy(signal, embedding_dim=4, time_delay=1)
        pe3 = calculate_permutation_entropy(signal, embedding_dim=3, time_delay=2)
        
        # All should be valid floats
        assert all(isinstance(p, float) and not np.isnan(p) for p in [pe1, pe2, pe3])
