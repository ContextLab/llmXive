"""
Unit tests for power analysis module.

These tests verify the correctness of power calculations and MDES estimates
for the kinetic lifetime study design.
"""
import pytest
import numpy as np
from scipy import stats

from analysis.power import (
    calculate_effect_size,
    estimate_mdes,
    calculate_post_hoc_power,
    analyze_kinetic_power,
    write_power_report
)


class TestEffectSizeCalculation:
    """Tests for Cohen's d effect size calculation."""

    def test_cohens_d_identical_means(self):
        """Effect size should be 0 when means are identical."""
        d, interp = calculate_effect_size(10.0, 10.0, 2.0, 2.0, 3, 3)
        assert d == 0.0
        assert interp == "negligible"

    def test_cohens_d_large_effect(self):
        """Large effect size when means differ substantially."""
        # Means differ by 4 units, pooled std ~2
        d, interp = calculate_effect_size(10.0, 14.0, 2.0, 2.0, 3, 3)
        assert d > 0.8  # Large effect
        assert interp == "large"

    def test_cohens_d_small_effect(self):
        """Small effect size when means differ slightly."""
        d, interp = calculate_effect_size(10.0, 10.5, 2.0, 2.0, 3, 3)
        assert 0.2 <= d < 0.5
        assert interp == "small"

    def test_cohens_d_pooled_std_calculation(self):
        """Verify pooled standard deviation calculation."""
        # n1=3, n2=3, std1=2, std2=4
        # pooled_std = sqrt(((2*4) + (2*16)) / 4) = sqrt(40/4) = sqrt(10)
        d, _ = calculate_effect_size(10.0, 12.0, 2.0, 4.0, 3, 3)
        expected_pooled = np.sqrt(((2 * 4) + (2 * 16)) / 4)
        expected_d = 2.0 / expected_pooled
        assert np.isclose(d, expected_d)


class TestMDESEstimation:
    """Tests for Minimum Detectable Effect Size estimation."""

    def test_mdes_decreases_with_sample_size(self):
        """MDES should decrease as sample size increases."""
        mdes_n3 = estimate_mdes(n=3, power=0.80)
        mdes_n10 = estimate_mdes(n=10, power=0.80)
        mdes_n30 = estimate_mdes(n=30, power=0.80)

        assert mdes_n3 > mdes_n10 > mdes_n30

    def test_mdes_increases_with_power(self):
        """MDES should increase as desired power increases."""
        mdes_80 = estimate_mdes(n=3, power=0.80)
        mdes_90 = estimate_mdes(n=3, power=0.90)
        mdes_95 = estimate_mdes(n=3, power=0.95)

        assert mdes_95 > mdes_90 > mdes_80

    def test_mdes_reasonable_values(self):
        """MDES for n=3 should be large (reflecting low power)."""
        mdes = estimate_mdes(n=3, power=0.80)
        # With n=3, we need a very large effect to detect it
        assert mdes > 1.0
        assert mdes < 3.0


class TestPostHocPower:
    """Tests for post-hoc power calculation."""

    def test_power_increases_with_effect_size(self):
        """Power should increase with larger effect sizes."""
        power_small = calculate_post_hoc_power(cohens_d=0.3, n=3)
        power_medium = calculate_post_hoc_power(cohens_d=0.6, n=3)
        power_large = calculate_post_hoc_power(cohens_d=1.5, n=3)

        assert power_large > power_medium > power_small

    def test_power_bounds(self):
        """Power should always be between 0 and 1."""
        power = calculate_post_hoc_power(cohens_d=0.5, n=3)
        assert 0.0 <= power <= 1.0

    def test_power_with_zero_effect(self):
        """Power should be near alpha when effect size is zero."""
        power = calculate_post_hoc_power(cohens_d=0.0, n=3)
        assert power < 0.1  # Should be close to alpha (0.05)


class TestIntegration:
    """Integration tests for the power analysis module."""

    def test_analyze_kinetic_power_no_data(self, tmp_path):
        """Should return theoretical analysis when no data exists."""
        results = analyze_kinetic_power(str(tmp_path / "nonexistent.csv"))

        assert results["status"] == "theoretical_only"
        assert "theoretical_mdes_80_power" in results
        assert results["sample_size"] == 3

    def test_write_power_report(self, tmp_path):
        """Should write valid JSON report."""
        results = {
            "status": "test",
            "sample_size": 3,
            "theoretical_mdes_80_power": 1.5,
            "pairwise_comparisons": [],
            "limitations": ["Test limitation"]
        }

        output_path = tmp_path / "test_report.json"
        written_path = write_power_report(results, str(output_path))

        assert written_path == str(output_path)
        assert output_path.exists()

        import json
        with open(output_path) as f:
            loaded = json.load(f)

        assert loaded["status"] == "test"
        assert loaded["sample_size"] == 3