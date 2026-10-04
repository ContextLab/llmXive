"""
Unit tests for the analysis module.
"""
import pytest
import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

from code.analysis.contradiction_analyzer import (
    load_contradiction_log,
    calculate_contradiction_rate,
    verify_contradiction_rate,
    flag_study_if_high_rate,
    run_contradiction_analysis,
    StudyFlagError
)

from code.analysis.statistics import (
    calculate_effect_size,
    power_analysis_two_proportions,
    two_proportion_z_test,
    fisher_exact_test,
    select_statistical_test,
    aggregate_violation_rates,
    StudyInvalidError,
    run_statistical_comparison
)


class TestContradictionAnalyzer:
    def test_calculate_contradiction_rate(self):
        """Test contradiction rate calculation."""
        log_data = {'contradictions': [{'id': 1}, {'id': 2}]}
        rate = calculate_contradiction_rate(log_data, 100)
        assert rate == 2.0
        
    def test_calculate_contradiction_rate_zero_total(self):
        """Test error on zero total scenes."""
        log_data = {'contradictions': []}
        with pytest.raises(ValueError):
            calculate_contradiction_rate(log_data, 0)
            
    def test_verify_contradiction_rate_valid(self):
        """Test valid rate verification."""
        assert verify_contradiction_rate(4.0, 5.0) is True
        assert verify_contradiction_rate(5.0, 5.0) is True
        
    def test_verify_contradiction_rate_invalid(self):
        """Test invalid rate verification."""
        assert verify_contradiction_rate(5.1, 5.0) is False
        
    def test_flag_study_if_high_rate(self):
        """Test flagging study on high rate."""
        with pytest.raises(StudyFlagError):
            flag_study_if_high_rate(6.0, 5.0)
            
    def test_flag_study_if_low_rate(self):
        """Test no flag on low rate."""
        try:
            flag_study_if_high_rate(4.0, 5.0)
        except StudyFlagError:
            pytest.fail("StudyFlagError raised unexpectedly")


class TestStatistics:
    def test_calculate_effect_size(self):
        """Test effect size calculation."""
        effect = calculate_effect_size(0.5, 0.3)
        assert effect > 0
        
    def test_select_statistical_test_fisher(self):
        """Test Fisher test selection for small cells."""
        # x1=1, n1=5, x2=1, n2=5 -> min cell = 1
        assert select_statistical_test(1, 5, 1, 5) == 'fisher'
        
    def test_select_statistical_test_z(self):
        """Test Z-test selection for large cells."""
        # x1=100, n1=500, x2=100, n2=500 -> min cell = 400
        assert select_statistical_test(100, 500, 100, 500) == 'z-test'
        
    def test_two_proportion_z_test(self):
        """Test Z-test calculation."""
        z_stat, p_value = two_proportion_z_test(50, 100, 30, 100)
        assert z_stat != 0
        assert 0 <= p_value <= 1
        
    def test_fisher_exact_test(self):
        """Test Fisher's exact test."""
        odds_ratio, p_value = fisher_exact_test(10, 40, 5, 45)
        assert odds_ratio > 0
        assert 0 <= p_value <= 1
        
    def test_aggregate_violation_rates(self):
        """Test aggregation of violation rates."""
        results = [
            {'group': 'A', 'is_violation': True},
            {'group': 'A', 'is_violation': False},
            {'group': 'B', 'is_violation': True},
            {'group': 'B', 'is_violation': True},
            {'group': 'B', 'is_violation': False}
        ]
        
        agg = aggregate_violation_rates(results)
        
        assert agg['A']['total'] == 2
        assert agg['A']['violations'] == 1
        assert agg['B']['total'] == 3
        assert agg['B']['violations'] == 2
        
    def test_run_statistical_comparison(self):
        """Test statistical comparison between groups."""
        results = [
            {'group': 'Baseline', 'is_violation': True},
            {'group': 'Baseline', 'is_violation': False},
            {'group': 'Experimental', 'is_violation': True},
            {'group': 'Experimental', 'is_violation': True},
            {'group': 'Experimental', 'is_violation': False}
        ]
        
        result = run_statistical_comparison(results, 'Baseline', 'Experimental')
        
        assert 'test_type' in result
        assert 'p_value' in result
        assert result['group1_total'] == 2
        assert result['group2_total'] == 3