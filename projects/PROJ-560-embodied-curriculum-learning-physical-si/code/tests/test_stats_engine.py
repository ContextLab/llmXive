import pytest
import numpy as np
import json
import os
import tempfile
from typing import List, Tuple
import pandas as pd

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

class TestStatsEngine:
    @pytest.fixture
    def sample_data(self):
        """Generate sample data for testing."""
        np.random.seed(42)
        group1 = np.random.normal(loc=10, scale=2, size=50)
        group2 = np.random.normal(loc=12, scale=2, size=50)
        return group1, group2

    @pytest.fixture
    def ancova_data(self):
        """Generate data for ANCOVA testing."""
        np.random.seed(42)
        n = 100
        pre_scores = np.random.normal(loc=50, scale=10, size=n)
        instruction_type = np.random.choice(['static', 'embodied'], size=n)
        # Simulate post scores with a slight effect for embodied
        post_scores = 0.5 * pre_scores + 20 + np.where(instruction_type == 'embodied', 5, 0) + np.random.normal(0, 5, size=n)
        df = pd.DataFrame({
            'pre_test_score': pre_scores,
            'instruction_type': instruction_type,
            'post_test_score': post_scores
        })
        return df

    def test_t_test_basic(self, sample_data):
        """Test basic t-test functionality."""
        g1, g2 = sample_data
        t_stat, p_val = run_t_test(g1, g2)
        assert isinstance(t_stat, float)
        assert isinstance(p_val, float)
        assert 0 <= p_val <= 1

    def test_t_test_empty_groups(self):
        """Test t-test with empty groups raises error."""
        with pytest.raises(ValueError):
            run_t_test([], [1, 2, 3])

    def test_ancova_basic(self, ancova_data):
        """Test basic ANCOVA functionality."""
        result = run_ancova(None, "post_test_score ~ pre_test_score + C(instruction_type)", ancova_data)
        assert "f_statistic" in result
        assert "p_value" in result
        assert isinstance(result["f_statistic"], float)
        assert isinstance(result["p_value"], float)

    def test_calculate_effect_size(self, sample_data):
        """Test Cohen's d calculation."""
        g1, g2 = sample_data
        d = calculate_effect_size(g1, g2)
        assert isinstance(d, float)
        # With a known difference of 2 and std of 2, d should be around 1.0
        assert 0.5 < d < 1.5

    def test_calculate_confidence_interval(self):
        """Test confidence interval calculation."""
        ci = calculate_confidence_interval(effect_size=0.5, n1=50, n2=50)
        assert isinstance(ci, tuple)
        assert len(ci) == 2
        assert ci[0] < 0.5 < ci[1]

    def test_bonferroni_correction(self):
        """Test Bonferroni correction."""
        p_values = [0.01, 0.04, 0.06]
        adjusted = apply_bonferroni_correction(p_values)
        assert len(adjusted) == 3
        assert adjusted[0] == 0.03 # 0.01 * 3
        assert adjusted[1] == 0.12 # 0.04 * 3
        assert adjusted[2] == 1.0  # 0.06 * 3 > 1

    def test_collinearity_detection(self):
        """Test collinearity detection."""
        df = pd.DataFrame({
            'x1': [1, 2, 3, 4, 5],
            'x2': [2, 4, 6, 8, 10], # Perfectly correlated
            'x3': [1, 3, 2, 4, 3]
        })
        result = check_collinearity(df, ['x1', 'x2', 'x3'], threshold=0.8)
        assert result["collinear"] is True
        assert len(result["problematic_pairs"]) > 0

    def test_calculate_power_adequate(self):
        """Test power calculation for adequate power."""
        # Large effect, large sample
        result = calculate_power(effect_size=0.8, n1=100, n2=100)
        assert result["power"] > 0.8
        assert result["underpowered"] is False

    def test_calculate_power_underpowered(self):
        """Test power calculation for underpowered result (FR-007)."""
        # Small effect, small sample
        result = calculate_power(effect_size=0.2, n1=10, n2=10)
        assert result["underpowered"] is True
        assert result["power"] < 0.8

    def test_frame_inference(self):
        """Test inference framing."""
        results = {"key": "value"}
        framed = frame_inference(results)
        assert framed["inference_framing"] == "associational"
        assert "methodological_caveats" in framed

    def test_aggregate_results(self):
        """Test aggregation of all results."""
        ancova = {"f_statistic": 10.0, "p_value": 0.001}
        t_test = (2.5, 0.01)
        effect = 0.5
        ci = (0.1, 0.9)
        power = {"power": 0.9, "underpowered": False}
        collinearity = {"collinear": False}
        framing = {"inference_framing": "associational"}
        
        combined = aggregate_results(ancova, t_test, effect, ci, power, collinearity, framing)
        
        assert "ancova" in combined
        assert "t_test" in combined
        assert "effect_size_cohen_d" in combined
        assert "confidence_interval" in combined
        assert "power_analysis" in combined
        assert "inference_framing" in combined