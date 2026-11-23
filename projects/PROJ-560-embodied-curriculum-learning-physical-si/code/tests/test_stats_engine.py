import pytest
import numpy as np
from typing import List, Tuple
import pandas as pd
import os
import sys
import json
import tempfile
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from stats_engine import (
    run_t_test,
    calculate_effect_size,
    check_collinearity,
    calculate_power,
    apply_bonferroni_correction,
    detect_multiple_concepts,
    frame_inference
)
from config import INFERENTIAL_FRAMING_STRING

class TestTTest:
    @pytest.fixture
    def sample_data(self):
        """Create sample data for t-test."""
        np.random.seed(42)
        n_embodied = 50
        n_static = 50
        
        # Embodied group: mean gain = 10
        embodied_gain = np.random.normal(loc=10, scale=3, size=n_embodied)
        # Static group: mean gain = 8
        static_gain = np.random.normal(loc=8, scale=3, size=n_static)
        
        data = pd.DataFrame({
            'gain_score': np.concatenate([embodied_gain, static_gain]),
            'instruction_type': ['embodied'] * n_embodied + ['static'] * n_static
        })
        return data

    def test_run_t_test_equal_variance(self, sample_data):
        """Test t-test when variances are equal."""
        # Modify data to have equal variances
        embodied_gain = np.random.normal(loc=10, scale=2, size=50)
        static_gain = np.random.normal(loc=8, scale=2, size=50)
        data = pd.DataFrame({
            'gain_score': np.concatenate([embodied_gain, static_gain]),
            'instruction_type': ['embodied'] * 50 + ['static'] * 50
        })
        
        result = run_t_test(data)
        
        assert 't_statistic' in result
        assert 'p_value' in result
        assert result['test_type'] == 'student'
        assert result['n_embodied'] == 50
        assert result['n_static'] == 50
        # With means 10 and 8, std 2, n=50, we expect a significant difference
        assert result['p_value'] < 0.05

    def test_run_t_test_unequal_variance(self, sample_data):
        """Test Welch's t-test when variances are unequal."""
        embodied_gain = np.random.normal(loc=10, scale=5, size=50)
        static_gain = np.random.normal(loc=8, scale=2, size=50)
        data = pd.DataFrame({
            'gain_score': np.concatenate([embodied_gain, static_gain]),
            'instruction_type': ['embodied'] * 50 + ['static'] * 50
        })
        
        result = run_t_test(data)
        
        assert 't_statistic' in result
        assert 'p_value' in result
        assert result['test_type'] == 'welch'
        assert result['n_embodied'] == 50
        assert result['n_static'] == 50

    def test_t_test_underpowered(self):
        """Test t-test with small sample size (N < 30)."""
        embodied_gain = np.random.normal(loc=10, scale=2, size=10)
        static_gain = np.random.normal(loc=8, scale=2, size=10)
        data = pd.DataFrame({
            'gain_score': np.concatenate([embodied_gain, static_gain]),
            'instruction_type': ['embodied'] * 10 + ['static'] * 10
        })
        
        result = run_t_test(data)
        
        assert result['n_embodied'] == 10
        assert result['n_static'] == 10
        # Should still run, but power will be low (tested in calculate_power)

class TestBonferroniCorrection:
    def test_bonferroni_single_concept(self):
        """Test Bonferroni correction with single concept."""
        result = apply_bonferroni_correction(p_value=0.04, n_concepts=1)
        
        assert result['corrected_p_value'] == 0.04
        assert result['adjusted_alpha'] == 0.05
        assert result['is_significant_after_correction'] == True

    def test_bonferroni_multiple_concepts(self):
        """Test Bonferroni correction with multiple concepts."""
        result = apply_bonferroni_correction(p_value=0.04, n_concepts=3)
        
        assert result['corrected_p_value'] == 0.12 # 0.04 * 3
        assert result['adjusted_alpha'] == pytest.approx(0.0166, rel=0.01)
        assert result['is_significant_after_correction'] == False # 0.12 > 0.0166

class TestEffectSize:
    @pytest.fixture
    def sample_data(self):
        np.random.seed(42)
        n_embodied = 50
        n_static = 50
        embodied_gain = np.random.normal(loc=10, scale=3, size=n_embodied)
        static_gain = np.random.normal(loc=8, scale=3, size=n_static)
        data = pd.DataFrame({
            'gain_score': np.concatenate([embodied_gain, static_gain]),
            'instruction_type': ['embodied'] * n_embodied + ['static'] * n_static
        })
        return data

    def test_calculate_effect_size(self, sample_data):
        result = calculate_effect_size(sample_data)
        
        assert 'cohens_d' in result
        assert 'confidence_interval' in result
        assert len(result['confidence_interval']) == 2
        # Expected d approx (10-8)/3 = 0.66
        assert 0.5 < result['cohens_d'] < 0.8

class TestCollinearity:
    def test_check_collinearity_no_high_corr(self):
        """Test collinearity detection when no high correlation exists."""
        np.random.seed(42)
        data = pd.DataFrame({
            'var1': np.random.normal(0, 1, 100),
            'var2': np.random.normal(0, 1, 100),
            'var3': np.random.normal(0, 1, 100)
        })
        
        result = check_collinearity(data)
        
        assert 'high_correlation_pairs' in result
        assert 'warning' in result
        assert len(result['high_correlation_pairs']) == 0
        assert "No high collinearity" in result['warning']

    def test_check_collinearity_high_corr(self):
        """Test collinearity detection when high correlation exists."""
        np.random.seed(42)
        var1 = np.random.normal(0, 1, 100)
        var2 = var1 * 0.9 + np.random.normal(0, 0.1, 100) # High correlation
        var3 = np.random.normal(0, 1, 100)
        
        data = pd.DataFrame({
            'var1': var1,
            'var2': var2,
            'var3': var3
        })
        
        result = check_collinearity(data)
        
        assert len(result['high_correlation_pairs']) > 0
        assert "High collinearity detected" in result['warning']

class TestPower:
    @pytest.fixture
    def sample_data(self):
        np.random.seed(42)
        n_embodied = 50
        n_static = 50
        embodied_gain = np.random.normal(loc=10, scale=3, size=n_embodied)
        static_gain = np.random.normal(loc=8, scale=3, size=n_static)
        data = pd.DataFrame({
            'gain_score': np.concatenate([embodied_gain, static_gain]),
            'instruction_type': ['embodied'] * n_embodied + ['static'] * n_static
        })
        return data

    def test_calculate_power_sufficient(self, sample_data):
        result = calculate_power(sample_data)
        
        assert 'achieved_power' in result
        assert 'is_underpowered' in result
        # With n=50 per group and d~0.66, power should be > 0.8
        assert result['achieved_power'] > 0.8
        assert result['is_underpowered'] == False

    def test_calculate_power_insufficient(self):
        """Test power calculation with small sample size."""
        np.random.seed(42)
        n_embodied = 10
        n_static = 10
        embodied_gain = np.random.normal(loc=10, scale=3, size=n_embodied)
        static_gain = np.random.normal(loc=8, scale=3, size=n_static)
        data = pd.DataFrame({
            'gain_score': np.concatenate([embodied_gain, static_gain]),
            'instruction_type': ['embodied'] * n_embodied + ['static'] * n_static
        })
        
        result = calculate_power(data)
        
        assert result['is_underpowered'] == True

class TestMultipleConcepts:
    def test_detect_multiple_concepts(self):
        """Test detection of multiple concept columns."""
        data = pd.DataFrame({
            'math_score': np.random.normal(0, 1, 10),
            'physics_score': np.random.normal(0, 1, 10),
            'pre_test_score': np.random.normal(0, 1, 10),
            'post_test_score': np.random.normal(0, 1, 10),
            'gain_score': np.random.normal(0, 1, 10)
        })
        
        result = detect_multiple_concepts(data)
        
        assert 'n_concepts' in result
        assert 'concept_ids' in result
        assert result['n_concepts'] == 2
        assert 'math_score' in result['concept_ids']
        assert 'physics_score' in result['concept_ids']

class TestFraming:
    def test_frame_inference(self):
        """Test that inference framing is correctly applied."""
        results = {
            't_statistic': 2.5,
            'p_value': 0.01
        }
        
        framed_results = frame_inference(results)
        
        assert 'inference_framing' in framed_results
        assert framed_results['inference_framing'] == INFERENTIAL_FRAMING_STRING