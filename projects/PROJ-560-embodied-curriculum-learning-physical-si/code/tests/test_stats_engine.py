import pytest
import numpy as np
import json
import os
import tempfile
from typing import List, Tuple
from src.stats_engine import run_t_test, apply_bonferroni_correction, calculate_effect_size, check_collinearity, confidence_interval, calculate_power, aggregate_results
from src.models import AnalysisResult

class TestStatsEngine:
    def test_run_t_test_welch(self):
        # Create two groups with different variances
        group1 = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        group2 = np.array([10.0, 20.0, 30.0, 40.0, 50.0])
        t_stat, p_val = run_t_test(group1, group2)
        assert isinstance(t_stat, float)
        assert isinstance(p_val, float)
        assert p_val < 0.05 # Should be significant given the large difference

    def test_run_t_test_student(self):
        # Create two groups with similar variances
        group1 = np.random.normal(0, 1, 100)
        group2 = np.random.normal(0.5, 1, 100)
        t_stat, p_val = run_t_test(group1, group2)
        assert isinstance(t_stat, float)
        assert isinstance(p_val, float)

    def test_calculate_effect_size(self):
        group1 = np.array([1.0, 2.0, 3.0])
        group2 = np.array([4.0, 5.0, 6.0])
        d = calculate_effect_size(group1, group2)
        assert isinstance(d, float)
        # Expected d is approx -2.0 (large effect)
        assert abs(d + 2.0) < 0.5

    def test_confidence_interval(self):
        data = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        ci_low, ci_high = confidence_interval(data)
        assert ci_low < np.mean(data) < ci_high

    def test_apply_bonferroni_correction(self):
        alpha = 0.05
        num_tests = 5
        corrected = apply_bonferroni_correction(alpha, num_tests)
        assert corrected == 0.01

    def test_check_collinearity(self):
        # Perfect collinearity
        x = np.array([1, 2, 3, 4, 5])
        y = x * 2
        predictors = {"A": x, "B": y}
        result = check_collinearity(predictors, threshold=0.8)
        assert result["warning"] is True
        assert len(result["collinear_pairs"]) == 1

    def test_calculate_power(self):
        power = calculate_power(effect_size=0.5, n1=50, n2=50)
        assert 0.0 <= power <= 1.0

    def test_aggregate_results(self):
        # Mock data for aggregation
        t_stat = 2.5
        p_val = 0.01
        eff_size = 0.8
        ci = (0.1, 0.9)
        g1_n, g2_n = 50, 50
        g1_mean, g2_mean = 10.0, 12.0

        result = aggregate_results(
            t_stat=t_stat,
            p_value=p_val,
            effect_size=eff_size,
            ci_low=ci[0],
            ci_high=ci[1],
            group1_n=g1_n,
            group2_n=g2_n,
            group1_mean=g1_mean,
            group2_mean=g2_mean,
            alpha=0.05,
            concepts_tested=1
        )

        assert isinstance(result, AnalysisResult)
        assert result.t_statistic == t_stat
        assert result.is_significant is True
        assert "associational" in result.inference_framing["interpretation"]

    def test_aggregate_results_to_json(self):
        result = aggregate_results(
            t_stat=2.5,
            p_value=0.01,
            effect_size=0.8,
            ci_low=0.1,
            ci_high=0.9,
            group1_n=50,
            group2_n=50,
            group1_mean=10.0,
            group2_mean=12.0,
            alpha=0.05,
            concepts_tested=1
        )
        
        json_str = result.to_json()
        parsed = json.loads(json_str)
        
        assert "t_statistic" in parsed
        assert "inference_framing" in parsed
        assert "associational" in parsed["inference_framing"]["interpretation"]