"""
Unit tests for sensitivity analysis module (T025).
"""
import pytest
import pandas as pd
import numpy as np
from src.reports.sensitivity import (
    get_significant_predictors,
    calculate_jaccard_index,
    perform_threshold_sweep,
    calculate_pairwise_jaccard,
    generate_sensitivity_report,
    run_sensitivity_analysis
)
from pathlib import Path
import tempfile
import json


class TestSignificantPredictors:
    def test_basic_significant_predictors(self):
        """Test basic significant predictor detection."""
        p_values = pd.Series({
            'feature_a': 0.003,
            'feature_b': 0.012,
            'feature_c': 0.045
        })
        result = get_significant_predictors(p_values, 0.01)
        assert result == {'feature_a'}

    def test_empty_result(self):
        """Test when no predictors are significant."""
        p_values = pd.Series({
            'feature_a': 0.1,
            'feature_b': 0.2
        })
        result = get_significant_predictors(p_values, 0.01)
        assert result == set()

    def test_nan_handling(self):
        """Test that NaN p-values are excluded."""
        p_values = pd.Series({
            'feature_a': 0.005,
            'feature_b': np.nan,
            'feature_c': 0.02
        })
        result = get_significant_predictors(p_values, 0.01)
        assert result == {'feature_a'}
        assert 'feature_b' not in result

    def test_all_significant(self):
        """Test when all predictors are significant."""
        p_values = pd.Series({
            'feature_a': 0.001,
            'feature_b': 0.002,
            'feature_c': 0.003
        })
        result = get_significant_predictors(p_values, 0.05)
        assert result == {'feature_a', 'feature_b', 'feature_c'}


class TestJaccardIndex:
    def test_identical_sets(self):
        """Test Jaccard index for identical sets."""
        set_a = {'a', 'b', 'c'}
        set_b = {'a', 'b', 'c'}
        result = calculate_jaccard_index(set_a, set_b)
        assert result == 1.0

    def test_disjoint_sets(self):
        """Test Jaccard index for disjoint sets."""
        set_a = {'a', 'b'}
        set_b = {'c', 'd'}
        result = calculate_jaccard_index(set_a, set_b)
        assert result == 0.0

    def test_partial_overlap(self):
        """Test Jaccard index for partially overlapping sets."""
        set_a = {'a', 'b', 'c'}
        set_b = {'b', 'c', 'd'}
        # Intersection: {b, c} -> 2
        # Union: {a, b, c, d} -> 4
        # Jaccard: 2/4 = 0.5
        result = calculate_jaccard_index(set_a, set_b)
        assert result == 0.5

    def test_both_empty(self):
        """Test Jaccard index when both sets are empty."""
        result = calculate_jaccard_index(set(), set())
        assert result == 0.0

    def test_one_empty(self):
        """Test Jaccard index when one set is empty."""
        result = calculate_jaccard_index({'a', 'b'}, set())
        assert result == 0.0


class TestThresholdSweep:
    def test_basic_sweep(self):
        """Test basic threshold sweep."""
        p_values = pd.Series({
            'feature_a': 0.003,
            'feature_b': 0.012,
            'feature_c': 0.045
        })
        thresholds = [0.01, 0.05]
        results = perform_threshold_sweep(p_values, thresholds)

        assert results[0.01] == {'feature_a'}
        assert results[0.05] == {'feature_a', 'feature_b', 'feature_c'}

    def test_empty_p_values(self):
        """Test sweep with empty p-values."""
        p_values = pd.Series(dtype=float)
        thresholds = [0.01, 0.05]
        results = perform_threshold_sweep(p_values, thresholds)

        assert results[0.01] == set()
        assert results[0.05] == set()


class TestPairwiseJaccard:
    def test_pairwise_calculation(self):
        """Test pairwise Jaccard calculation."""
        threshold_results = {
            0.01: {'feature_a'},
            0.05: {'feature_a', 'feature_b'}
        }
        thresholds = [0.01, 0.05]

        result = calculate_pairwise_jaccard(threshold_results, thresholds)

        # Jaccard({a}, {a, b}) = 1 / 2 = 0.5
        assert (0.01, 0.05) in result
        assert result[(0.01, 0.05)] == 0.5


class TestSensitivityReportGeneration:
    def test_report_structure(self):
        """Test that the report has the correct structure."""
        p_values = pd.Series({
            'feature_a': 0.003,
            'feature_b': 0.012,
            'feature_c': 0.045
        })
        thresholds = [0.005, 0.01, 0.05]

        report = generate_sensitivity_report(p_values, thresholds)

        assert 'thresholds' in report
        assert 'significant_counts' in report
        assert 'delta_variation' in report
        assert 'pairwise_jaccard' in report
        assert 'significant_sets' in report
        assert report['analysis_complete'] is True

    def test_delta_calculation(self):
        """Test that delta variation is calculated correctly."""
        p_values = pd.Series({
            'feature_a': 0.003,
            'feature_b': 0.008,
            'feature_c': 0.045
        })
        thresholds = [0.01, 0.05]

        report = generate_sensitivity_report(p_values, thresholds)

        # At 0.01: {a, b} -> count 2
        # At 0.05: {a, b, c} -> count 3
        # Delta: 3 - 2 = 1
        delta_key = "0.01_0.05"
        assert delta_key in report['delta_variation']
        assert report['delta_variation'][delta_key] == 1

    def test_empty_threshold_sets(self):
        """Test handling of empty significant sets."""
        p_values = pd.Series({
            'feature_a': 0.5,
            'feature_b': 0.6
        })
        thresholds = [0.01, 0.05]

        report = generate_sensitivity_report(p_values, thresholds)

        # Both thresholds should have empty sets
        assert report['significant_counts'][0.01] == 0
        assert report['significant_counts'][0.05] == 0

        # Jaccard of two empty sets should be 0
        jaccard_key = "0.01_0.05"
        assert report['pairwise_jaccard'][jaccard_key] == 0.0


class TestRunSensitivityAnalysis:
    def test_file_output(self):
        """Test that results are saved to file."""
        p_values = pd.Series({
            'feature_a': 0.003,
            'feature_b': 0.012
        })

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "sensitivity_test.json"
            report = run_sensitivity_analysis(p_values, str(output_path))

            assert output_path.exists()

            with open(output_path, 'r') as f:
                saved_data = json.load(f)

            assert 'thresholds' in saved_data
            assert 'analysis_complete' in saved_data