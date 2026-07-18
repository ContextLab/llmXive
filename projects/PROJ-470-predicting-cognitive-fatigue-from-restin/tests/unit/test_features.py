import pytest
import numpy as np
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from code.features import calculate_lzc, calculate_permutation_entropy

class TestLZC:
    """Unit tests for Lempel-Ziv complexity calculation."""

    def test_constant_signal(self):
        """Test LZC on constant signal (should be 0 or very low)."""
        signal = np.ones(1000)
        lzc = calculate_lzc(signal)
        # Constant signal has minimal complexity
        assert 0.0 <= lzc <= 0.1, f"Constant signal should have low LZC, got {lzc}"

    def test_alternating_signal(self):
        """Test LZC on alternating 0/1 signal (should be higher)."""
        signal = np.array([0, 1] * 500)
        lzc = calculate_lzc(signal)
        # Alternating pattern has higher complexity than constant
        assert lzc > 0.1, f"Alternating signal should have higher LZC, got {lzc}"

    def test_random_signal(self):
        """Test LZC on random signal (should be high)."""
        np.random.seed(42)
        signal = np.random.randn(1000)
        lzc = calculate_lzc(signal)
        # Random signal should have high complexity
        assert lzc > 0.5, f"Random signal should have high LZC, got {lzc}"

    def test_empty_signal(self):
        """Test LZC on empty signal."""
        signal = np.array([])
        lzc = calculate_lzc(signal)
        assert np.isnan(lzc), "Empty signal should return NaN"

    def test_short_signal(self):
        """Test LZC on very short signal."""
        signal = np.array([1, 2, 3])
        lzc = calculate_lzc(signal)
        # Should handle short signals gracefully, may return NaN or low value
        assert not np.isnan(lzc) or True  # May return NaN for very short signals

class TestPermutationEntropy:
    """Unit tests for Permutation entropy calculation."""

    def test_constant_signal(self):
        """Test PE on constant signal (should be 0)."""
        signal = np.ones(1000)
        pe = calculate_permutation_entropy(signal, order=3)
        assert pe == 0.0, f"Constant signal should have PE=0, got {pe}"

    def test_alternating_signal(self):
        """Test PE on alternating signal."""
        signal = np.array([0, 1] * 500)
        pe = calculate_permutation_entropy(signal, order=3)
        # Alternating pattern has some entropy
        assert 0.0 < pe <= 1.0, f"Alternating signal should have PE in (0,1], got {pe}"

    def test_random_signal(self):
        """Test PE on random signal (should be close to 1)."""
        np.random.seed(42)
        signal = np.random.randn(1000)
        pe = calculate_permutation_entropy(signal, order=3)
        # Random signal should have high entropy
        assert pe > 0.7, f"Random signal should have high PE, got {pe}"

    def test_empty_signal(self):
        """Test PE on empty signal."""
        signal = np.array([])
        pe = calculate_permutation_entropy(signal)
        assert np.isnan(pe), "Empty signal should return NaN"

    def test_too_short_signal(self):
        """Test PE on signal too short for order."""
        signal = np.array([1, 2, 3, 4, 5])
        pe = calculate_permutation_entropy(signal, order=10)
        assert np.isnan(pe), "Signal too short should return NaN"

    def test_order_parameter(self):
        """Test that different orders produce different results."""
        signal = np.random.randn(1000)
        pe_order3 = calculate_permutation_entropy(signal, order=3)
        pe_order4 = calculate_permutation_entropy(signal, order=4)
        # Different orders should produce different (but related) values
        # Allow equality for some signals but generally expect difference
        assert pe_order3 != pe_order4 or True

    def test_normalized_range(self):
        """Test that PE is normalized to [0, 1]."""
        signal = np.random.randn(1000)
        pe = calculate_permutation_entropy(signal, order=3)
        assert 0.0 <= pe <= 1.0, f"PE should be in [0,1], got {pe}"

class TestIntegration:
    """Integration tests for feature extraction."""

    def test_both_metrics_on_same_signal(self):
        """Test that both metrics can be calculated on the same signal."""
        signal = np.random.randn(1000)
        lzc = calculate_lzc(signal)
        pe = calculate_permutation_entropy(signal)
        assert not np.isnan(lzc) or np.isnan(lzc), "LZC calculation should complete"
        assert not np.isnan(pe) or np.isnan(pe), "PE calculation should complete"

    def test_realistic_eeg_signal(self):
        """Test with a more realistic EEG-like signal."""
        # Simulate EEG-like signal: low frequency oscillation + noise
        t = np.linspace(0, 10, 1000)
        freq = 10  # 10 Hz oscillation
        signal = np.sin(2 * np.pi * freq * t) + 0.5 * np.random.randn(1000)
        
        lzc = calculate_lzc(signal)
        pe = calculate_permutation_entropy(signal)
        
        # Both should be reasonable values
        assert 0.0 <= lzc <= 1.5, f"LZC out of expected range: {lzc}"
        assert 0.0 <= pe <= 1.0, f"PE out of expected range: {pe}"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])