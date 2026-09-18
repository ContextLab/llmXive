"""
Unit tests for validate_success_criteria module.

Tests cover:
- Loading statistical summary
- Checking individual criteria
- Direction validation
- Effect size validation
- Report generation
"""

import json
import os
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from code.validation.validate_success_criteria import (
    SuccessCriterion,
    ValidationResult,
    ValidationReport,
    get_metric_key,
    load_statistical_summary,
    check_criterion,
    check_all_significant_criteria,
    validate_success_criteria,
    _check_all_effect_sizes,
    SUCCESS_CRITERIA
)


@pytest.fixture
def valid_summary():
    """Create a valid statistical summary for testing."""
    return {
        "metrics": {
            "sart_commission_errors": {
                "mean_change": -2.5,
                "corrected_p_value": 0.03,
                "cohens_d": -0.45,
                "ci_lower": -3.8,
                "ci_upper": -1.2
            },
            "ospan_total_correct": {
                "mean_change": 3.2,
                "corrected_p_value": 0.02,
                "cohens_d": 0.52,
                "ci_lower": 1.5,
                "ci_upper": 4.9
            },
            "pss10_total": {
                "mean_change": -4.1,
                "corrected_p_value": 0.01,
                "cohens_d": -0.68,
                "ci_lower": -6.2,
                "ci_upper": -2.0
            },
            "panas_positive_affect": {
                "mean_change": 2.8,
                "corrected_p_value": 0.04,
                "cohens_d": 0.38,
                "ci_lower": 0.9,
                "ci_upper": 4.7
            }
        }
    }


@pytest.fixture
def invalid_summary():
    """Create a summary with some failing criteria."""
    return {
        "metrics": {
            "sart_commission_errors": {
                "mean_change": -2.5,
                "corrected_p_value": 0.08,  # Not significant
                "cohens_d": -0.45
            },
            "ospan_total_correct": {
                "mean_change": -1.0,  # Wrong direction
                "corrected_p_value": 0.02,
                "cohens_d": -0.15
            }
        }
    }


@pytest.fixture
def temp_summary_file(tmp_path, valid_summary):
    """Create a temporary summary file."""
    file_path = tmp_path / "statistical_summary.json"
    with open(file_path, 'w') as f:
        json.dump(valid_summary, f)
    return str(file_path)


@pytest.fixture
def temp_report_file(tmp_path):
    """Create a temporary report file path."""
    return str(tmp_path / "validation_report.json")


class TestGetMetricKey:
    def test_known_metric(self):
        assert get_metric_key("sart_commission_errors") == "sart_commission_errors"
        assert get_metric_key("ospan_total_correct") == "ospan_total_correct"

    def test_unknown_metric(self):
        assert get_metric_key("unknown_metric") == "unknown_metric"


class TestLoadStatisticalSummary:
    def test_load_valid_file(self, temp_summary_file, valid_summary):
        result = load_statistical_summary(temp_summary_file)
        assert result == valid_summary

    def test_file_not_found(self):
        with pytest.raises(FileNotFoundError):
            load_statistical_summary("nonexistent/file.json")

    def test_invalid_json(self, tmp_path):
        file_path = tmp_path / "invalid.json"
        file_path.write_text("not valid json")
        with pytest.raises(json.JSONDecodeError):
            load_statistical_summary(str(file_path))


class TestCheckCriterion:
    def test_pass_significant_negative(self, valid_summary):
        criterion = SuccessCriterion(
            id="TEST-001",
            metric="sart_commission_errors",
            direction="negative",
            threshold_p=0.05,
            threshold_d=0.2,
            description="Test criterion"
        )
        result = check_criterion(criterion, valid_summary)
        assert result.passed is True
        assert result.observed_p == 0.03
        assert result.observed_change == -2.5

    def test_pass_significant_positive(self, valid_summary):
        criterion = SuccessCriterion(
            id="TEST-002",
            metric="ospan_total_correct",
            direction="positive",
            threshold_p=0.05,
            threshold_d=0.2,
            description="Test criterion"
        )
        result = check_criterion(criterion, valid_summary)
        assert result.passed is True
        assert result.observed_p == 0.02
        assert result.observed_change == 3.2

    def test_fail_not_significant(self, invalid_summary):
        criterion = SuccessCriterion(
            id="TEST-003",
            metric="sart_commission_errors",
            direction="negative",
            threshold_p=0.05,
            threshold_d=0.2,
            description="Test criterion"
        )
        result = check_criterion(criterion, invalid_summary)
        assert result.passed is False
        assert "Not significant" in result.reason

    def test_fail_wrong_direction(self, invalid_summary):
        criterion = SuccessCriterion(
            id="TEST-004",
            metric="ospan_total_correct",
            direction="positive",
            threshold_p=0.05,
            threshold_d=0.2,
            description="Test criterion"
        )
        result = check_criterion(criterion, invalid_summary)
        assert result.passed is False
        assert "Wrong direction" in result.reason

    def test_fail_effect_size_too_small(self, valid_summary):
        # Create a summary with small effect size
        small_effect_summary = {
            "metrics": {
                "sart_commission_errors": {
                    "mean_change": -0.5,
                    "corrected_p_value": 0.03,
                    "cohens_d": 0.1
                }
            }
        }
        criterion = SuccessCriterion(
            id="TEST-005",
            metric="sart_commission_errors",
            direction="negative",
            threshold_p=0.05,
            threshold_d=0.2,
            description="Test criterion"
        )
        result = check_criterion(criterion, small_effect_summary)
        assert result.passed is False
        assert "Effect size too small" in result.reason

    def test_metric_not_found(self, valid_summary):
        criterion = SuccessCriterion(
            id="TEST-006",
            metric="nonexistent_metric",
            direction="positive",
            threshold_p=0.05,
            threshold_d=0.2,
            description="Test criterion"
        )
        result = check_criterion(criterion, valid_summary)
        assert result.passed is False
        assert "not found" in result.reason


class TestCheckAllEffectSizes:
    def test_all_pass(self, valid_summary):
        criterion = SuccessCriterion(
            id="SC-005",
            metric="all_significant",
            direction="any",
            threshold_p=0.05,
            threshold_d=0.2,
            description="All effect sizes >= 0.2"
        )
        result = _check_all_effect_sizes(valid_summary, criterion)
        assert result.passed is True

    def test_one_fails(self):
        summary_with_small_effect = {
            "metrics": {
                "sart_commission_errors": {
                    "mean_change": -2.5,
                    "corrected_p_value": 0.03,
                    "cohens_d": -0.45
                },
                "ospan_total_correct": {
                    "mean_change": 3.2,
                    "corrected_p_value": 0.02,
                    "cohens_d": 0.15  # Too small
                }
            }
        }
        criterion = SuccessCriterion(
            id="SC-005",
            metric="all_significant",
            direction="any",
            threshold_p=0.05,
            threshold_d=0.2,
            description="All effect sizes >= 0.2"
        )
        result = _check_all_effect_sizes(summary_with_small_effect, criterion)
        assert result.passed is False
        assert "ospan_total_correct" in result.reason


class TestCheckAllSignificantCriteria:
    def test_all_pass(self, valid_summary):
        results = check_all_significant_criteria(valid_summary)
        assert len(results) == len(SUCCESS_CRITERIA)
        # At least the first 4 should pass
        passing = sum(1 for r in results[:4] if r.passed)
        assert passing == 4

    def test_some_fail(self, invalid_summary):
        results = check_all_significant_criteria(invalid_summary)
        assert len(results) == len(SUCCESS_CRITERIA)
        # Some should fail
        passing = sum(1 for r in results if r.passed)
        assert passing < len(results)


class TestValidateSuccessCriteria:
    def test_full_validation_pass(self, temp_summary_file, temp_report_file, valid_summary):
        report = validate_success_criteria(temp_summary_file, temp_report_file)
        assert report.total_criteria == len(SUCCESS_CRITERIA)
        assert report.passed_criteria == 4  # SC-001 to SC-004 pass, SC-005 depends
        assert os.path.exists(temp_report_file)
        assert os.path.exists(temp_report_file.replace('.json', '.md'))

    def test_full_validation_fail(self, tmp_path):
        # Create a summary that will fail
        failing_summary = {
            "metrics": {
                "sart_commission_errors": {
                    "mean_change": -0.1,
                    "corrected_p_value": 0.99,
                    "cohens_d": -0.01
                }
            }
        }
        summary_file = tmp_path / "summary.json"
        with open(summary_file, 'w') as f:
            json.dump(failing_summary, f)

        report_file = tmp_path / "report.json"
        report = validate_success_criteria(str(summary_file), str(report_file))

        assert report.overall_passed is False
        assert report.failed_criteria > 0

    def test_missing_summary_file(self, tmp_path):
        report = validate_success_criteria(
            str(tmp_path / "nonexistent.json"),
            str(tmp_path / "report.json")
        )
        assert report.overall_passed is False
        assert report.failed_criteria == len(SUCCESS_CRITERIA)


class TestValidationReport:
    def test_report_structure(self, valid_summary, tmp_path):
        summary_file = tmp_path / "summary.json"
        report_file = tmp_path / "report.json"

        with open(summary_file, 'w') as f:
            json.dump(valid_summary, f)

        report = validate_success_criteria(str(summary_file), str(report_file))

        assert hasattr(report, 'timestamp')
        assert hasattr(report, 'overall_passed')
        assert hasattr(report, 'total_criteria')
        assert hasattr(report, 'passed_criteria')
        assert hasattr(report, 'failed_criteria')
        assert hasattr(report, 'results')
        assert hasattr(report, 'summary')
        assert isinstance(report.results, list)


class TestEdgeCases:
    def test_missing_p_value(self):
        summary = {
            "metrics": {
                "sart_commission_errors": {
                    "mean_change": -2.5,
                    "cohens_d": -0.45
                }
            }
        }
        criterion = SuccessCriterion(
            id="TEST",
            metric="sart_commission_errors",
            direction="negative",
            threshold_p=0.05,
            threshold_d=0.2,
            description="Test"
        )
        result = check_criterion(criterion, summary)
        assert result.passed is False
        assert "No p-value" in result.reason

    def test_missing_effect_size(self):
        summary = {
            "metrics": {
                "sart_commission_errors": {
                    "mean_change": -2.5,
                    "corrected_p_value": 0.03
                }
            }
        }
        criterion = SuccessCriterion(
            id="TEST",
            metric="sart_commission_errors",
            direction="negative",
            threshold_p=0.05,
            threshold_d=0.2,
            description="Test"
        )
        result = check_criterion(criterion, summary)
        assert result.passed is False
        assert "No effect size" in result.reason

    def test_zero_change(self):
        summary = {
            "metrics": {
                "sart_commission_errors": {
                    "mean_change": 0.0,
                    "corrected_p_value": 0.03,
                    "cohens_d": 0.45
                }
            }
        }
        criterion = SuccessCriterion(
            id="TEST",
            metric="sart_commission_errors",
            direction="negative",
            threshold_p=0.05,
            threshold_d=0.2,
            description="Test"
        )
        result = check_criterion(criterion, summary)
        assert result.passed is False
        assert "Wrong direction" in result.reason