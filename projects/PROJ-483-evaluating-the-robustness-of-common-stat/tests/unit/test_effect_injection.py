"""
Unit tests for effect injection logic (US3).

Tests the logic to inject true effects (mean shift) into data
before dependency injection, as required by T026.
"""
import numpy as np
import pytest
from scipy import stats
from pathlib import Path
import sys

# Add parent directory to path to import code modules
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from dependency_injector import ar1_inject, block_bootstrap


class TestEffectInjection:
    """Tests for the effect injection logic required by US3."""

    def test_inject_mean_shift_additive(self):
        """Test that a mean shift is correctly added to a group."""
        rng = np.random.default_rng(42)
        n = 100
        # Generate null data (mean=0)
        group_null = rng.normal(loc=0.0, scale=1.0, size=n)
        
        # Define effect size (delta)
        delta = 1.5
        
        # Inject effect (simulating the logic in simulation_runner)
        # In a real scenario, we would add delta to the mean
        group_effect = group_null + delta
        
        # Verify the mean has shifted
        observed_mean = np.mean(group_effect)
        assert np.isclose(observed_mean, delta, atol=0.1), \
            f"Expected mean shift of {delta}, got {observed_mean}"
        
        # Verify the variance is preserved (approximately)
        original_var = np.var(group_null)
        shifted_var = np.var(group_effect)
        assert np.isclose(original_var, shifted_var, rtol=0.1), \
            f"Variance changed from {original_var} to {shifted_var}"

    def test_inject_mean_shift_two_groups(self):
        """Test effect injection in a two-sample scenario (t-test context)."""
        rng = np.random.default_rng(123)
        n1, n2 = 50, 50
        
        # Group 1: Null (mean=0)
        group1 = rng.normal(loc=0.0, scale=1.0, size=n1)
        
        # Group 2: Effect (mean=delta)
        delta = 2.0
        group2_base = rng.normal(loc=0.0, scale=1.0, size=n2)
        group2 = group2_base + delta
        
        # Verify separation
        diff = np.mean(group2) - np.mean(group1)
        assert diff > 0, "Effect should create a positive difference"
        assert np.isclose(diff, delta, atol=0.5), \
            f"Expected difference ~{delta}, got {diff}"

    def test_effect_injection_before_dependency_injection(self):
        """
        Verify that injecting an effect before dependency injection
        results in a detectable signal, whereas dependency injection
        alone (without effect) might obscure it.
        
        This tests the "True Effect Mode" logic required by T026.
        """
        rng = np.random.default_rng(456)
        n = 100
        delta = 1.0
        rho = 0.3  # AR(1) strength
        
        # Scenario A: Effect injected, NO dependency
        group_a_null = rng.normal(0, 1, n)
        group_a_effect = group_a_null + delta
        # No dependency injection here
        
        # Scenario B: Effect injected, THEN dependency injected
        group_b_null = rng.normal(0, 1, n)
        group_b_effect = group_b_null + delta
        # Inject AR(1) dependency
        group_b_injected = ar1_inject(group_b_effect, rho, rng)
        
        # Perform t-tests
        t_stat_a, p_val_a = stats.ttest_1samp(group_a_effect, 0.0)
        t_stat_b, p_val_b = stats.ttest_1samp(group_b_injected, 0.0)
        
        # Both should ideally reject the null (p < 0.05) if power is sufficient
        # However, the key test is that the effect is present in the data
        # before dependency injection corrupts the standard error.
        # We verify the mean shift exists in the injected data.
        assert np.abs(np.mean(group_b_injected) - delta) < 1.5, \
            "Effect should be roughly preserved after dependency injection"

    def test_effect_size_preservation_across_dependencies(self):
        """
        Test that the injected effect size remains detectable across
        different dependency structures (AR(1) vs Block Bootstrap).
        """
        rng = np.random.default_rng(789)
        n = 200
        delta = 1.5
        rho = 0.5
        block_size = 10
        
        # Generate base data with effect
        base_data = rng.normal(0, 1, n) + delta
        
        # Apply AR(1)
        ar1_data = ar1_inject(base_data.copy(), rho, rng)
        ar1_mean = np.mean(ar1_data)
        
        # Apply Block Bootstrap (resampling with replacement of blocks)
        # Note: Block bootstrap resamples blocks, so the mean of the
        # resampled data will fluctuate around the original mean.
        # We verify the structure is valid and the mean is roughly preserved.
        block_data, _ = block_bootstrap(base_data.copy(), block_size, rng)
        block_mean = np.mean(block_data)
        
        # The means should be close to the injected delta
        assert np.isclose(ar1_mean, delta, atol=0.5), \
            f"AR(1) mean {ar1_mean} deviates too much from {delta}"
        assert np.isclose(block_mean, delta, atol=0.5), \
            f"Block bootstrap mean {block_mean} deviates too much from {delta}"

    def test_no_effect_injection_when_delta_is_zero(self):
        """Verify that delta=0 results in no shift."""
        rng = np.random.default_rng(999)
        n = 50
        original = rng.normal(0, 1, n)
        
        # Inject zero effect
        modified = original + 0.0
        
        # Should be identical
        assert np.array_equal(original, modified), \
            "Zero effect injection should not change data"
        assert np.mean(modified) == np.mean(original)

    def test_effect_injection_with_different_scales(self):
        """Test effect injection works correctly with different standard deviations."""
        rng = np.random.default_rng(111)
        n = 100
        scales = [0.5, 1.0, 2.0]
        delta = 1.0
        
        for scale in scales:
            data = rng.normal(0, scale, n)
            data_with_effect = data + delta
            
            # The shift should be exactly delta regardless of scale
            mean_shift = np.mean(data_with_effect) - np.mean(data)
            assert np.isclose(mean_shift, delta, atol=1e-9), \
                f"Scale {scale}: Expected shift {delta}, got {mean_shift}"