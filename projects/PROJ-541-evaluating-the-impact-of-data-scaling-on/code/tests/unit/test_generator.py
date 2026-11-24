"""
Unit tests for the synthetic data generator (FR-001 / T002).

Checks:
  * Null dataset mean difference < 0.01.
  * Alternative dataset mean difference within +/- 0.05 of the
    requested effect size.
  * Skewed data achieves target skewness within +/- 0.1.
"""

import sys
from pathlib import Path

import numpy as np
import pytest
from scipy import stats

PROJECT_ROOT = Path(__file__).resolve().parents[3]
CODE_ROOT = PROJECT_ROOT / "code"
for p in (str(PROJECT_ROOT), str(CODE_ROOT)):
    if p not in sys.path:
        sys.path.insert(0, p)

from simulation.generator import (  # noqa: E402
    generate_alternative,
    generate_null,
    generate_synthetic_data,
    generate_synthetic_data_from_config,
)
from simulation.config import SimulationConfig  # noqa: E402


class TestGenerateNull:
    def test_null_mean_difference_below_001_normal(self):
        g1, g2 = generate_null(n_samples=2000, variance=1.0, seed=42)
        assert abs(g1.mean() - g2.mean()) < 0.01

    def test_null_mean_difference_below_001_skewed(self):
        g1, g2 = generate_null(n_samples=5000, variance=1.0, skewness=2.0, seed=7)
        assert abs(g1.mean() - g2.mean()) < 0.01

    def test_null_groups_have_correct_size(self):
        g1, g2 = generate_null(n_samples=137, seed=1)
        assert g1.shape == (137,)
        assert g2.shape == (137,)

    def test_null_variance_close_to_target(self):
        g1, _ = generate_null(n_samples=20000, variance=4.0, seed=3)
        assert abs(g1.var() - 4.0) < 0.5

    def test_null_invalid_inputs_raise(self):
        with pytest.raises(ValueError):
            generate_null(n_samples=0)
        with pytest.raises(ValueError):
            generate_null(n_samples=10, variance=-1.0)


class TestGenerateAlternative:
    @pytest.mark.parametrize("effect", [0.5, 1.0, 1.5])
    def test_mean_difference_within_005_of_effect(self, effect):
        g1, g2 = generate_alternative(
            effect_size=effect, n_samples=1000, variance=1.0, seed=99
        )
        diff = g2.mean() - g1.mean()
        assert abs(diff - effect) < 0.05

    def test_effect_direction_is_group2_minus_group1(self):
        g1, g2 = generate_alternative(effect_size=1.0, n_samples=500, seed=5)
        assert (g2.mean() - g1.mean()) > 0

    def test_alternative_skewed_mean_difference(self):
        g1, g2 = generate_alternative(
            effect_size=1.0, n_samples=5000, variance=1.0, skewness=2.0, seed=11
        )
        assert abs((g2.mean() - g1.mean()) - 1.0) < 0.05


class TestSkewness:
    @pytest.mark.parametrize("target", [0.5, 1.0, 2.0])
    def test_skewness_within_01_of_target(self, target):
        g1, g2 = generate_alternative(
            effect_size=1.0,
            n_samples=10000,
            variance=1.0,
            skewness=target,
            seed=13,
        )
        assert abs(stats.skew(g1) - target) < 0.1
        assert abs(stats.skew(g2) - target) < 0.1

    def test_zero_skewness_is_normal(self):
        g1, _ = generate_null(n_samples=20000, variance=1.0, seed=17)
        assert abs(stats.skew(g1)) < 0.1


class TestLegacyApi:
    def test_generate_synthetic_data_null(self):
        g1, g2 = generate_synthetic_data(
            mean=0.0, var=1.0, skew=0.0, kurt=3.0, n=2000, seed=42
        )
        assert abs(g1.mean() - g2.mean()) < 0.01

    def test_generate_synthetic_data_alternative(self):
        g1, g2 = generate_synthetic_data(
            mean=1.0, var=1.0, skew=0.0, kurt=3.0, n=1000, seed=42
        )
        assert abs((g2.mean() - g1.mean()) - 1.0) < 0.05

    def test_zero_variance_returns_empty(self):
        g1, g2 = generate_synthetic_data(
            mean=0.0, var=0.0, skew=0.0, kurt=3.0, n=100, seed=1
        )
        assert g1.size == 0
        assert g2.size == 0

    def test_from_config(self):
        config = SimulationConfig(
            distribution_type="Normal",
            mean=1.0,
            variance=1.0,
            skewness=0.0,
            kurtosis=3.0,
        )
        g1, g2 = generate_synthetic_data_from_config(config)
        assert g1.shape == g2.shape
        assert g1.size > 0

    def test_deterministic_with_seed(self):
        a = generate_null(n_samples=100, seed=123)
        b = generate_null(n_samples=100, seed=123)
        np.testing.assert_array_equal(a[0], b[0])
        np.testing.assert_array_equal(a[1], b[1])


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
