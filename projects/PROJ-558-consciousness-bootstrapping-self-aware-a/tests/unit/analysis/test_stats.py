"""
Unit tests for statistical analysis functions in code/analysis/stats.py.
Extends existing tests with coverage for sensitivity analysis, error handling,
and edge cases for statistical metrics.
"""
import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import numpy as np
import pytest
from scipy import stats as scipy_stats

from code.analysis.stats import (
    StatisticalTestResult,
    StatisticalReport,
    load_evaluation_results_from_json,
    filter_converged_seeds,
    calculate_percentage_difference,
    run_paired_ttest,
    calculate_cohen_d,
    calculate_confidence_interval,
    bonferroni_correction,
    generate_statistical_report,
    save_statistical_report,
    run_sensitivity_analysis,
    main,
)
from code.config import Config


class TestStatisticalTestResult:
    """Tests for the StatisticalTestResult dataclass."""

    def test_creation(self):
        """Test basic creation of StatisticalTestResult."""
        result = StatisticalTestResult(
            test_name="paired_ttest",
            statistic=2.5,
            p_value=0.02,
            effect_size=0.8,
            significant=True,
            description="Test description"
        )
        assert result.test_name == "paired_ttest"
        assert result.statistic == 2.5
        assert result.p_value == 0.02
        assert result.effect_size == 0.8
        assert result.significant is True
        assert result.description == "Test description"

    def test_to_dict(self):
        """Test conversion to dictionary."""
        result = StatisticalTestResult(
            test_name="test",
            statistic=1.0,
            p_value=0.05,
            effect_size=0.5,
            significant=False,
            description="Desc"
        )
        d = result.to_dict()
        assert d["test_name"] == "test"
        assert d["statistic"] == 1.0
        assert d["p_value"] == 0.05
        assert d["effect_size"] == 0.5
        assert d["significant"] is False

    def test_from_dict(self):
        """Test creation from dictionary."""
        d = {
            "test_name": "test",
            "statistic": 1.0,
            "p_value": 0.05,
            "effect_size": 0.5,
            "significant": False,
            "description": "Desc"
        }
        result = StatisticalTestResult.from_dict(d)
        assert result.test_name == "test"
        assert result.statistic == 1.0
        assert result.p_value == 0.05


class TestStatisticalReport:
    """Tests for the StatisticalReport dataclass."""

    def test_creation(self):
        """Test basic creation of StatisticalReport."""
        report = StatisticalReport(
            project_id="PROJ-558",
            description="Test report",
            tests=[],
            summary_stats={},
            raw_metrics_file="metrics.json",
            threshold_sensitivity=None
        )
        assert report.project_id == "PROJ-558"
        assert report.description == "Test report"
        assert report.tests == []
        assert report.summary_stats == {}

    def test_to_dict(self):
        """Test conversion to dictionary."""
        report = StatisticalReport(
            project_id="PROJ-558",
            description="Test",
            tests=[],
            summary_stats={"mean": 1.0},
            raw_metrics_file="metrics.json",
            threshold_sensitivity={"threshold": 0.5}
        )
        d = report.to_dict()
        assert d["project_id"] == "PROJ-558"
        assert d["description"] == "Test"
        assert d["summary_stats"]["mean"] == 1.0
        assert d["threshold_sensitivity"]["threshold"] == 0.5


class TestLoadEvaluationResultsFromJson:
    """Tests for loading evaluation results from JSON files."""

    def test_load_valid_json(self):
        """Test loading a valid JSON file with evaluation results."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            data = {
                "seed": 42,
                "model_type": "recursive",
                "metrics": {
                    "self_consistency": 0.85,
                    "error_detection_accuracy": 0.72,
                    "converged": True
                }
            }
            json.dump(data, f)
            f.flush()

            result = load_evaluation_results_from_json(f.name)
            assert result["seed"] == 42
            assert result["model_type"] == "recursive"
            assert result["metrics"]["self_consistency"] == 0.85
            assert result["metrics"]["converged"] is True

        os.unlink(f.name)

    def test_load_invalid_json(self):
        """Test loading an invalid JSON file raises an error."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write("not valid json")
            f.flush()

            with pytest.raises(json.JSONDecodeError):
                load_evaluation_results_from_json(f.name)

        os.unlink(f.name)

    def test_load_nonexistent_file(self):
        """Test loading a nonexistent file raises an error."""
        with pytest.raises(FileNotFoundError):
            load_evaluation_results_from_json("nonexistent.json")


class TestFilterConvergedSeeds:
    """Tests for filtering converged seeds."""

    def test_filter_converged(self):
        """Test filtering only converged seeds."""
        results = [
            {"seed": 1, "metrics": {"converged": True}},
            {"seed": 2, "metrics": {"converged": False}},
            {"seed": 3, "metrics": {"converged": True}},
            {"seed": 4, "metrics": {}},  # No converged key
        ]

        converged = filter_converged_seeds(results)
        assert len(converged) == 2
        assert all(r["metrics"]["converged"] is True for r in converged)

    def test_filter_all_converged(self):
        """Test when all seeds are converged."""
        results = [
            {"seed": 1, "metrics": {"converged": True}},
            {"seed": 2, "metrics": {"converged": True}},
        ]

        converged = filter_converged_seeds(results)
        assert len(converged) == 2

    def test_filter_none_converged(self):
        """Test when no seeds are converged."""
        results = [
            {"seed": 1, "metrics": {"converged": False}},
            {"seed": 2, "metrics": {"converged": False}},
        ]

        converged = filter_converged_seeds(results)
        assert len(converged) == 0

    def test_filter_missing_key(self):
        """Test handling of missing 'converged' key."""
        results = [
            {"seed": 1, "metrics": {}},
            {"seed": 2, "metrics": {"converged": True}},
        ]

        converged = filter_converged_seeds(results)
        assert len(converged) == 1
        assert converged[0]["seed"] == 2


class TestCalculatePercentageDifference:
    """Tests for calculating percentage difference between groups."""

    def test_basic_calculation(self):
        """Test basic percentage difference calculation."""
        group_a = [0.8, 0.9, 0.85]
        group_b = [0.7, 0.75, 0.72]

        diff = calculate_percentage_difference(group_a, group_b)
        # Mean A = 0.85, Mean B = 0.7233
        # Diff = (0.85 - 0.7233) / 0.7233 * 100 = 17.52%
        expected_mean_a = np.mean(group_a)
        expected_mean_b = np.mean(group_b)
        expected = ((expected_mean_a - expected_mean_b) / expected_mean_b) * 100

        assert np.isclose(diff, expected, rtol=1e-4)

    def test_negative_difference(self):
        """Test when group_a mean is less than group_b mean."""
        group_a = [0.5, 0.6]
        group_b = [0.7, 0.8]

        diff = calculate_percentage_difference(group_a, group_b)
        assert diff < 0

    def test_zero_difference(self):
        """Test when means are equal."""
        group_a = [0.5, 0.6, 0.7]
        group_b = [0.5, 0.6, 0.7]

        diff = calculate_percentage_difference(group_a, group_b)
        assert np.isclose(diff, 0.0, atol=1e-6)

    def test_single_element(self):
        """Test with single element in each group."""
        group_a = [0.8]
        group_b = [0.4]

        diff = calculate_percentage_difference(group_a, group_b)
        assert np.isclose(diff, 100.0, atol=1e-4)


class TestRunPairedTtest:
    """Tests for paired t-test implementation."""

    def test_basic_ttest(self):
        """Test basic paired t-test."""
        group_a = np.array([0.8, 0.9, 0.85, 0.92])
        group_b = np.array([0.7, 0.75, 0.72, 0.78])

        result = run_paired_ttest(group_a, group_b)

        assert result.test_name == "paired_ttest"
        assert result.statistic is not None
        assert result.p_value is not None
        assert result.effect_size is not None
        assert isinstance(result.significant, bool)

        # Verify against scipy
        scipy_result = scipy_stats.ttest_rel(group_a, group_b)
        assert np.isclose(result.statistic, scipy_result.statistic, rtol=1e-5)
        assert np.isclose(result.p_value, scipy_result.pvalue, rtol=1e-5)

    def test_identical_groups(self):
        """Test when groups are identical (p-value should be 1.0)."""
        group_a = np.array([0.5, 0.6, 0.7])
        group_b = np.array([0.5, 0.6, 0.7])

        result = run_paired_ttest(group_a, group_b)

        assert np.isclose(result.statistic, 0.0, atol=1e-6)
        assert np.isclose(result.p_value, 1.0, atol=1e-4)

    def test_small_sample(self):
        """Test with small sample size."""
        group_a = np.array([0.8, 0.9])
        group_b = np.array([0.7, 0.75])

        result = run_paired_ttest(group_a, group_b)

        assert result.test_name == "paired_ttest"
        assert result.statistic is not None
        assert result.p_value is not None

    def test_unequal_length_raises(self):
        """Test that unequal lengths raise an error."""
        group_a = np.array([0.8, 0.9, 0.85])
        group_b = np.array([0.7, 0.75])

        with pytest.raises(ValueError):
            run_paired_ttest(group_a, group_b)


class TestCalculateCohenD:
    """Tests for Cohen's d effect size calculation."""

    def test_basic_cohen_d(self):
        """Test basic Cohen's d calculation."""
        group_a = np.array([0.8, 0.9, 0.85, 0.92])
        group_b = np.array([0.7, 0.75, 0.72, 0.78])

        d = calculate_cohen_d(group_a, group_b)

        # Manual calculation
        mean_a = np.mean(group_a)
        mean_b = np.mean(group_b)
        std_a = np.std(group_a, ddof=1)
        std_b = np.std(group_b, ddof=1)
        pooled_std = np.sqrt((std_a**2 + std_b**2) / 2)
        expected_d = (mean_a - mean_b) / pooled_std

        assert np.isclose(d, expected_d, rtol=1e-4)

    def test_zero_pooled_std(self):
        """Test when pooled standard deviation is zero."""
        group_a = np.array([0.5, 0.5, 0.5])
        group_b = np.array([0.5, 0.5, 0.5])

        d = calculate_cohen_d(group_a, group_b)
        assert np.isclose(d, 0.0, atol=1e-6)

    def test_interpretation(self):
        """Test that Cohen's d falls in expected ranges."""
        # Small effect (~0.2)
        group_a = np.array([0.5, 0.6, 0.7, 0.8])
        group_b = np.array([0.4, 0.5, 0.6, 0.7])
        d_small = calculate_cohen_d(group_a, group_b)
        assert 0.1 < d_small < 0.4

        # Large effect (~0.8)
        group_a = np.array([0.9, 0.95, 1.0])
        group_b = np.array([0.1, 0.15, 0.2])
        d_large = calculate_cohen_d(group_a, group_b)
        assert d_large > 0.5


class TestCalculateConfidenceInterval:
    """Tests for confidence interval calculation."""

    def test_95_confidence_interval(self):
        """Test 95% confidence interval calculation."""
        data = np.array([0.8, 0.9, 0.85, 0.92, 0.88])

        ci = calculate_confidence_interval(data, confidence=0.95)

        assert isinstance(ci, tuple)
        assert len(ci) == 2
        assert ci[0] <= np.mean(data) <= ci[1]

        # Verify against scipy
        from scipy import stats as scipy_stats
        scipy_ci = scipy_stats.t.interval(
            0.95,
            len(data) - 1,
            loc=np.mean(data),
            scale=scipy_stats.sem(data)
        )

        assert np.isclose(ci[0], scipy_ci[0], rtol=1e-4)
        assert np.isclose(ci[1], scipy_ci[1], rtol=1e-4)

    def test_99_confidence_interval(self):
        """Test 99% confidence interval calculation."""
        data = np.array([0.8, 0.9, 0.85, 0.92, 0.88])

        ci = calculate_confidence_interval(data, confidence=0.99)

        # 99% CI should be wider than 95% CI
        ci_95 = calculate_confidence_interval(data, confidence=0.95)
        assert (ci[1] - ci[0]) > (ci_95[1] - ci_95[0])

    def test_single_element(self):
        """Test with single element."""
        data = np.array([0.8])

        ci = calculate_confidence_interval(data, confidence=0.95)

        # With single element, CI should be the element itself (or very narrow)
        assert np.isclose(ci[0], 0.8, atol=1e-6)
        assert np.isclose(ci[1], 0.8, atol=1e-6)


class TestBonferroniCorrection:
    """Tests for Bonferroni correction."""

    def test_basic_correction(self):
        """Test basic Bonferroni correction."""
        p_values = [0.01, 0.05, 0.1, 0.001]
        n_tests = len(p_values)

        corrected = bonferroni_correction(p_values, n_tests)

        # Each p-value should be multiplied by n_tests
        expected = [p * n_tests for p in p_values]

        assert len(corrected) == len(p_values)
        for i, (c, e) in enumerate(zip(corrected, expected)):
            assert np.isclose(c, min(e, 1.0), rtol=1e-4)

    def test_capped_at_one(self):
        """Test that corrected p-values are capped at 1.0."""
        p_values = [0.5, 0.6, 0.7]
        n_tests = 3

        corrected = bonferroni_correction(p_values, n_tests)

        for p in corrected:
            assert p <= 1.0

    def test_empty_list(self):
        """Test with empty list."""
        p_values = []

        corrected = bonferroni_correction(p_values, 0)
        assert corrected == []


class TestGenerateStatisticalReport:
    """Tests for generating the full statistical report."""

    def test_full_report_generation(self):
        """Test generation of a complete statistical report."""
        # Create mock evaluation results
        recursive_results = [
            {"seed": 1, "metrics": {"self_consistency": 0.85, "converged": True}},
            {"seed": 2, "metrics": {"self_consistency": 0.88, "converged": True}},
            {"seed": 3, "metrics": {"self_consistency": 0.82, "converged": True}},
        ]

        baseline_results = [
            {"seed": 1, "metrics": {"self_consistency": 0.72, "converged": True}},
            {"seed": 2, "metrics": {"self_consistency": 0.75, "converged": True}},
            {"seed": 3, "metrics": {"self_consistency": 0.70, "converged": True}},
        ]

        report = generate_statistical_report(
            project_id="PROJ-558",
            recursive_results=recursive_results,
            baseline_results=baseline_results,
            metric_name="self_consistency",
            alpha=0.05
        )

        assert report.project_id == "PROJ-558"
        assert len(report.tests) > 0
        assert report.summary_stats is not None

        # Check that a t-test result is included
        ttest_results = [t for t in report.tests if "ttest" in t.test_name.lower()]
        assert len(ttest_results) > 0

    def test_report_with_non_converged_seeds(self):
        """Test report generation with some non-converged seeds."""
        recursive_results = [
            {"seed": 1, "metrics": {"self_consistency": 0.85, "converged": True}},
            {"seed": 2, "metrics": {"self_consistency": 0.88, "converged": False}},  # Excluded
            {"seed": 3, "metrics": {"self_consistency": 0.82, "converged": True}},
        ]

        baseline_results = [
            {"seed": 1, "metrics": {"self_consistency": 0.72, "converged": True}},
            {"seed": 2, "metrics": {"self_consistency": 0.75, "converged": True}},
            {"seed": 3, "metrics": {"self_consistency": 0.70, "converged": True}},
        ]

        report = generate_statistical_report(
            project_id="PROJ-558",
            recursive_results=recursive_results,
            baseline_results=baseline_results,
            metric_name="self_consistency",
            alpha=0.05
        )

        # Should only use 2 recursive seeds (seed 2 excluded)
        assert len(report.tests) > 0

    def test_report_with_zero_variance(self):
        """Test report generation when one group has zero variance."""
        recursive_results = [
            {"seed": 1, "metrics": {"self_consistency": 0.85, "converged": True}},
            {"seed": 2, "metrics": {"self_consistency": 0.85, "converged": True}},
        ]

        baseline_results = [
            {"seed": 1, "metrics": {"self_consistency": 0.72, "converged": True}},
            {"seed": 2, "metrics": {"self_consistency": 0.72, "converged": True}},
        ]

        # This should not crash even with zero variance
        report = generate_statistical_report(
            project_id="PROJ-558",
            recursive_results=recursive_results,
            baseline_results=baseline_results,
            metric_name="self_consistency",
            alpha=0.05
        )

        assert report.project_id == "PROJ-558"


class TestSaveStatisticalReport:
    """Tests for saving statistical reports to JSON."""

    def test_save_and_load(self):
        """Test saving and loading a statistical report."""
        report = StatisticalReport(
            project_id="PROJ-558",
            description="Test report",
            tests=[
                StatisticalTestResult(
                    test_name="ttest",
                    statistic=2.5,
                    p_value=0.02,
                    effect_size=0.8,
                    significant=True,
                    description="Test"
                )
            ],
            summary_stats={"mean": 0.85},
            raw_metrics_file="metrics.json",
            threshold_sensitivity={"threshold": 0.5}
        )

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            save_statistical_report(report, f.name)

            # Load and verify
            with open(f.name, 'r') as loaded:
                data = json.load(loaded)

            assert data["project_id"] == "PROJ-558"
            assert len(data["tests"]) == 1
            assert data["tests"][0]["test_name"] == "ttest"
            assert data["summary_stats"]["mean"] == 0.85

        os.unlink(f.name)


class TestRunSensitivityAnalysis:
    """Tests for sensitivity analysis across confidence thresholds."""

    def test_basic_sensitivity_analysis(self):
        """Test basic sensitivity analysis execution."""
        # Create mock results with confidence scores and correctness
        recursive_results = [
            {
                "seed": 1,
                "metrics": {
                    "self_consistency": 0.85,
                    "converged": True,
                    "confidence_scores": [0.9, 0.8, 0.7, 0.6, 0.5],
                    "correctness": [1, 1, 1, 0, 0]
                }
            },
            {
                "seed": 2,
                "metrics": {
                    "self_consistency": 0.88,
                    "converged": True,
                    "confidence_scores": [0.95, 0.85, 0.75, 0.65, 0.55],
                    "correctness": [1, 1, 1, 1, 0]
                }
            }
        ]

        thresholds = [0.5, 0.6, 0.7, 0.8]

        results = run_sensitivity_analysis(
            recursive_results,
            thresholds,
            metric_name="self_consistency"
        )

        assert len(results) == len(thresholds)
        for i, result in enumerate(results):
            assert "threshold" in result
            assert "false_positive_rate" in result
            assert "false_negative_rate" in result
            assert "fp_rate_delta" in result
            assert "fn_rate_delta" in result
            assert result["threshold"] == thresholds[i]

    def test_sensitivity_with_no_converged(self):
        """Test sensitivity analysis with no converged seeds."""
        recursive_results = [
            {
                "seed": 1,
                "metrics": {
                    "self_consistency": 0.85,
                    "converged": False,
                    "confidence_scores": [0.9, 0.8],
                    "correctness": [1, 1]
                }
            }
        ]

        thresholds = [0.5, 0.6]

        # Should handle gracefully (possibly empty or warning)
        results = run_sensitivity_analysis(
            recursive_results,
            thresholds,
            metric_name="self_consistency"
        )

        # With no converged seeds, results might be empty or have defaults
        # The function should not crash

    def test_sensitivity_with_single_threshold(self):
        """Test sensitivity analysis with a single threshold."""
        recursive_results = [
            {
                "seed": 1,
                "metrics": {
                    "self_consistency": 0.85,
                    "converged": True,
                    "confidence_scores": [0.9, 0.8, 0.7],
                    "correctness": [1, 1, 0]
                }
            }
        ]

        thresholds = [0.6]

        results = run_sensitivity_analysis(
            recursive_results,
            thresholds,
            metric_name="self_consistency"
        )

        assert len(results) == 1
        assert results[0]["threshold"] == 0.6

    def test_delta_calculation(self):
        """Test that delta values are calculated correctly."""
        recursive_results = [
            {
                "seed": 1,
                "metrics": {
                    "self_consistency": 0.85,
                    "converged": True,
                    "confidence_scores": [0.9, 0.8, 0.7, 0.6, 0.5],
                    "correctness": [1, 1, 1, 0, 0]
                }
            }
        ]

        thresholds = [0.5, 0.6, 0.7]

        results = run_sensitivity_analysis(
            recursive_results,
            thresholds,
            metric_name="self_consistency"
        )

        # First threshold should have None deltas
        assert results[0]["fp_rate_delta"] is None
        assert results[0]["fn_rate_delta"] is None

        # Subsequent thresholds should have numeric deltas
        for i in range(1, len(results)):
            assert results[i]["fp_rate_delta"] is not None
            assert results[i]["fn_rate_delta"] is not None


class TestMainFunction:
    """Tests for the main function entry point."""

    def test_main_with_args(self):
        """Test main function with command line arguments."""
        import sys
        from io import StringIO

        # Mock arguments
        sys.argv = [
            "test_main",
            "--recursive-results", "data/recursive_results.json",
            "--baseline-results", "data/baseline_results.json",
            "--output", "artifacts/results/statistical_report.json",
            "--metric", "self_consistency"
        ]

        # Create mock input files
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f1:
            json.dump([{"seed": 1, "metrics": {"self_consistency": 0.85, "converged": True}}], f1)
            recursive_file = f1.name

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f2:
            json.dump([{"seed": 1, "metrics": {"self_consistency": 0.72, "converged": True}}], f2)
            baseline_file = f2.name

        # Update args with real paths
        sys.argv = [
            "test_main",
            "--recursive-results", recursive_file,
            "--baseline-results", baseline_file,
            "--output", "artifacts/results/test_report.json",
            "--metric", "self_consistency"
        ]

        # Mock the output file to avoid actual writing
        with patch('code.analysis.stats.save_statistical_report') as mock_save:
            mock_save.return_value = None
            try:
                main()
                # If we get here without crashing, the function parsed args correctly
                assert mock_save.called
            except SystemExit:
                # Expected if main() calls sys.exit()
                pass
            finally:
                os.unlink(recursive_file)
                os.unlink(baseline_file)

    def test_main_with_invalid_args(self):
        """Test main function with invalid arguments."""
        import sys

        sys.argv = [
            "test_main",
            "--recursive-results", "nonexistent.json",
            "--baseline-results", "nonexistent.json",
            "--output", "artifacts/results/test_report.json"
        ]

        # Should raise FileNotFoundError or similar
        with pytest.raises(FileNotFoundError):
            main()
