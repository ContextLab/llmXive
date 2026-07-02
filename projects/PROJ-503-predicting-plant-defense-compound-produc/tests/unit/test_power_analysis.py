"""
Unit tests for the power analysis utility.
"""
import math
import pytest
import sys
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from code.utils.power_analysis import (
    calculate_sample_size_for_correlation,
    calculate_power_for_correlation,
    calculate_z_score,
    run_analysis
)


class TestZScore:
    def test_z_score_valid(self):
        # p=0.05 two-tailed -> z ~ 1.96
        # Our function takes p-value (two-tailed input to function logic?)
        # The function calculates z from p.
        # If p=0.05, z should be approx 1.96
        z = calculate_z_score(0.05)
        assert abs(z - 1.96) < 0.01

        # p=0.5 -> z = 0
        z = calculate_z_score(0.5)
        assert abs(z) < 0.01

    def test_z_score_invalid(self):
        with pytest.raises(ValueError):
            calculate_z_score(0)
        with pytest.raises(ValueError):
            calculate_z_score(1)
        with pytest.raises(ValueError):
            calculate_z_score(-0.1)
        with pytest.raises(ValueError):
            calculate_z_score(1.1)


class TestSampleSizeCalculation:
    def test_default_parameters(self):
        # Default: power=0.8, alpha=0.05, r=0.5
        # Expected n is typically around 28-29
        n = calculate_sample_size_for_correlation()
        assert n >= 28
        assert n <= 35  # Reasonable range

    def test_higher_power_requires_more_samples(self):
        n_08 = calculate_sample_size_for_correlation(power=0.8)
        n_09 = calculate_sample_size_for_correlation(power=0.9)
        assert n_09 > n_08

    def test_stronger_correlation_requires_fewer_samples(self):
        n_r05 = calculate_sample_size_for_correlation(target_r=0.5)
        n_r08 = calculate_sample_size_for_correlation(target_r=0.8)
        assert n_r08 < n_r05

    def test_invalid_r(self):
        with pytest.raises(ValueError):
            calculate_sample_size_for_correlation(target_r=1.0)
        with pytest.raises(ValueError):
            calculate_sample_size_for_correlation(target_r=-1.0)
        with pytest.raises(ValueError):
            calculate_sample_size_for_correlation(target_r=0.0)

    def test_invalid_alpha(self):
        with pytest.raises(ValueError):
            calculate_sample_size_for_correlation(alpha=0)
        with pytest.raises(ValueError):
            calculate_sample_size_for_correlation(alpha=1)

    def test_invalid_power(self):
        with pytest.raises(ValueError):
            calculate_sample_size_for_correlation(power=0)
        with pytest.raises(ValueError):
            calculate_sample_size_for_correlation(power=1)


class TestPowerCalculation:
    def test_power_increases_with_n(self):
        p_10 = calculate_power_for_correlation(n=10, target_r=0.5)
        p_30 = calculate_power_for_correlation(n=30, target_r=0.5)
        assert p_30 > p_10

    def test_power_increases_with_r(self):
        p_r05 = calculate_power_for_correlation(n=30, target_r=0.5)
        p_r08 = calculate_power_for_correlation(n=30, target_r=0.8)
        assert p_r08 > p_r05

    def test_small_n(self):
        # With n=3, power should be 0 or very low
        p = calculate_power_for_correlation(n=3, target_r=0.5)
        assert p == 0.0


class TestRunAnalysis:
    def test_run_analysis_default(self):
        result = run_analysis()
        assert "parameters" in result
        assert "results" in result
        assert result["status"] == "success"
        assert result["results"]["minimum_sample_size"] >= 28

    def test_run_analysis_with_output(self, tmp_path):
        output_file = tmp_path / "test_power.json"
        result = run_analysis(output_path=str(output_file))
        assert output_file.exists()
        assert result["status"] == "success"