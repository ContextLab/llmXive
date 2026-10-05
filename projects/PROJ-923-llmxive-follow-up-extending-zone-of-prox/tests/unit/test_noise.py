"""
Unit tests for noise injection utilities (T026).

These tests verify that the noise injection logic works correctly
and integrates properly with the seed management system.
"""
import pytest
import numpy as np
from unittest.mock import patch, MagicMock

from utils.noise import inject_noise, inject_gaussian_noise, apply_noise_to_batch
from utils.seeds import get_rng

class TestInjectNoise:
    """Tests for the inject_noise function."""

    def test_basic_noise_injection(self):
        """Test that noise is actually injected."""
        rng = get_rng(42)
        confidence = 0.5
        sigma = 0.1
        
        # Run multiple times to ensure variance (since we're using a real RNG)
        results = [inject_noise(confidence, sigma, rng) for _ in range(10)]
        
        # All results should be in valid range
        for result in results:
            assert 0.0 <= result <= 1.0, f"Result {result} out of range"
        
        # With a fixed seed, we should get deterministic results
        rng1 = get_rng(42)
        rng2 = get_rng(42)
        
        result1 = inject_noise(0.5, 0.1, rng1)
        result2 = inject_noise(0.5, 0.1, rng2)
        
        assert result1 == result2, "Same seed should produce same result"

    def test_clamping_lower_bound(self):
        """Test that results below 0.0 are clamped."""
        rng = get_rng(999)
        # Force a scenario where noise would push below 0
        # We can't easily force this with a random RNG, so we test the logic
        # by mocking the noise value
        with patch('numpy.random.Generator.normal', return_value=-0.6):
            result = inject_noise(0.1, 0.05, rng)
            assert result == 0.0, "Should clamp to 0.0"

    def test_clamping_upper_bound(self):
        """Test that results above 1.0 are clamped."""
        rng = get_rng(999)
        with patch('numpy.random.Generator.normal', return_value=0.6):
            result = inject_noise(0.95, 0.05, rng)
            assert result == 1.0, "Should clamp to 1.0"

    def test_invalid_confidence_below_zero(self):
        """Test that confidence < 0.0 raises ValueError."""
        rng = get_rng(42)
        with pytest.raises(ValueError, match="Confidence must be in range"):
            inject_noise(-0.1, 0.05, rng)

    def test_invalid_confidence_above_one(self):
        """Test that confidence > 1.0 raises ValueError."""
        rng = get_rng(42)
        with pytest.raises(ValueError, match="Confidence must be in range"):
            inject_noise(1.1, 0.05, rng)

    def test_zero_sigma(self):
        """Test that sigma=0.0 returns the original value."""
        rng = get_rng(42)
        confidence = 0.75
        result = inject_noise(confidence, 0.0, rng)
        assert result == confidence, "Zero sigma should return original value"

    def test_default_sigma(self):
        """Test that default sigma is 0.05."""
        rng = get_rng(42)
        # We can't easily verify the exact sigma value without mocking,
        # but we can verify the function signature works
        result = inject_noise(0.5, rng=rng)
        assert 0.0 <= result <= 1.0

    def test_rng_parameter_required_for_reproducibility(self):
        """Test that passing an explicit RNG ensures reproducibility."""
        confidence = 0.5
        sigma = 0.1
        
        # Create two identical RNGs
        rng1 = get_rng(12345)
        rng2 = get_rng(12345)
        
        result1 = inject_noise(confidence, sigma, rng1)
        result2 = inject_noise(confidence, sigma, rng2)
        
        assert result1 == result2, "Identical RNGs should produce identical results"

class TestInjectGaussianNoise:
    """Tests for the inject_gaussian_noise alias."""

    def test_alias_functionality(self):
        """Test that inject_gaussian_noise behaves identically to inject_noise."""
        rng = get_rng(42)
        confidence = 0.6
        sigma = 0.08
        
        result1 = inject_noise(confidence, sigma, rng)
        
        rng2 = get_rng(42)
        result2 = inject_gaussian_noise(confidence, sigma, rng2)
        
        assert result1 == result2, "Alias should behave identically"

class TestApplyNoiseToBatch:
    """Tests for batch noise application."""

    def test_batch_processing(self):
        """Test that batch processing works correctly."""
        rng = get_rng(42)
        confidences = [0.1, 0.5, 0.9]
        sigma = 0.05
        
        results = apply_noise_to_batch(confidences, sigma, rng)
        
        assert len(results) == len(confidences)
        for result in results:
            assert 0.0 <= result <= 1.0

    def test_batch_reproducibility(self):
        """Test that batch processing is reproducible with same RNG."""
        confidences = [0.2, 0.4, 0.6, 0.8]
        sigma = 0.1
        
        rng1 = get_rng(555)
        rng2 = get_rng(555)
        
        results1 = apply_noise_to_batch(confidences, sigma, rng1)
        results2 = apply_noise_to_batch(confidences, sigma, rng2)
        
        assert results1 == results2, "Same RNG should produce same batch results"

    def test_empty_batch(self):
        """Test handling of empty batch."""
        rng = get_rng(42)
        results = apply_noise_to_batch([], 0.05, rng)
        assert results == []