import pytest
import numpy as np
import json
import os
import tempfile
from typing import List, Tuple
from src.stats_engine import (
    run_t_test, 
    calculate_effect_size, 
    calculate_confidence_interval, 
    apply_bonferroni_correction, 
    frame_inference, 
    check_collinearity, 
    calculate_power,
    aggregate_results
)
from src.models import AnalysisResult


class TestStatsEngine:
    """Tests for statistical engine functions."""
    
    def test_t_test_equal_var(self):
        """Test t-test with equal variance assumption."""
        g1 = [1.0, 2.0, 3.0]
        g2 = [4.0, 5.0, 6.0]
        t_stat, p_val = run_t_test(g1, g2, use_welch=False)
        assert isinstance(t_stat, float)
        assert isinstance(p_val, float)
        assert 0 <= p_val <= 1
        
    def test_t_test_welch(self):
        """Test Welch's t-test."""
        g1 = [1.0, 2.0, 3.0]
        g2 = [10.0, 20.0, 30.0]
        t_stat, p_val = run_t_test(g1, g2, use_welch=True)
        assert isinstance(t_stat, float)
        assert p_val < 0.05
        
    def test_effect_size(self):
        """Test Cohen's d calculation."""
        g1 = [1.0, 2.0, 3.0]
        g2 = [4.0, 5.0, 6.0]
        d = calculate_effect_size(g1, g2)
        assert isinstance(d, float)
        
    def test_confidence_interval(self):
        """Test confidence interval calculation."""
        g1 = [1.0, 2.0, 3.0]
        g2 = [4.0, 5.0, 6.0]
        ci = calculate_confidence_interval(g1, g2)
        assert len(ci) == 2
        assert ci[0] < ci[1]
        
    def test_bonferroni(self):
        """Test Bonferroni correction."""
        p_vals = [0.01, 0.02, 0.03]
        adjusted = apply_bonferroni_correction(p_vals)
        assert len(adjusted) == 3
        assert all(0 <= p <= 1 for p in adjusted)
        
    def test_frame_inference(self):
        """Test inference framing."""
        result = AnalysisResult(
            t_statistic=2.0,
            p_value=0.05,
            effect_size=0.5,
            confidence_interval=[0.1, 0.9],
            method="t-test"
        )
        framed = frame_inference(result)
        assert framed["finding"] == "associational"
        
    def test_collinearity(self):
        """Test collinearity detection."""
        covariates = [
            {"x": 1.0, "y": 1.0},
            {"x": 2.0, "y": 2.0},
            {"x": 3.0, "y": 3.0}
        ]
        diag = check_collinearity(covariates)
        assert diag["collinearity_detected"] is True
        
    def test_power_calculation(self):
        """Test power calculation."""
        power = calculate_power(effect_size=0.5, n1=50, n2=50)
        assert 0 <= power <= 1
        
    def test_aggregate_results(self):
        """Test result aggregation."""
        result = aggregate_results(
            t_stat=2.0,
            p_val=0.05,
            effect=0.5,
            ci=[0.1, 0.9],
            method="t-test"
        )
        assert isinstance(result, AnalysisResult)
        assert result.associational_framing is True
