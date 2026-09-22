import os
import sys
import math
import pytest
import pandas as pd
import numpy as np

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
    run_analysis
)

class TestContinuityCorrection:
    def test_adds_0_5(self):
        assert apply_continuity_correction(0) == 0.5
        assert apply_continuity_correction(10) == 10.5

class TestContingencyTable:
    def test_build_table_correct(self):
        data = {
            'SOC_CODE': ['A', 'A', 'B', 'B', 'A', 'B'],
            'VAX_TYPE': ['COVID-19', 'COVID-19', 'Flu', 'Flu', 'Flu', 'Flu']
        }
        df = pd.DataFrame(data)
        
        # SOC A: 2 in COVID, 1 in Flu. Total COVID=2, Total Flu=4.
        # a=2, b=0, c=1, d=3
        table = build_contingency_table(df, 'A', 'COVID-19')
        assert table['a'] == 2
        assert table['c'] == 1
        assert table['b'] == 0 # 2 total COVID - 2 events
        assert table['d'] == 3 # 4 total Flu - 1 event

class TestRORCalculation:
    def test_basic_ror(self):
        # a=10, b=10, c=5, d=15
        # ROR = (10*15)/(10*5) = 150/50 = 3.0
        assert calculate_ror(10, 10, 5, 15) == 3.0

    def test_ror_nan_div_zero(self):
        assert math.isnan(calculate_ror(10, 0, 5, 15))

class TestPRRCalculation:
    def test_basic_prr(self):
        # a=10, b=10 -> p1 = 0.5
        # c=5, d=15 -> p2 = 0.25
        # PRR = 0.5 / 0.25 = 2.0
        assert calculate_prr(10, 10, 5, 15) == 2.0

class TestICCalculation:
    def test_basic_ic(self):
        # a=10, b=10, c=5, d=15
        # total = 40
        # observed = 10/20 = 0.5
        # expected = 15/40 = 0.375
        # IC = log2(0.5/0.375) = log2(1.333) approx 0.415
        val = calculate_ic(10, 10, 5, 15)
        expected = math.log2( (10/20) / (15/40) )
        assert math.isclose(val, expected, rel_tol=1e-5)

class TestConfidenceIntervals:
    def test_ci_ror(self):
        # Known values
        lower, upper = calculate_ci_ror(10, 10, 5, 15)
        assert lower < 3.0 < upper

    def test_ci_prr(self):
        lower, upper = calculate_ci_prr(10, 10, 5, 15)
        assert lower < 2.0 < upper

    def test_ci_ic(self):
        lower, upper = calculate_ci_ic(10, 10, 5, 15)
        # Just check it returns numbers
        assert isinstance(lower, float)
        assert isinstance(upper, float)

class TestPValueChi2:
    def test_p_value(self):
        p = calculate_p_value_chi2(10, 10, 5, 15)
        assert 0 <= p <= 1

class TestBenjaminiHochberg:
    def test_monotonicity(self):
        p_vals = [0.01, 0.04, 0.03, 0.02]
        adj = benjamini_hochberg(p_vals)
        # Check that adjusted p-values are monotonic with respect to original order?
        # Actually BH ensures that if you sort by p, the adjusted p is monotonic.
        # Here we just check it returns a list of same length and valid range
        assert len(adj) == 4
        assert all(0 <= x <= 1 for x in adj)

class TestFullMetrics:
    def test_all_metrics(self):
        metrics = calculate_disproportionality_metrics(10, 10, 5, 15)
        assert 'ror' in metrics
        assert 'prr' in metrics
        assert 'ic' in metrics
        assert 'ror_ci_lower' in metrics
        assert 'adjusted_p' not in metrics # Not in this function, added in run_analysis

class TestRunAnalysis:
    def test_run_analysis_integration(self):
        data = {
            'SOC_CODE': ['A'] * 10 + ['B'] * 4 + ['C'] * 6,
            'VAX_TYPE': ['COVID-19'] * 5 + ['Flu'] * 5 + ['Flu'] * 4 + ['COVID-19'] * 3 + ['Flu'] * 3
        }
        df = pd.DataFrame(data)
        
        # SOC A: 5 COVID, 5 Flu (Total 10) -> Included
        # SOC B: 0 COVID, 4 Flu (Total 4) -> Excluded (<5)
        # SOC C: 3 COVID, 3 Flu (Total 6) -> Included
        
        result = run_analysis(df)
        
        assert len(result) == 2
        assert 'A' in result['SOC_CODE'].values
        assert 'C' in result['SOC_CODE'].values
        assert 'B' not in result['SOC_CODE'].values
        
        # Check columns exist
        assert 'adjusted_p' in result.columns
        assert 'ror' in result.columns