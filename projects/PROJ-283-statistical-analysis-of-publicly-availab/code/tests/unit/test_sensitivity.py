import pytest
import pandas as pd
import numpy as np
from src.reports.sensitivity import (
    calculate_jaccard_index,
    get_significant_predictors,
    perform_threshold_sweep,
    generate_sensitivity_report
)
from pathlib import Path
import tempfile
import json

class TestJaccardIndex:
    def test_identical_sets(self):
        set_a = {"A", "B", "C"}
        set_b = {"A", "B", "C"}
        assert calculate_jaccard_index(set_a, set_b) == 1.0

    def test_disjoint_sets(self):
        set_a = {"A", "B"}
        set_b = {"C", "D"}
        assert calculate_jaccard_index(set_a, set_b) == 0.0

    def test_partial_overlap(self):
        set_a = {"A", "B", "C"}
        set_b = {"B", "C", "D"}
        # Intersection: {B, C} = 2
        # Union: {A, B, C, D} = 4
        assert calculate_jaccard_index(set_a, set_b) == 0.5

    def test_both_empty(self):
        assert calculate_jaccard_index(set(), set()) == 1.0

    def test_one_empty(self):
        assert calculate_jaccard_index({"A"}, set()) == 0.0

class TestSignificantPredictors:
    def test_basic_threshold(self):
        p_values = pd.Series({
            "feat_A": 0.01,
            "feat_B": 0.04,
            "feat_C": 0.06,
            "feat_D": 0.001
        })
        significant = get_significant_predictors(p_values, 0.05)
        assert significant == {"feat_A", "feat_B", "feat_D"}
        assert "feat_C" not in significant

    def test_no_significant(self):
        p_values = pd.Series({
            "feat_A": 0.1,
            "feat_B": 0.2
        })
        significant = get_significant_predictors(p_values, 0.05)
        assert len(significant) == 0

    def test_all_significant(self):
        p_values = pd.Series({
            "feat_A": 0.001,
            "feat_B": 0.002
        })
        significant = get_significant_predictors(p_values, 0.05)
        assert len(significant) == 2

    def test_empty_series(self):
        p_values = pd.Series(dtype=float)
        significant = get_significant_predictors(p_values, 0.05)
        assert len(significant) == 0

class TestThresholdSweep:
    def test_sweep_basic(self):
        p_values = pd.Series({
            "feat_A": 0.001,
            "feat_B": 0.008,
            "feat_C": 0.02,
            "feat_D": 0.04,
            "feat_E": 0.06
        })
        thresholds = [0.005, 0.01, 0.05]
        results, sets = perform_threshold_sweep(p_values, thresholds)
        
        # Check 0.005: only feat_A
        assert results[0.005]['significant_count'] == 1
        assert "feat_A" in results[0.005]['significant_predictors']
        
        # Check 0.01: feat_A, feat_B
        assert results[0.01]['significant_count'] == 2
        
        # Check 0.05: feat_A, feat_B, feat_C, feat_D
        assert results[0.05]['significant_count'] == 4

    def test_delta_calculation(self):
        p_values = pd.Series({
            "feat_A": 0.001,
            "feat_B": 0.008,
            "feat_C": 0.02
        })
        thresholds = [0.005, 0.01, 0.05]
        results, _ = perform_threshold_sweep(p_values, thresholds)
        
        # First threshold has no delta
        assert results[0.005]['delta'] is None
        
        # Subsequent thresholds have delta
        assert results[0.01]['delta'] == 1  # 2 - 1
        assert results[0.05]['delta'] == 1  # 3 - 2

class TestSensitivityReportGeneration:
    def test_report_structure(self):
        p_values = pd.Series({
            "feat_A": 0.001,
            "feat_B": 0.008,
            "feat_C": 0.02,
            "feat_D": 0.04,
            "feat_E": 0.06
        })
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "sensitivity_test.json"
            report = generate_sensitivity_report(p_values, output_path)
            
            # Check file exists
            assert output_path.exists()
            
            # Check report structure
            assert 'thresholds_analyzed' in report
            assert 'sweep_results' in report
            assert 'jaccard_indices' in report
            assert 'total_predictors' in report
            assert 'analysis_summary' in report
            
            # Check Jaccard indices exist
            assert len(report['jaccard_indices']) > 0
            assert 'Jaccard(0.005, 0.01)' in report['jaccard_indices']
            assert 'Jaccard(0.01, 0.05)' in report['jaccard_indices']
            assert 'Jaccard(0.005, 0.05)' in report['jaccard_indices']
            
            # Verify file content
            with open(output_path, 'r') as f:
                saved_report = json.load(f)
                assert saved_report == report

    def test_report_with_no_significant(self):
        p_values = pd.Series({
            "feat_A": 0.1,
            "feat_B": 0.2
        })
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "sensitivity_test.json"
            report = generate_sensitivity_report(p_values, output_path)
            
            assert report['sweep_results'][0.05]['significant_count'] == 0
            assert report['sweep_results'][0.01]['significant_count'] == 0
            assert report['sweep_results'][0.005]['significant_count'] == 0
            
            # Jaccard index for empty sets should be 1.0
            assert report['jaccard_indices']['Jaccard(0.005, 0.01)'] == 1.0