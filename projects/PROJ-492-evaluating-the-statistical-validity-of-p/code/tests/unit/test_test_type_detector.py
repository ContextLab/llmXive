"""
Unit tests for the outcome type detector (T022).

These tests verify that the test_type_detector module correctly classifies
A/B test summaries as binary or continuous outcomes.
"""

import pytest
from code.src.audit.test_type_detector import (
    detect_outcome_type,
    detect_outcome_type_from_ab_summary,
    is_binary_outcome,
    is_continuous_outcome,
    OUTCOME_BINARY,
    OUTCOME_CONTINUOUS,
    OUTCOME_UNKNOWN,
    _normalize_field_name,
    _check_binary_fields,
    _check_continuous_fields,
    _check_binary_keywords,
    _check_continuous_keywords,
    _check_numeric_patterns,
)
from code.src.models.data_models import ABTestSummary
from code.src.utils.logger import get_default_logger
from datetime import datetime


class TestNormalizeFieldName:
    """Tests for the _normalize_field_name helper function."""

    def test_simple_field(self):
        assert _normalize_field_name("conversion_rate") == "conversion_rate"

    def test_with_dashes(self):
        assert _normalize_field_name("click-through-rate") == "click_through_rate"

    def test_with_dots(self):
        assert _normalize_field_name("baseline.rate") == "baseline_rate"

    def test_empty_string(self):
        assert _normalize_field_name("") == ""

    def test_none_handling(self):
        assert _normalize_field_name(None) == ""

    def test_uppercase(self):
        assert _normalize_field_name("CONVERSION_RATE") == "conversion_rate"


class TestCheckBinaryFields:
    """Tests for the _check_binary_fields function."""

    def test_conversion_rate_field(self):
        data = {"conversion_rate": 0.05}
        assert _check_binary_fields(data) is True

    def test_baseline_rate_field(self):
        data = {"baseline_rate": 0.05}
        assert _check_binary_fields(data) is True

    def test_ctr_field(self):
        data = {"ctr": 0.02}
        assert _check_binary_fields(data) is True

    def test_proportion_field(self):
        data = {"proportion": 0.1}
        assert _check_binary_fields(data) is True

    def test_no_binary_fields(self):
        data = {"revenue": 100, "cost": 50}
        assert _check_binary_fields(data) is False

    def test_empty_data(self):
        data = {}
        assert _check_binary_fields(data) is False


class TestCheckContinuousFields:
    """Tests for the _check_continuous_fields function."""

    def test_mean_field(self):
        data = {"mean": 50.0}
        assert _check_continuous_fields(data) is True

    def test_baseline_mean_field(self):
        data = {"baseline_mean": 50.0}
        assert _check_continuous_fields(data) is True

    def test_average_field(self):
        data = {"average": 100}
        assert _check_continuous_fields(data) is True

    def test_revenue_field(self):
        data = {"revenue": 1000}
        assert _check_continuous_fields(data) is True

    def test_latency_field(self):
        data = {"latency": 200}
        assert _check_continuous_fields(data) is True

    def test_no_continuous_fields(self):
        data = {"conversion_rate": 0.05}
        assert _check_continuous_fields(data) is False


class TestCheckBinaryKeywords:
    """Tests for the _check_binary_keywords function."""

    def test_conversion_keyword(self):
        data = {"metric_name": "Conversion Rate"}
        assert _check_binary_keywords(data) is True

    def test_click_keyword(self):
        data = {"metric_name": "Click-Through Rate"}
        assert _check_binary_keywords(data) is True

    def test_ctr_keyword(self):
        data = {"description": "Click through rate analysis"}
        assert _check_binary_keywords(data) is True

    def test_purchase_keyword(self):
        data = {"metric_name": "Purchase Rate"}
        assert _check_binary_keywords(data) is True

    def test_no_binary_keywords(self):
        data = {"metric_name": "Average Revenue"}
        assert _check_binary_keywords(data) is False


class TestCheckContinuousKeywords:
    """Tests for the _check_continuous_keywords function."""

    def test_mean_keyword(self):
        data = {"metric_name": "Mean Revenue"}
        assert _check_continuous_keywords(data) is True

    def test_average_keyword(self):
        data = {"metric_name": "Average Response Time"}
        assert _check_continuous_keywords(data) is True

    def test_revenue_keyword(self):
        data = {"metric_name": "Total Revenue"}
        assert _check_continuous_keywords(data) is True

    def test_latency_keyword(self):
        data = {"description": "Latency analysis"}
        assert _check_continuous_keywords(data) is True

    def test_no_continuous_keywords(self):
        data = {"metric_name": "Conversion Rate"}
        assert _check_continuous_keywords(data) is False


class TestCheckNumericPatterns:
    """Tests for the _check_numeric_patterns function."""

    def test_binary_rate_pattern(self):
        data = {"baseline_rate": 0.05, "treatment_rate": 0.07}
        has_binary, has_continuous = _check_numeric_patterns(data)
        assert has_binary is True

    def test_continuous_mean_std_pattern(self):
        data = {
            "baseline_mean": 50.0,
            "treatment_mean": 55.0,
            "baseline_std": 10.0,
            "treatment_std": 12.0,
        }
        has_binary, has_continuous = _check_numeric_patterns(data)
        assert has_continuous is True

    def test_no_patterns(self):
        data = {"sample_size": 100}
        has_binary, has_continuous = _check_numeric_patterns(data)
        assert has_binary is False
        assert has_continuous is False


class TestDetectOutcomeType:
    """Tests for the main detect_outcome_type function."""

    def test_binary_conversion_rate(self):
        data = {
            "metric_name": "Conversion Rate",
            "baseline_rate": 0.05,
            "treatment_rate": 0.07,
        }
        outcome_type, evidence = detect_outcome_type(data)
        assert outcome_type == OUTCOME_BINARY
        assert evidence["binary_fields"] is True

    def test_binary_ctr(self):
        data = {
            "metric_name": "CTR",
            "baseline_ctr": 0.02,
            "treatment_ctr": 0.025,
        }
        outcome_type, evidence = detect_outcome_type(data)
        assert outcome_type == OUTCOME_BINARY

    def test_continuous_mean_revenue(self):
        data = {
            "metric_name": "Average Revenue",
            "baseline_mean": 50.0,
            "treatment_mean": 55.0,
            "baseline_std": 10.0,
            "treatment_std": 12.0,
        }
        outcome_type, evidence = detect_outcome_type(data)
        assert outcome_type == OUTCOME_CONTINUOUS
        assert evidence["continuous_fields"] is True

    def test_continuous_latency(self):
        data = {
            "metric_name": "Response Time",
            "baseline_mean": 200,
            "treatment_mean": 180,
            "baseline_std": 50,
            "treatment_std": 45,
        }
        outcome_type, evidence = detect_outcome_type(data)
        assert outcome_type == OUTCOME_CONTINUOUS

    def test_unknown_insufficient_data(self):
        data = {
            "metric_name": "Unknown Metric",
            "sample_size": 100,
        }
        outcome_type, evidence = detect_outcome_type(data)
        assert outcome_type == OUTCOME_UNKNOWN

    def test_evidence_dict_structure(self):
        data = {"conversion_rate": 0.05}
        outcome_type, evidence = detect_outcome_type(data)
        assert "binary_fields" in evidence
        assert "continuous_fields" in evidence
        assert "binary_keywords" in evidence
        assert "continuous_keywords" in evidence
        assert "binary_numeric_pattern" in evidence
        assert "continuous_numeric_pattern" in evidence


class TestDetectOutcomeTypeFromAbSummary:
    """Tests for detect_outcome_type_from_ab_summary with Pydantic models."""

    def test_from_pydantic_binary(self):
        summary = ABTestSummary(
            url="https://example.com/test",
            metric_name="Conversion Rate",
            baseline_rate=0.05,
            treatment_rate=0.07,
            baseline_n=1000,
            treatment_n=1000,
            p_value=0.03,
            effect_size=0.02,
            timestamp=datetime.now(),
        )
        outcome_type, evidence = detect_outcome_type_from_ab_summary(summary)
        assert outcome_type == OUTCOME_BINARY

    def test_from_pydantic_continuous(self):
        summary = ABTestSummary(
            url="https://example.com/test",
            metric_name="Average Revenue",
            baseline_mean=50.0,
            treatment_mean=55.0,
            baseline_std=10.0,
            treatment_std=12.0,
            baseline_n=1000,
            treatment_n=1000,
            p_value=0.03,
            effect_size=5.0,
            timestamp=datetime.now(),
        )
        outcome_type, evidence = detect_outcome_type_from_ab_summary(summary)
        assert outcome_type == OUTCOME_CONTINUOUS

    def test_from_dict(self):
        data = {"conversion_rate": 0.05, "baseline_n": 1000}
        outcome_type, evidence = detect_outcome_type_from_ab_summary(data)
        assert outcome_type == OUTCOME_BINARY


class TestIsBinaryOutcome:
    """Tests for the is_binary_outcome convenience function."""

    def test_returns_true_for_binary(self):
        data = {"conversion_rate": 0.05}
        assert is_binary_outcome(data) is True

    def test_returns_false_for_continuous(self):
        data = {"baseline_mean": 50.0}
        assert is_binary_outcome(data) is False

    def test_returns_false_for_unknown(self):
        data = {"sample_size": 100}
        assert is_binary_outcome(data) is False


class TestIsContinuousOutcome:
    """Tests for the is_continuous_outcome convenience function."""

    def test_returns_true_for_continuous(self):
        data = {"baseline_mean": 50.0}
        assert is_continuous_outcome(data) is True

    def test_returns_false_for_binary(self):
        data = {"conversion_rate": 0.05}
        assert is_continuous_outcome(data) is False

    def test_returns_false_for_unknown(self):
        data = {"sample_size": 100}
        assert is_continuous_outcome(data) is False


class TestEdgeCases:
    """Tests for edge cases and boundary conditions."""

    def test_rate_at_boundary(self):
        """Rate of exactly 1.0 should still be detected as binary."""
        data = {"baseline_rate": 1.0, "treatment_rate": 1.0}
        outcome_type, _ = detect_outcome_type(data)
        assert outcome_type == OUTCOME_BINARY

    def test_rate_at_zero(self):
        """Rate of 0.0 should still be detected as binary."""
        data = {"baseline_rate": 0.0, "treatment_rate": 0.0}
        outcome_type, _ = detect_outcome_type(data)
        assert outcome_type == OUTCOME_BINARY

    def test_mixed_indicators_binary_wins(self):
        """When indicators conflict, binary should win if it has more evidence."""
        data = {
            "conversion_rate": 0.05,  # binary field
            "metric_name": "Average",  # continuous keyword
            "baseline_n": 1000,
        }
        outcome_type, evidence = detect_outcome_type(data)
        assert outcome_type == OUTCOME_BINARY
        assert evidence["binary_fields"] is True

    def test_empty_string_values(self):
        """Empty string values should not crash the detector."""
        data = {"metric_name": "", "baseline_rate": ""}
        outcome_type, _ = detect_outcome_type(data)
        # Should not crash, may return unknown
        assert outcome_type in [OUTCOME_BINARY, OUTCOME_CONTINUOUS, OUTCOME_UNKNOWN]

    def test_none_values_in_data(self):
        """None values in data should be handled gracefully."""
        data = {"metric_name": None, "baseline_rate": None}
        outcome_type, _ = detect_outcome_type(data)
        # Should not crash
        assert outcome_type in [OUTCOME_BINARY, OUTCOME_CONTINUOUS, OUTCOME_UNKNOWN]


class TestIntegrationWithLogger:
    """Tests for integration with the AuditLogger."""

    def test_with_logger_provided(self):
        """Should work correctly when logger is provided."""
        logger = get_default_logger()
        data = {"conversion_rate": 0.05}
        outcome_type, evidence = detect_outcome_type(data, logger)
        assert outcome_type == OUTCOME_BINARY

    def test_without_logger(self):
        """Should work correctly when logger is not provided."""
        data = {"conversion_rate": 0.05}
        outcome_type, evidence = detect_outcome_type(data)
        assert outcome_type == OUTCOME_BINARY
