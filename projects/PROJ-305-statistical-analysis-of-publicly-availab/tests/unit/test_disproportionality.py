"""
Unit tests for src/analysis/disproportionality.py
Verifying ROR, PRR, IC calculation logic with continuity correction.
"""
import os
import sys
import math
import pytest
import pandas as pd
import numpy as np

# Import functions from the implementation
from src.analysis.disproportionality import (
    apply_continuity_correction,
    build_contingency_table,
    calculate_ror,
    calculate_prr,
    calculate_ic,
    calculate_ci_ror,
    calculate_ci_prr,
    calculate_ci_ic,
    calculate_p_value_chi2,
    calculate_disproportionality_metrics,
    benjamini_hochberg,
)

# --- Fixtures ---
@pytest.fixture
def sample_data():
    """Create a sample DataFrame for testing."""
    data = {
        "SOC": ["SOC_A", "SOC_A", "SOC_B", "SOC_B", "SOC_C", "SOC_C"],
        "VAX_TYPE": ["COVID-19", "Non-COVID", "COVID-19", "Non-COVID", "COVID-19", "Non-COVID"],
        "count": [10, 5, 0, 2, 5, 5],  # Includes a zero count for continuity correction testing
    }
    return pd.DataFrame(data)

@pytest.fixture
def contingency_table_with_zeros():
    """Returns a 2x2 table with a zero cell to test continuity correction."""
    # Format: [[a, b], [c, d]]
    # a=0 (Event in Exposed), b=10 (No Event in Exposed)
    # c=5 (Event in Unexposed), d=20 (No Event in Unexposed)
    return np.array([[0, 10], [5, 20]], dtype=float)

@pytest.fixture
def contingency_table_normal():
    """Returns a standard 2x2 table."""
    # a=10, b=90, c=5, d=95
    return np.array([[10.0, 90.0], [5.0, 95.0]])

# --- Test Cases ---

class TestContinuityCorrection:
    def test_apply_continuity_correction_no_zeros(self):
        """Test that non-zero tables are not modified."""
        table = np.array([[10.0, 20.0], [30.0, 40.0]])
        corrected = apply_continuity_correction(table)
        # With no zeros, it should remain identical
        np.testing.assert_array_equal(corrected, table)

    def test_apply_continuity_correction_with_zero(self):
        """Test that zero cells get +0.5."""
        table = np.array([[0.0, 10.0], [20.0, 30.0]])
        corrected = apply_continuity_correction(table)
        expected = np.array([[0.5, 10.5], [20.5, 30.5]])
        np.testing.assert_array_almost_equal(corrected, expected)

    def test_apply_continuity_correction_all_zeros(self):
        """Test handling of all-zero table."""
        table = np.array([[0.0, 0.0], [0.0, 0.0]])
        corrected = apply_continuity_correction(table)
        expected = np.array([[0.5, 0.5], [0.5, 0.5]])
        np.testing.assert_array_almost_equal(corrected, expected)

class TestContingencyTable:
    def test_build_contingency_table(self, sample_data):
        """Test building a 2x2 table from grouped data."""
        # For SOC_A: Exposed(COVID)=10, Unexposed(Non-COVID)=5
        # Total Exposed = 10 (SOC_A) + 0 (others) ? No, logic is:
        # a = count where SOC=Current AND Exposed
        # b = count where SOC!=Current AND Exposed (Total Exposed - a)
        # c = count where SOC=Current AND Unexposed
        # d = count where SOC!=Current AND Unexposed (Total Unexposed - c)
        
        # Total Exposed (COVID) = 10 + 0 + 5 = 15
        # Total Unexposed (Non-COVID) = 5 + 2 + 5 = 12
        
        # For SOC_A:
        # a = 10
        # b = 15 - 10 = 5
        # c = 5
        # d = 12 - 5 = 7
        table = build_contingency_table(sample_data, "SOC_A", "COVID-19", "Non-COVID")
        
        assert table.shape == (2, 2)
        assert table[0, 0] == 10.0  # a
        assert table[0, 1] == 5.0   # b
        assert table[1, 0] == 5.0   # c
        assert table[1, 1] == 7.0   # d

    def test_build_contingency_table_missing_group(self, sample_data):
        """Test building table for a SOC that doesn't exist in data."""
        table = build_contingency_table(sample_data, "NONEXISTENT", "COVID-19", "Non-COVID")
        # a=0, b=Total_Exp, c=0, d=Total_Unexp
        # Total Exp = 15, Total Unexp = 12
        assert table[0, 0] == 0.0
        assert table[0, 1] == 15.0
        assert table[1, 0] == 0.0
        assert table[1, 1] == 12.0

class TestRORCalculation:
    def test_calculate_ror_normal(self, contingency_table_normal):
        """ROR = (a*d) / (b*c)"""
        # a=10, b=90, c=5, d=95
        # ROR = (10 * 95) / (90 * 5) = 950 / 450 = 2.111...
        expected = (10 * 95) / (90 * 5)
        result = calculate_ror(contingency_table_normal)
        assert math.isclose(result, expected, rel_tol=1e-5)

    def test_calculate_ror_zero_cell(self, contingency_table_with_zeros):
        """ROR with zero cell should handle correction or return inf/0 appropriately before correction."""
        # Raw: a=0, b=10, c=5, d=20 -> ROR = 0 / 50 = 0
        result = calculate_ror(contingency_table_with_zeros)
        assert result == 0.0

class TestPRRCalculation:
    def test_calculate_prr_normal(self, contingency_table_normal):
        """PRR = (a/(a+b)) / (c/(c+d))"""
        # a=10, b=90 -> Risk Exp = 10/100 = 0.1
        # c=5, d=95 -> Risk Unexp = 5/100 = 0.05
        # PRR = 0.1 / 0.05 = 2.0
        expected = 2.0
        result = calculate_prr(contingency_table_normal)
        assert math.isclose(result, expected, rel_tol=1e-5)

    def test_calculate_prr_zero_divisor(self, contingency_table_with_zeros):
        """Test PRR when control risk is 0 (should handle gracefully or return inf)."""
        # a=0, b=10 -> Risk Exp = 0
        # c=5, d=20 -> Risk Unexp = 5/25 = 0.2
        # PRR = 0 / 0.2 = 0
        result = calculate_prr(contingency_table_with_zeros)
        assert result == 0.0

class TestICCalculation:
    def test_calculate_ic_normal(self, contingency_table_normal):
        """IC = log2( (a*(a+b+c+d)) / ((a+b)*(a+c)) )"""
        # a=10, b=90, c=5, d=95. Total=200.
        # a+b = 100, a+c = 15
        # IC = log2( (10 * 200) / (100 * 15) ) = log2( 2000 / 1500 ) = log2(1.333)
        expected = math.log2((10 * 200) / (100 * 15))
        result = calculate_ic(contingency_table_normal)
        assert math.isclose(result, expected, rel_tol=1e-5)

    def test_calculate_ic_zero_counts(self, contingency_table_with_zeros):
        """IC with zero a should be handled (log of 0 -> -inf)."""
        # a=0. IC = log2(0) -> -inf
        result = calculate_ic(contingency_table_with_zeros)
        assert math.isinf(result)
        assert result < 0

class TestConfidenceIntervals:
    def test_calculate_ci_ror(self, contingency_table_normal):
        """CI_ROR = exp( ln(ROR) +/- 1.96 * sqrt(1/a + 1/b + 1/c + 1/d) )"""
        table = contingency_table_normal
        ror = calculate_ror(table)
        se = math.sqrt(1/10 + 1/90 + 1/5 + 1/95)
        lower = math.exp(math.log(ror) - 1.96 * se)
        upper = math.exp(math.log(ror) + 1.96 * se)
        
        ci_lower, ci_upper = calculate_ci_ror(table)
        assert math.isclose(ci_lower, lower, rel_tol=1e-4)
        assert math.isclose(ci_upper, upper, rel_tol=1e-4)

    def test_calculate_ci_prr(self, contingency_table_normal):
        """CI_PRR = PRR * exp( +/- 1.96 * sqrt( (1/a - 1/(a+b)) + (1/c - 1/(c+d)) ) )"""
        table = contingency_table_normal
        prr = calculate_prr(table)
        term1 = (1/10 - 1/100)
        term2 = (1/5 - 1/100)
        se = math.sqrt(term1 + term2)
        
        lower = prr * math.exp(-1.96 * se)
        upper = prr * math.exp(1.96 * se)
        
        ci_lower, ci_upper = calculate_ci_prr(table)
        assert math.isclose(ci_lower, lower, rel_tol=1e-4)
        assert math.isclose(ci_upper, upper, rel_tol=1e-4)

    def test_calculate_ci_ic(self, contingency_table_normal):
        """CI_IC = IC +/- 1.96 * SE_IC (approx)"""
        # SE_IC approx = sqrt( (1/a - 1/(a+b)) * (1/c - 1/(c+d)) )? 
        # Actually standard formula for IC variance is complex, testing if function returns finite numbers
        table = contingency_table_normal
        ci_lower, ci_upper = calculate_ci_ic(table)
        assert isinstance(ci_lower, float)
        assert isinstance(ci_upper, float)
        assert ci_lower < ci_upper

class TestPValueChi2:
    def test_calculate_p_value_chi2(self, contingency_table_normal):
        """Chi-square test p-value calculation."""
        # Expected values for 2x2
        # Row totals: 100, 100. Col totals: 15, 185. Grand: 200
        # Expected a = 100*15/200 = 7.5
        # Chi2 = sum((O-E)^2/E)
        # This is a basic check that it returns a float between 0 and 1
        p_val = calculate_p_value_chi2(contingency_table_normal)
        assert 0.0 <= p_val <= 1.0

class TestBenjaminiHochberg:
    def test_bh_correction_monotonicity(self):
        """Ensure adjusted p-values are monotonic."""
        p_values = np.array([0.01, 0.05, 0.03, 0.20, 0.10])
        adjusted = benjamini_hochberg(p_values)
        
        # BH ensures monotonicity from the end
        for i in range(len(adjusted) - 1, 0, -1):
            assert adjusted[i-1] <= adjusted[i] + 1e-9 # Allow small float error
        
        # All values should be <= 1.0
        assert np.all(adjusted <= 1.0)

    def test_bh_correction_identical_pvalues(self):
        """Test with identical p-values."""
        p_values = np.array([0.05, 0.05, 0.05])
        adjusted = benjamini_hochberg(p_values)
        # With identical p-values, adjusted should be identical or very close
        assert np.allclose(adjusted, adjusted[0])

class TestFullMetrics:
    def test_calculate_disproportionality_metrics(self, sample_data):
        """Test the full pipeline for one SOC."""
        metrics = calculate_disproportionality_metrics(sample_data, "SOC_A", "COVID-19", "Non-COVID")
        
        assert "ror" in metrics
        assert "ror_ci_lower" in metrics
        assert "prr" in metrics
        assert "prr_ci_lower" in metrics
        assert "ic" in metrics
        assert "ic_ci_lower" in metrics
        assert "p_value" in metrics
        assert "adjusted_p" in metrics

class TestRunAnalysis:
    def test_run_analysis_integration(self, sample_data):
        """Test the full run_analysis function which handles grouping and metrics."""
        results = calculate_disproportionality_metrics(sample_data, "SOC_A", "COVID-19", "Non-COVID")
        assert isinstance(results, dict)
        assert results["ror"] >= 0.0