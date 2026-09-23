"""
Unit tests for the power_analysis module.
"""

import pytest
import math
import tempfile
import os
from pathlib import Path
import pandas as pd

from src.utils.power_analysis import (
    calculate_effect_size,
    calculate_power_spearman,
    calculate_margin_of_error,
    run_power_analysis
)


class TestEffectSize:
    def test_positive_rho(self):
        """Test Fisher's z for a positive correlation."""
        rho = 0.5
        z = calculate_effect_size(rho)
        # 0.5 * ln((1.5)/(0.5)) = 0.5 * ln(3) ≈ 0.5493
        expected = 0.5 * math.log(3)
        assert math.isclose(z, expected, rel_tol=1e-5)

    def test_negative_rho(self):
        """Test Fisher's z for a negative correlation."""
        rho = -0.5
        z = calculate_effect_size(rho)
        expected = -0.5 * math.log(3)
        assert math.isclose(z, expected, rel_tol=1e-5)

    def test_zero_rho(self):
        """Test Fisher's z for zero correlation."""
        rho = 0.0
        z = calculate_effect_size(rho)
        assert math.isclose(z, 0.0, rel_tol=1e-5)

    def test_invalid_rho_high(self):
        """Test that rho >= 1 raises ValueError."""
        with pytest.raises(ValueError):
            calculate_effect_size(1.0)

    def test_invalid_rho_low(self):
        """Test that rho <= -1 raises ValueError."""
        with pytest.raises(ValueError):
            calculate_effect_size(-1.0)


class TestPowerSpearman:
    def test_high_power_large_n(self):
        """Large sample size with moderate effect should yield high power."""
        power = calculate_power_spearman(n=500, rho=0.3, alpha=0.05)
        assert power > 0.9

    def test_low_power_small_n(self):
        """Small sample size with moderate effect should yield low power."""
        power = calculate_power_spearman(n=10, rho=0.3, alpha=0.05)
        assert power < 0.5

    def test_zero_effect_size(self):
        """If effect size is 0, power should be approximately alpha (type I error rate)."""
        # With n=100, rho=0, power should be close to 0.05
        power = calculate_power_spearman(n=100, rho=0.0, alpha=0.05)
        assert 0.04 < power < 0.06

    def test_small_sample_size(self):
        """Sample size < 3 should return 0.0 power."""
        power = calculate_power_spearman(n=2, rho=0.5)
        assert power == 0.0


class TestMarginOfError:
    def test_moe_decreases_with_n(self):
        """Margin of error should decrease as sample size increases."""
        moe_small = calculate_margin_of_error(n=20, rho=0.5)
        moe_large = calculate_margin_of_error(n=200, rho=0.5)
        assert moe_small > moe_large

    def test_moe_at_zero(self):
        """Test MoE calculation at rho=0."""
        moe = calculate_margin_of_error(n=100, rho=0.0)
        assert moe > 0

    def test_small_sample_size_error(self):
        """Sample size < 3 should raise ValueError."""
        with pytest.raises(ValueError):
            calculate_margin_of_error(n=2, rho=0.5)


class TestRunPowerAnalysis:
    def test_run_analysis_returns_dict(self):
        """Test that run_power_analysis returns a dictionary with correct keys."""
        result = run_power_analysis(sample_size=100, effect_size=0.3)
        assert "power" in result
        assert "margin_of_error" in result
        assert "sample_size" in result
        assert "effect_size" in result
        assert "alpha" in result

    def test_run_analysis_writes_file(self):
        """Test that run_power_analysis writes a TSV file when output_path is provided."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "power_test.tsv"
            run_power_analysis(sample_size=100, effect_size=0.3, output_path=output_path)
            
            assert output_path.exists()
            df = pd.read_csv(output_path, sep='\t')
            assert "power" in df.columns
            assert "margin_of_error" in df.columns
            assert len(df) == 1
            assert df["sample_size"].iloc[0] == 100