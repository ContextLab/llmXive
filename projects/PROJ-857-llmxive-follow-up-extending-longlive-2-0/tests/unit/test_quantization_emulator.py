"""
Unit tests for the Stochastic Rounding implementation in quantization_emulator.py.

These tests verify:
1. Correctness of stochastic rounding logic.
2. Noise distribution matches theoretical uniform within 5% KL-divergence.
3. Handling of edge cases (single value, constant array).
"""

import numpy as np
import pytest
from scipy.stats import entropy

# Import the module under test
from simulation.quantization_emulator import (
    stochastic_round,
    verify_noise_distribution,
    run_quantization_emulation,
    PRECISION_BITS
)

class TestStochasticRounding:
    """Tests for the core stochastic_round function."""

    def test_supported_bits(self):
        """Test that supported bit depths are recognized."""
        assert 2 in PRECISION_BITS
        assert 4 in PRECISION_BITS
        assert 8 in PRECISION_BITS
        assert 16 not in PRECISION_BITS

    def test_invalid_bits_raises_error(self):
        """Test that invalid bit depth raises ValueError."""
        with pytest.raises(ValueError):
            stochastic_round(np.array([0.5]), bits=16)
        with pytest.raises(ValueError):
            stochastic_round(np.array([0.5]), bits=1)

    def test_constant_array(self):
        """Test that a constant array remains constant after quantization."""
        x = np.full(100, 0.5)
        result = stochastic_round(x, bits=4, rng=np.random.default_rng(42))
        # Since min=max, the function should return the original array
        np.testing.assert_array_equal(result, x)

    def test_single_value(self):
        """Test quantization of a single value."""
        x = np.array([0.5])
        result = stochastic_round(x, bits=4, rng=np.random.default_rng(42))
        assert result.shape == x.shape
        assert 0.0 <= result[0] <= 1.0

    def test_preserves_range(self):
        """Test that quantization preserves the min/max range of input."""
        x = np.array([0.0, 0.25, 0.5, 0.75, 1.0])
        result = stochastic_round(x, bits=4, rng=np.random.default_rng(42))
        assert result.min() >= x.min()
        assert result.max() <= x.max()

    def test_deterministic_with_seed(self):
        """Test that same seed produces same results."""
        x = np.random.uniform(0, 1, 100)
        rng1 = np.random.default_rng(123)
        rng2 = np.random.default_rng(123)
        
        result1 = stochastic_round(x, bits=4, rng=rng1)
        result2 = stochastic_round(x, bits=4, rng=rng2)
        
        np.testing.assert_array_equal(result1, result2)

class TestNoiseDistributionVerification:
    """Tests for the verify_noise_distribution function."""

    def test_kl_divergence_threshold(self):
        """Test that KL divergence is within 5% threshold for valid distribution."""
        for bits in [2, 4, 8]:
            kl_div, is_valid = verify_noise_distribution(bits, n_samples=10000, seed=42)
            assert is_valid, f"KL divergence {kl_div} exceeds 0.05 threshold for {bits}-bit"
            assert kl_div < 0.05

    def test_sample_size(self):
        """Test that the function uses the specified sample size."""
        # We can't easily inspect the internal N, but we can verify it runs without error
        # and produces a valid result for a smaller sample size
        kl_div, is_valid = verify_noise_distribution(bits=4, n_samples=1000, seed=42)
        assert isinstance(kl_div, float)
        assert isinstance(is_valid, bool)

    def test_different_seeds_produce_similar_results(self):
        """Test that different seeds produce similar KL divergence values."""
        kl_divs = []
        for seed in [42, 123, 456, 789]:
            kl_div, _ = verify_noise_distribution(bits=4, n_samples=10000, seed=seed)
            kl_divs.append(kl_div)
        
        # All should be below the threshold
        assert all(k < 0.05 for k in kl_divs)

class TestRunQuantizationEmulation:
    """Tests for the high-level run_quantization_emulation function."""

    def test_basic_emulation(self):
        """Test basic emulation workflow."""
        x = np.random.uniform(0, 1, 100)
        result = run_quantization_emulation(x, bits=4, seed=42)
        assert result.shape == x.shape
        assert np.all(result >= 0) and np.all(result <= 1)

    def test_multiple_bits(self):
        """Test emulation with different bit depths."""
        x = np.random.uniform(0, 1, 100)
        for bits in [2, 4, 8]:
            result = run_quantization_emulation(x, bits=bits, seed=42)
            assert result.shape == x.shape
            # Check that quantization levels are appropriate
            # For 2-bit, we should have 4 levels
            unique_levels = np.unique(result)
            assert len(unique_levels) <= PRECISION_BITS[bits]