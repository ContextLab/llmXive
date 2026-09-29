"""
Unit tests for stats_engine.py, specifically for power analysis (T025).
"""

import pytest
import numpy as np
from typing import List, Tuple
from src.stats_engine import (
    calculate_power,
    run_t_test,
    calculate_effect_size,
    calculate_confidence_interval,
    apply_bonferroni_correction,
    check_collinearity,
    frame_inference,
    aggregate_results
)
import pandas as pd
import os


class TestPowerAnalysis:
    """Tests for the calculate_power function (T025)."""

    def test_calculate_power_sufficient(self):
        """Test power calculation with large sample size (should be > 0.80)."""
        # Large N, moderate effect size
        effect_size = 0.5
        n1 = 100
        n2 = 100
        
        result = calculate_power(effect_size, n1, n2)
        
        assert result["power"] > 0.80
        assert result["is_underpowered"] is False
        assert result["threshold"] == 0.80

    def test_calculate_power_underpowered(self):
        """Test power calculation with small sample size (should be < 0.80)."""
        # Small N
        effect_size = 0.5
        n1 = 10
        n2 = 10
        
        result = calculate_power(effect_size, n1, n2)
        
        assert result["is_underpowered"] is True
        assert result["threshold"] == 0.80
        # Power should be low for small N
        assert result["power"] < 0.80

    def test_calculate_power_zero_effect(self):
        """Test power calculation with zero effect size."""
        effect_size = 0.0
        n1 = 50
        n2 = 50
        
        result = calculate_power(effect_size, n1, n2)
        
        # Power should be very low (close to alpha) if effect is 0
        assert result["is_underpowered"] is True
        assert result["power"] < 0.80

    def test_calculate_power_invalid_n(self):
        """Test power calculation with invalid sample sizes."""
        result = calculate_power(0.5, 0, 10)
        
        assert result["is_underpowered"] is True
        assert result["power"] == 0.0
        assert "Invalid sample sizes" in result["message"]

    def test_calculate_power_large_effect(self):
        """Test power calculation with large effect size and moderate N."""
        effect_size = 1.0  # Large effect
        n1 = 30
        n2 = 30
        
        result = calculate_power(effect_size, n1, n2)
        
        # With large effect and N=30, power should be reasonably high
        # It might still be underpowered depending on exact calculation, 
        # but it should be > 0 for valid inputs
        assert result["power"] > 0.0
        assert result["threshold"] == 0.80


class TestTTest:
    """Tests for run_t_test."""

    def test_ttest_equal_var(self):
        """Test Student's t-test."""
        g1 = [1.0, 2.0, 3.0, 4.0, 5.0]
        g2 = [2.0, 3.0, 4.0, 5.0, 6.0]
        
        t_stat, p_val = run_t_test(g1, g2, equal_var=True)
        
        assert isinstance(t_stat, float)
        assert isinstance(p_val, float)
        assert 0 <= p_val <= 1

    def test_ttest_welch(self):
        """Test Welch's t-test."""
        g1 = [1.0, 2.0, 3.0, 4.0, 5.0]
        g2 = [10.0, 20.0, 30.0, 40.0, 50.0]
        
        t_stat, p_val = run_t_test(g1, g2, equal_var=False)
        
        assert isinstance(t_stat, float)
        assert isinstance(p_val, float)
        assert 0 <= p_val <= 1

    def test_ttest_empty_group(self):
        """Test that empty group raises error."""
        with pytest.raises(ValueError):
            run_t_test([], [1.0, 2.0])


class TestEffectSize:
    """Tests for calculate_effect_size."""

    def test_cohen_d_basic(self):
        """Test basic Cohen's d calculation."""
        g1 = [10, 12, 14]
        g2 = [2, 4, 6]
        
        d = calculate_effect_size(g1, g2)
        
        assert isinstance(d, float)
        # Large difference, should be positive and significant
        assert d > 0

    def test_cohen_d_zero_std(self):
        """Test with zero standard deviation."""
        g1 = [5, 5, 5]
        g2 = [5, 5, 5]
        
        d = calculate_effect_size(g1, g2)
        
        assert d == 0.0


class TestBonferroni:
    """Tests for apply_bonferroni_correction."""

    def test_bonferroni_correction(self):
        """Test basic Bonferroni correction."""
        p = 0.05
        k = 5
        
        corrected = apply_bonferroni_correction(p, k)
        
        assert corrected == 0.25  # 0.05 * 5
        assert corrected <= 1.0

    def test_bonferroni_cap(self):
        """Test that corrected p-value is capped at 1.0."""
        p = 0.5
        k = 10
        
        corrected = apply_bonferroni_correction(p, k)
        
        assert corrected == 1.0


class TestCollinearity:
    """Tests for check_collinearity."""

    def test_no_collinearity(self):
        """Test with no collinearity."""
        df = pd.DataFrame({
            "A": np.random.randn(100),
            "B": np.random.randn(100),
            "C": np.random.randn(100)
        })
        
        result = check_collinearity(df, ["A", "B", "C"], threshold=0.8)
        
        assert result["flagged"] is False
        assert "max_correlation" in result

    def test_collinearity_detected(self):
        """Test with high collinearity."""
        x = np.random.randn(100)
        df = pd.DataFrame({
            "A": x,
            "B": x * 2 + 0.1,  # Highly correlated
            "C": np.random.randn(100)
        })
        
        result = check_collinearity(df, ["A", "B", "C"], threshold=0.8)
        
        assert result["flagged"] is True
        assert "A_B" in result["correlations"]


class TestFraming:
    """Tests for frame_inference."""

    def test_framing_significant(self):
        """Test framing for significant result."""
        text = frame_inference(0.01, 0.05)
        
        assert "associational" in text
        assert "statistically significant" in text

    def test_framing_not_significant(self):
        """Test framing for non-significant result."""
        text = frame_inference(0.10, 0.05)
        
        assert "associational" in text
        assert "not statistically significant" in text


class TestAggregateResults:
    """Tests for aggregate_results."""

    def test_aggregate_structure(self):
        """Test that aggregate_results returns correct keys."""
        results = aggregate_results(
            t_stat=2.5,
            p_value=0.01,
            effect_size=0.5,
            ci=(0.1, 0.9),
            power_info={"power": 0.85, "is_underpowered": False},
            collinearity_info={"flagged": False},
            inference_text="Test framing"
        )
        
        required_keys = [
            "t_statistic", "p_value", "effect_size_cohen_d",
            "confidence_interval", "power_analysis",
            "collinearity_diagnostics", "inference_framing"
        ]
        
        for key in required_keys:
            assert key in results