import pytest
import numpy as np
from typing import List, Tuple
from src.stats_engine import (
    run_t_test,
    run_ancova,
    calculate_effect_size,
    calculate_confidence_interval,
    apply_bonferroni_correction,
    check_collinearity,
    calculate_power,
    frame_inference,
    aggregate_results
)
import pandas as pd
import os
import json

class TestPower:
    """Tests for calculate_power function (T025)."""

    def test_power_adequate_sample(self):
        """Test power calculation with sufficient sample size and effect."""
        # Large effect, large N -> high power
        power_result = calculate_power(effect_size=0.8, n1=100, n2=100, alpha=0.05)
        assert 0.0 <= power_result["power"] <= 1.0
        assert not power_result["underpowered"]

    def test_power_underpowered_small_n(self):
        """Test power calculation with small sample size (underpowered)."""
        # Small N -> low power
        power_result = calculate_power(effect_size=0.5, n1=10, n2=10, alpha=0.05)
        assert 0.0 <= power_result["power"] <= 1.0
        assert power_result["underpowered"] is True
        assert power_result["threshold"] == 0.80

    def test_power_underpowered_small_effect(self):
        """Test power calculation with small effect size (underpowered)."""
        # Small effect -> low power even with moderate N
        power_result = calculate_power(effect_size=0.1, n1=50, n2=50, alpha=0.05)
        assert 0.0 <= power_result["power"] <= 1.0
        # With very small effect, power is likely < 0.8
        if power_result["power"] < 0.8:
            assert power_result["underpowered"] is True

    def test_power_insufficient_sample_size(self):
        """Test power calculation with n < 2."""
        power_result = calculate_power(effect_size=0.5, n1=1, n2=10)
        assert power_result["power"] == 0.0
        assert power_result["underpowered"] is True
        assert "insufficient_sample_size" in power_result.get("reason", "")

    def test_power_calculation_values(self):
        """Verify that power increases with sample size."""
        p1 = calculate_power(effect_size=0.5, n1=20, n2=20)["power"]
        p2 = calculate_power(effect_size=0.5, n1=100, n2=100)["power"]
        assert p2 > p1, "Power should increase with sample size"

class TestBonferroniCorrection:
    def test_bonferroni_basic(self):
        p_values = [0.01, 0.05, 0.10]
        adjusted = apply_bonferroni_correction(p_values, alpha=0.05)
        assert len(adjusted) == 3
        assert adjusted[0] == min(0.01 * 3, 1.0)

    def test_bonferroni_cap(self):
        p_values = [0.5]
        adjusted = apply_bonferroni_correction(p_values, alpha=0.05)
        assert adjusted[0] == 1.0

class TestTTestLogic:
    def test_ttest_equal_variance(self):
        # Create synthetic data with known difference
        group1 = [10, 12, 11, 13, 12]
        group2 = [8, 9, 7, 10, 8]
        t_stat, p_val, is_sig = run_t_test(group1, group2)
        assert t_stat != 0.0
        assert p_val > 0.0 and p_val <= 1.0
        assert is_sig is True  # Large difference expected

    def test_ttest_no_difference(self):
        group1 = [5, 5, 5, 5]
        group2 = [5, 5, 5, 5]
        t_stat, p_val, is_sig = run_t_test(group1, group2)
        assert p_val > 0.05

class TestANCOVALogic:
    def test_ancova_basic(self):
        df = pd.DataFrame({
            "score": [10, 12, 11, 13, 12, 8, 9, 7, 10, 8],
            "group": ["A", "A", "A", "A", "A", "B", "B", "B", "B", "B"],
            "pre": [5, 6, 5, 6, 5, 5, 5, 5, 5, 5]
        })
        f_stat, p_val, summary = run_ancova(df, "score", "group", "pre")
        assert f_stat > 0.0
        assert 0.0 < p_val <= 1.0

class TestEffectSize:
    def test_cohens_d_positive(self):
        g1 = [10, 12, 11]
        g2 = [5, 6, 4]
        d = calculate_effect_size(g1, g2)
        assert d > 0

    def test_cohens_d_negative(self):
        g1 = [5, 6, 4]
        g2 = [10, 12, 11]
        d = calculate_effect_size(g1, g2)
        assert d < 0

class TestCollinearity:
    def test_collinearity_detection(self):
        df = pd.DataFrame({
            "x1": [1, 2, 3, 4, 5],
            "x2": [1.0, 2.0, 3.0, 4.0, 5.0], # Perfect correlation
            "y": [10, 20, 30, 40, 50]
        })
        diag = check_collinearity(df, ["x1", "x2"])
        assert diag["is_collinear"] is True
        assert diag["max_correlation"] > 0.8

    def test_no_collinearity(self):
        df = pd.DataFrame({
            "x1": [1, 2, 3, 4, 5],
            "x2": [5, 4, 3, 2, 1], # Negative correlation but not > 0.8 absolute? No, this is -1.0.
            "y": [10, 20, 30, 40, 50]
        })
        # Actually -1.0 is > 0.8 absolute. Let's use uncorrelated.
        df = pd.DataFrame({
            "x1": [1, 2, 3, 4, 5],
            "x2": [1, 5, 2, 4, 3],
            "y": [10, 20, 30, 40, 50]
        })
        diag = check_collinearity(df, ["x1", "x2"])
        assert diag["is_collinear"] is False

class TestFramingAndAggregation:
    def test_frame_inference_associational(self):
        power_info = {"power": 0.9, "underpowered": False}
        text = frame_inference(0.01, 0.5, power_info)
        assert "associational" in text.lower()
        assert "causal" not in text.lower()

    def test_frame_inference_underpowered(self):
        power_info = {"power": 0.4, "underpowered": True}
        text = frame_inference(0.1, 0.2, power_info)
        assert "underpowered" in text.lower()

    def test_aggregate_results_structure(self):
        ancova = (10.5, 0.001, {})
        t_test = (2.5, 0.01, True)
        power = calculate_power(0.5, 50, 50)
        collinearity = check_collinearity(pd.DataFrame({"a": [1,2], "b": [1,2]}), ["a", "b"])
        
        results = aggregate_results(
            ancova, t_test, 0.5, (0.3, 0.7),
            power, collinearity, pd.DataFrame()
        )
        
        assert "ancova" in results
        assert "secondary_descriptive_stats" in results
        assert "effect_size_cohen_d" in results
        assert "inference_framing" in results
        assert "associational" in results["inference_framing"].lower()
        assert results["inference_framing"].count("associational") > 0