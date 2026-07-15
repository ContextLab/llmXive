import os
import sys
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
from scipy import stats

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from statistical_analysis import (
    compute_effect_size_cohen_d,
    compute_power_cohen_d,
    compute_cliffs_delta,
    get_effect_size_magnitude,
    run_mann_whitney_u_test,
    apply_benjamini_hochberg_correction,
    get_effect_size_magnitude
)

class TestEffectSize:
    def test_cohen_d_identical_groups(self):
        """Cohen's d should be 0 for identical groups."""
        group1 = np.array([1.0, 2.0, 3.0])
        group2 = np.array([1.0, 2.0, 3.0])
        d = compute_effect_size_cohen_d(group1, group2)
        assert abs(d) < 1e-10

    def test_cohen_d_different_groups(self):
        """Cohen's d should be non-zero for different groups."""
        group1 = np.array([1.0, 2.0, 3.0])
        group2 = np.array([10.0, 11.0, 12.0])
        d = compute_effect_size_cohen_d(group1, group2)
        assert abs(d) > 0.5

    def test_cliffs_delta_identical_groups(self):
        """Cliff's delta should be 0 for identical distributions."""
        group1 = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        group2 = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        delta = compute_cliffs_delta(group1, group2)
        assert abs(delta) < 0.1  # Allow small floating point errors

    def test_cliffs_delta_magnitude_labels(self):
        """Test magnitude label assignment."""
        assert get_effect_size_magnitude(0.05) == "negligible"
        assert get_effect_size_magnitude(0.2) == "small"
        assert get_effect_size_magnitude(0.4) == "medium"
        assert get_effect_size_magnitude(0.6) == "large"
        assert get_effect_size_magnitude(-0.2) == "small"

class TestMannWhitney:
    def test_mann_whitney_identical(self):
        """Mann-Whitney U test p-value should be high for identical groups."""
        group1 = [1, 2, 3, 4, 5]
        group2 = [1, 2, 3, 4, 5]
        u, p = run_mann_whitney_u_test(group1, group2)
        assert p > 0.05

    def test_mann_whitney_different(self):
        """Mann-Whitney U test should detect difference in clearly separated groups."""
        group1 = [1, 2, 3, 4, 5]
        group2 = [10, 11, 12, 13, 14]
        u, p = run_mann_whitney_u_test(group1, group2)
        assert p < 0.05

class TestBHCorrection:
    def test_bh_correction_empty(self):
        """BH correction on empty list should return empty list."""
        result = apply_benjamini_hochberg_correction([])
        assert result == []

    def test_bh_correction_single(self):
        """BH correction on single p-value."""
        result = apply_benjamini_hochberg_correction([0.05])
        assert len(result) == 1
        # Single p-value adjusted should be same or capped at 1
        assert 0.0 <= result[0] <= 1.0

    def test_bh_correction_monotonicity(self):
        """Adjusted p-values should be monotonically non-decreasing when sorted by raw p."""
        raw_p = [0.01, 0.03, 0.02, 0.05]
        adjusted = apply_benjamini_hochberg_correction(raw_p)
        
        # Sort by original indices to check monotonicity in original order
        # Actually, BH ensures that if p_i < p_j, then adj_p_i <= adj_p_j
        # Let's check the property: adjusted p-values should be non-decreasing when raw p-values are sorted
        sorted_indices = sorted(range(len(raw_p)), key=lambda i: raw_p[i])
        sorted_adj = [adjusted[i] for i in sorted_indices]
        
        for i in range(len(sorted_adj) - 1):
            assert sorted_adj[i] <= sorted_adj[i + 1] + 1e-10  # Allow small floating point errors

    def test_bh_correction_bounds(self):
        """All adjusted p-values should be between 0 and 1."""
        raw_p = [0.01, 0.03, 0.02, 0.05, 0.1, 0.2]
        adjusted = apply_benjamini_hochberg_correction(raw_p)
        for p in adjusted:
            assert 0.0 <= p <= 1.0

class TestPowerAnalysis:
    def test_power_cohen_d_large_effect(self):
        """Large effect size should yield high power with sufficient sample size."""
        power = compute_power_cohen_d(effect_size=1.0, n1=50, n2=50)
        assert power > 0.8

    def test_power_cohen_d_small_effect(self):
        """Small effect size with small sample should yield low power."""
        power = compute_power_cohen_d(effect_size=0.2, n1=10, n2=10)
        assert power < 0.5

if __name__ == "__main__":
    pytest.main([__file__, "-v"])