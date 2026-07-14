import pytest
import numpy as np
from code.analysis.bootstrapper import (
    bootstrap_power_estimate,
    calculate_ks_distance,
    calculate_ks_distance
)
from code.simulation import get_rng

class TestBootstrapPowerEstimate:
    def test_bootstrap_power_estimate_basic(self):
        """Test basic bootstrap power estimation."""
        # Simulate p-values where 80% are < 0.05 (power = 0.8)
        rng = get_rng(42)
        n = 1000
        p_values = rng.uniform(0, 1, n)
        p_values[:800] = rng.uniform(0, 0.05, 800)  # Force 80% significant
        
        result = bootstrap_power_estimate(p_values, n_bootstrap=100, seed=42)
        
        assert result['estimated_power'] > 0.7
        assert result['estimated_power'] < 0.9
        assert result['ci_lower'] <= result['estimated_power']
        assert result['estimated_power'] <= result['ci_upper']
        assert result['n_bootstrap'] == 100
        assert result['n_samples'] == n

    def test_bootstrap_power_estimate_empty(self):
        """Test with empty p-values list."""
        result = bootstrap_power_estimate([], n_bootstrap=100)
        assert result['estimated_power'] == 0.0
        assert result['n_samples'] == 0

    def test_bootstrap_power_estimate_all_significant(self):
        """Test when all p-values are significant."""
        p_values = [0.01] * 100
        result = bootstrap_power_estimate(p_values, n_bootstrap=100)
        assert result['estimated_power'] == 1.0

    def test_bootstrap_power_estimate_none_significant(self):
        """Test when no p-values are significant."""
        p_values = [0.5] * 100
        result = bootstrap_power_estimate(p_values, n_bootstrap=100)
        assert result['estimated_power'] == 0.0

class TestCalculateKsDistance:
    def test_ks_distance_identical_distributions(self):
        """Test KS distance for identical distributions."""
        p1 = [0.1, 0.2, 0.3, 0.4, 0.5]
        p2 = [0.1, 0.2, 0.3, 0.4, 0.5]
        dist = calculate_ks_distance(p1, p2)
        assert dist == 0.0

    def test_ks_distance_different_distributions(self):
        """Test KS distance for clearly different distributions."""
        p1 = [0.01] * 50 + [0.99] * 50  # Bimodal
        p2 = [0.5] * 100  # All same
        dist = calculate_ks_distance(p1, p2)
        assert dist > 0.1  # Should be significantly different

    def test_ks_distance_empty(self):
        """Test with empty lists."""
        dist = calculate_ks_distance([], [])
        assert dist == 0.0

    def test_ks_distance_one_empty(self):
        """Test with one empty list."""
        dist = calculate_ks_distance([0.1, 0.2], [])
        assert dist == 0.0

class TestIntegration:
    def test_reproducibility(self):
        """Test that results are reproducible with same seed."""
        rng = get_rng(123)
        p_values = rng.uniform(0, 1, 500)
        p_values[:250] = rng.uniform(0, 0.05, 250)
        
        result1 = bootstrap_power_estimate(p_values, n_bootstrap=50, seed=999)
        result2 = bootstrap_power_estimate(p_values, n_bootstrap=50, seed=999)
        
        assert result1['estimated_power'] == result2['estimated_power']
        assert result1['ci_lower'] == result2['ci_lower']
        assert result1['ci_upper'] == result2['ci_upper']