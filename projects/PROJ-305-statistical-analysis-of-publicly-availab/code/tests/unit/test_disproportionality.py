"""
Unit tests for disproportionality analysis calculations.
Tests ROR, PRR, IC, confidence intervals, and continuity correction.
"""
import os
import sys
import math
import pytest
import pandas as pd
import numpy as np
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from src.analysis.disproportionality import (
    apply_continuity_correction,
    build_contingency_table,
    calculate_ror,
    calculate_prr,
    calculate_ic,
    calculate_p_value_chi2,
    calculate_ci_ror,
    calculate_ci_prr,
    calculate_ci_ic,
    calculate_disproportionality_metrics,
    benjamini_hochberg,
    run_analysis
)


class TestContinuityCorrection:
    """Tests for continuity correction functionality."""
    
    def test_apply_continuity_correction_basic(self):
        """Test that 0.5 is added to all cells."""
        a, b, c, d = 10, 20, 15, 25
        corrected = apply_continuity_correction(a, b, c, d)
        
        assert corrected == (10.5, 20.5, 15.5, 25.5)
    
    def test_apply_continuity_correction_zeroes(self):
        """Test continuity correction with zero values."""
        a, b, c, d = 0, 0, 0, 0
        corrected = apply_continuity_correction(a, b, c, d)
        
        assert corrected == (0.5, 0.5, 0.5, 0.5)


class TestContingencyTable:
    """Tests for contingency table building."""
    
    def test_build_contingency_table_basic(self):
        """Test basic contingency table construction."""
        data = {
            'VAX_TYPE_GROUP': ['COVID-19'] * 10 + ['Non-COVID'] * 10,
            'SOC_CODE': ['SOC001'] * 5 + ['SOC002'] * 5 + 
                        ['SOC001'] * 3 + ['SOC002'] * 7
        }
        df = pd.DataFrame(data)
        
        table = build_contingency_table(df, 'SOC001')
        
        # Expected: a=5 (COVID+SOC001), b=5 (COVID+not SOC001)
        #           c=3 (Non-COVID+SOC001), d=7 (Non-COVID+not SOC001)
        assert table['a'] == 5
        assert table['b'] == 5
        assert table['c'] == 3
        assert table['d'] == 7
    
    def test_build_contingency_table_no_matches(self):
        """Test table when no matches exist."""
        data = {
            'VAX_TYPE_GROUP': ['COVID-19'] * 5 + ['Non-COVID'] * 5,
            'SOC_CODE': ['SOC001'] * 5 + ['SOC002'] * 5
        }
        df = pd.DataFrame(data)
        
        table = build_contingency_table(df, 'SOC003')
        
        assert table['a'] == 0
        assert table['b'] == 5
        assert table['c'] == 0
        assert table['d'] == 5


class TestRORCalculation:
    """Tests for Reporting Odds Ratio calculation."""
    
    def test_calculate_ror_basic(self):
        """Test basic ROR calculation."""
        # a=10, b=10, c=5, d=25
        # ROR = (10*25) / (10*5) = 250/50 = 5.0
        ror = calculate_ror(10, 10, 5, 25)
        assert math.isclose(ror, 5.0, rel_tol=1e-9)
    
    def test_calculate_ror_equal_odds(self):
        """Test ROR when odds are equal (should be 1.0)."""
        # a=10, b=10, c=10, d=10
        # ROR = (10*10) / (10*10) = 1.0
        ror = calculate_ror(10, 10, 10, 10)
        assert math.isclose(ror, 1.0, rel_tol=1e-9)
    
    def test_calculate_ror_zero_denominator(self):
        """Test ROR with zero in denominator (after correction, this shouldn't happen)."""
        # With continuity correction, we should never have zero
        ror = calculate_ror(0.5, 0.5, 0.5, 0.5)
        assert math.isclose(ror, 1.0, rel_tol=1e-9)


class TestPRRCalculation:
    """Tests for Proportional Reporting Ratio calculation."""
    
    def test_calculate_prr_basic(self):
        """Test basic PRR calculation."""
        # a=10, b=10, c=5, d=25
        # p1 = 10/20 = 0.5
        # p2 = 5/30 = 0.1667
        # PRR = 0.5 / 0.1667 = 3.0
        prr = calculate_prr(10, 10, 5, 25)
        assert math.isclose(prr, 3.0, rel_tol=1e-9)
    
    def test_calculate_prr_equal_rates(self):
        """Test PRR when rates are equal (should be 1.0)."""
        # a=10, b=10, c=10, d=10
        # p1 = 10/20 = 0.5
        # p2 = 10/20 = 0.5
        # PRR = 1.0
        prr = calculate_prr(10, 10, 10, 10)
        assert math.isclose(prr, 1.0, rel_tol=1e-9)


class TestICCalculation:
    """Tests for Information Component calculation."""
    
    def test_calculate_ic_basic(self):
        """Test basic IC calculation."""
        # a=10, b=10, c=5, d=25
        # total = 50
        # observed = 10/20 = 0.5
        # expected = 15/50 = 0.3
        # IC = log2(0.5/0.3) = log2(1.667) ≈ 0.737
        ic = calculate_ic(10, 10, 5, 25)
        expected = math.log2(0.5 / 0.3)
        assert math.isclose(ic, expected, rel_tol=1e-6)
    
    def test_calculate_ic_equal_rates(self):
        """Test IC when observed equals expected (should be 0)."""
        # a=10, b=10, c=10, d=10
        # observed = 10/20 = 0.5
        # expected = 20/40 = 0.5
        # IC = log2(1) = 0
        ic = calculate_ic(10, 10, 10, 10)
        assert math.isclose(ic, 0.0, rel_tol=1e-9)


class TestConfidenceIntervals:
    """Tests for confidence interval calculations."""
    
    def test_calculate_ci_ror_basic(self):
        """Test ROR confidence interval calculation."""
        # With a=10, b=10, c=5, d=25
        ci_lower, ci_upper = calculate_ci_ror(10, 10, 5, 25)
        
        assert ci_lower > 0
        assert ci_upper > ci_lower
        assert ci_lower < 5.0 < ci_upper  # ROR should be in CI
    
    def test_calculate_ci_prr_basic(self):
        """Test PRR confidence interval calculation."""
        ci_lower, ci_upper = calculate_ci_prr(10, 10, 5, 25)
        
        assert ci_lower > 0
        assert ci_upper > ci_lower
        assert ci_lower < 3.0 < ci_upper  # PRR should be in CI
    
    def test_calculate_ci_ic_basic(self):
        """Test IC confidence interval calculation."""
        ci_lower, ci_upper = calculate_ci_ic(10, 10, 5, 25)
        
        assert ci_lower < ci_upper


class TestPValueChi2:
    """Tests for Chi-squared p-value calculation."""
    
    def test_calculate_p_value_chi2_basic(self):
        """Test basic p-value calculation."""
        p_value = calculate_p_value_chi2(10, 10, 5, 25)
        
        assert 0.0 <= p_value <= 1.0
    
    def test_calculate_p_value_chi2_no_difference(self):
        """Test p-value when there's no difference (should be high)."""
        p_value = calculate_p_value_chi2(10, 10, 10, 10)
        
        assert p_value > 0.5  # No difference should give high p-value


class TestBenjaminiHochberg:
    """Tests for Benjamini-Hochberg FDR correction."""
    
    def test_bh_correction_basic(self):
        """Test basic BH correction."""
        p_values = [0.01, 0.03, 0.05, 0.07, 0.10]
        adjusted = benjamini_hochberg(p_values)
        
        assert len(adjusted) == 5
        assert all(0.0 <= p <= 1.0 for p in adjusted)
    
    def test_bh_correction_monotonic(self):
        """Test that adjusted p-values are monotonically increasing."""
        p_values = [0.05, 0.01, 0.03, 0.07, 0.02]
        adjusted = benjamini_hochberg(p_values)
        
        # Check monotonicity
        sorted_indices = sorted(range(len(p_values)), key=lambda i: p_values[i])
        sorted_adjusted = [adjusted[i] for i in sorted_indices]
        
        for i in range(len(sorted_adjusted) - 1):
            assert sorted_adjusted[i] <= sorted_adjusted[i + 1]
    
    def test_bh_correction_empty(self):
        """Test BH correction with empty list."""
        adjusted = benjamini_hochberg([])
        assert adjusted == []


class TestFullMetrics:
    """Tests for complete disproportionality metrics calculation."""
    
    def test_calculate_disproportionality_metrics(self):
        """Test full metrics calculation."""
        data = {
            'VAX_TYPE_GROUP': ['COVID-19'] * 20 + ['Non-COVID'] * 20,
            'SOC_CODE': ['SOC001'] * 10 + ['SOC002'] * 10 + 
                        ['SOC001'] * 5 + ['SOC002'] * 15
        }
        df = pd.DataFrame(data)
        
        metrics = calculate_disproportionality_metrics(df, 'SOC001')
        
        assert 'ror' in metrics
        assert 'prr' in metrics
        assert 'ic' in metrics
        assert 'p_value' in metrics
        assert 'ror_ci_lower' in metrics
        assert 'ror_ci_upper' in metrics
        assert metrics['a'] == 10
        assert metrics['b'] == 10
        assert metrics['c'] == 5
        assert metrics['d'] == 15
    
    def test_calculate_disproportionality_metrics_zero_counts(self):
        """Test metrics with zero counts (should handle gracefully)."""
        data = {
            'VAX_TYPE_GROUP': ['COVID-19'] * 10 + ['Non-COVID'] * 10,
            'SOC_CODE': ['SOC001'] * 10 + ['SOC002'] * 10
        }
        df = pd.DataFrame(data)
        
        # SOC003 doesn't exist, so all counts should be 0 (after correction: 0.5)
        metrics = calculate_disproportionality_metrics(df, 'SOC003')
        
        assert metrics['a'] == 0
        assert metrics['b'] == 10
        assert metrics['c'] == 0
        assert metrics['d'] == 10


class TestRunAnalysis:
    """Tests for full analysis pipeline."""
    
    def test_run_analysis_basic(self):
        """Test basic analysis run."""
        data = {
            'VAX_TYPE_GROUP': ['COVID-19'] * 50 + ['Non-COVID'] * 50,
            'SOC_CODE': ['SOC001'] * 20 + ['SOC002'] * 15 + ['SOC003'] * 15 +
                        ['SOC001'] * 10 + ['SOC002'] * 20 + ['SOC003'] * 20
        }
        df = pd.DataFrame(data)
        
        results = run_analysis(df, min_reports=5)
        
        assert not results.empty
        assert 'ror' in results.columns
        assert 'prr' in results.columns
        assert 'ic' in results.columns
        assert 'adjusted_p' in results.columns
        assert 'is_signal' in results.columns
        assert len(results) == 3  # Three SOCs with >= 5 reports
    
    def test_run_analysis_min_reports_filter(self):
        """Test that SOCs with fewer than min_reports are excluded."""
        data = {
            'VAX_TYPE_GROUP': ['COVID-19'] * 20 + ['Non-COVID'] * 20,
            'SOC_CODE': ['SOC001'] * 10 + ['SOC002'] * 5 + ['SOC003'] * 3 +
                        ['SOC001'] * 5 + ['SOC002'] * 10 + ['SOC003'] * 2
        }
        df = pd.DataFrame(data)
        
        # SOC001: 15, SOC002: 15, SOC003: 5
        results = run_analysis(df, min_reports=10)
        
        assert len(results) == 2  # Only SOC001 and SOC002
        assert 'SOC003' not in results['soc_code'].values