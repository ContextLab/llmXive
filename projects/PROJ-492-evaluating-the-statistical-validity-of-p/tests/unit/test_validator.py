"""
Unit tests for the validator module (T025).

Covers:
- Absolute p-difference > 0.05
- Relative effect-size > 5%
- Inequality handling (p-value ranges)
- Sample-size mismatch with data_quality_warning generation
"""
import pytest
import math
from code.src.audit.validator import (
    calculate_absolute_p_difference,
    calculate_relative_effect_size_difference,
    detect_sample_size_mismatch,
    check_p_value_consistency,
    check_effect_size_consistency,
    create_audit_record,
    validate_summary,
    validate_all_summaries,
)
from code.src.models.data_models import ABTestSummary, AuditRecord
from code.src.utils.logger import get_error_message, AuditLogger
from typing import Dict, Any, List, Optional
import logging

# Configure logging for tests
logging.basicConfig(level=logging.INFO)
logger = AuditLogger("test_validator")

class TestAbsolutePDifference:
    """Tests for absolute p-value difference > 0.05 threshold."""

    def test_absolute_p_difference_within_threshold(self):
        """When p-diff is <= 0.05, should not flag inconsistency."""
        reported_p = 0.04
        reconstructed_p = 0.03
        diff = calculate_absolute_p_difference(reported_p, reconstructed_p)
        assert abs(diff) <= 0.05
        assert check_p_value_consistency(reported_p, reconstructed_p, threshold=0.05) is True

    def test_absolute_p_difference_exceeds_threshold(self):
        """When p-diff is > 0.05, should flag inconsistency."""
        reported_p = 0.04
        reconstructed_p = 0.10
        diff = calculate_absolute_p_difference(reported_p, reconstructed_p)
        assert abs(diff) > 0.05
        assert check_p_value_consistency(reported_p, reconstructed_p, threshold=0.05) is False

    def test_absolute_p_difference_exact_boundary(self):
        """When p-diff is exactly 0.05, should pass (<= threshold)."""
        reported_p = 0.04
        reconstructed_p = 0.09
        diff = calculate_absolute_p_difference(reported_p, reconstructed_p)
        assert math.isclose(abs(diff), 0.05, rel_tol=1e-9)
        assert check_p_value_consistency(reported_p, reconstructed_p, threshold=0.05) is True

    def test_absolute_p_difference_with_zero_values(self):
        """Edge case: zero reported p-value."""
        reported_p = 0.0
        reconstructed_p = 0.06
        diff = calculate_absolute_p_difference(reported_p, reconstructed_p)
        assert abs(diff) > 0.05
        assert check_p_value_consistency(reported_p, reconstructed_p, threshold=0.05) is False

class TestRelativeEffectSizeDifference:
    """Tests for relative effect-size difference > 5% threshold."""

    def test_effect_size_within_threshold(self):
        """When relative diff is <= 5%, should not flag inconsistency."""
        reported_effect = 0.10
        reconstructed_effect = 0.104
        diff = calculate_relative_effect_size_difference(reported_effect, reconstructed_effect)
        assert abs(diff) <= 0.05
        assert check_effect_size_consistency(reported_effect, reconstructed_effect, threshold=0.05) is True

    def test_effect_size_exceeds_threshold(self):
        """When relative diff is > 5%, should flag inconsistency."""
        reported_effect = 0.10
        reconstructed_effect = 0.12
        diff = calculate_relative_effect_size_difference(reported_effect, reconstructed_effect)
        # (0.12 - 0.10) / 0.10 = 0.20 -> 20%
        assert abs(diff) > 0.05
        assert check_effect_size_consistency(reported_effect, reconstructed_effect, threshold=0.05) is False

    def test_effect_size_small_baseline(self):
        """Edge case: small baseline effect size amplifies relative diff."""
        reported_effect = 0.01
        reconstructed_effect = 0.011
        diff = calculate_relative_effect_size_difference(reported_effect, reconstructed_effect)
        # (0.011 - 0.01) / 0.01 = 0.10 -> 10%
        assert abs(diff) > 0.05
        assert check_effect_size_consistency(reported_effect, reconstructed_effect, threshold=0.05) is False

    def test_effect_size_zero_baseline(self):
        """Edge case: zero effect size should handle division safely."""
        reported_effect = 0.0
        reconstructed_effect = 0.01
        # Should return a large diff or handle gracefully
        diff = calculate_relative_effect_size_difference(reported_effect, reconstructed_effect)
        # If baseline is zero, any non-zero diff is effectively infinite relative error
        # The function should return a value > 0.05
        assert diff > 0.05 or math.isinf(diff)

class TestInequalityHandling:
    """Tests for handling p-value inequalities (e.g., p < 0.05)."""

    def test_inequality_p_less_than(self):
        """When reported p is '< 0.05', treat as 0.05 for comparison."""
        reported_p_str = "< 0.05"
        reconstructed_p = 0.06
        # The validator should parse "< 0.05" as 0.05
        # 0.05 vs 0.06 -> diff = 0.01 (within threshold)
        assert check_p_value_consistency(reported_p_str, reconstructed_p, threshold=0.05) is True

    def test_inequality_p_greater_than(self):
        """When reported p is '> 0.10', treat as 0.10 for comparison."""
        reported_p_str = "> 0.10"
        reconstructed_p = 0.08
        # 0.10 vs 0.08 -> diff = 0.02 (within threshold)
        assert check_p_value_consistency(reported_p_str, reconstructed_p, threshold=0.05) is True

    def test_inequality_p_less_than_exceeds(self):
        """When reconstructed p is much larger than '< 0.05'."""
        reported_p_str = "< 0.05"
        reconstructed_p = 0.12
        # 0.05 vs 0.12 -> diff = 0.07 (exceeds threshold)
        assert check_p_value_consistency(reported_p_str, reconstructed_p, threshold=0.05) is False

    def test_inequality_p_less_than_small(self):
        """When reported p is '< 0.01' and reconstructed is 0.02."""
        reported_p_str = "< 0.01"
        reconstructed_p = 0.02
        # 0.01 vs 0.02 -> diff = 0.01 (within threshold)
        assert check_p_value_consistency(reported_p_str, reconstructed_p, threshold=0.05) is True

class TestSampleSizeMismatch:
    """Tests for sample-size mismatch detection and warning generation."""

    def test_sample_sizes_match(self):
        """When sample sizes match, no mismatch detected."""
        n_control = 1000
        n_treatment = 1000
        assert detect_sample_size_mismatch(n_control, n_treatment) is False

    def test_sample_sizes_mismatch(self):
        """When sample sizes differ significantly, mismatch detected."""
        n_control = 1000
        n_treatment = 1200
        # Assuming a threshold of 10% mismatch
        assert detect_sample_size_mismatch(n_control, n_treatment) is True

    def test_sample_sizes_slight_mismatch(self):
        """Small mismatch (1%) should not trigger."""
        n_control = 1000
        n_treatment = 1010
        assert detect_sample_size_mismatch(n_control, n_treatment) is False

    def test_sample_sizes_large_mismatch(self):
        """Large mismatch (50%) should trigger."""
        n_control = 1000
        n_treatment = 1500
        assert detect_sample_size_mismatch(n_control, n_treatment) is True

class TestDataQualityWarningGeneration:
    """Tests for data_quality_warning generation in AuditRecord."""

    def test_warning_generated_on_sample_size_mismatch(self):
        """When sample sizes mismatch, AuditRecord should have data_quality_warning."""
        summary = ABTestSummary(
            url="https://example.com/test",
            domain="example.com",
            n_control=1000,
            n_treatment=1500,
            baseline_rate=0.10,
            variant_rate=0.12,
            reported_p_value=0.03,
            outcome_type="binary",
            test_type="z-test"
        )
        
        audit_record = validate_summary(summary, logger=logger)
        
        assert audit_record is not None
        assert audit_record.data_quality_warning is True
        assert "sample-size mismatch" in audit_record.audit_notes.lower()

    def test_no_warning_when_sizes_match(self):
        """When sample sizes match, no data_quality_warning."""
        summary = ABTestSummary(
            url="https://example.com/test",
            domain="example.com",
            n_control=1000,
            n_treatment=1000,
            baseline_rate=0.10,
            variant_rate=0.12,
            reported_p_value=0.03,
            outcome_type="binary",
            test_type="z-test"
        )
        
        audit_record = validate_summary(summary, logger=logger)
        
        assert audit_record is not None
        assert audit_record.data_quality_warning is False

    def test_warning_generated_on_p_value_inconsistency(self):
        """When p-value inconsistency detected, AuditRecord flagged."""
        summary = ABTestSummary(
            url="https://example.com/test",
            domain="example.com",
            n_control=1000,
            n_treatment=1000,
            baseline_rate=0.10,
            variant_rate=0.12,
            reported_p_value=0.01,
            reconstructed_p_value=0.08,
            outcome_type="binary",
            test_type="z-test"
        )
        
        audit_record = validate_summary(summary, logger=logger)
        
        assert audit_record is not None
        assert audit_record.is_inconsistent is True
        assert "p-value inconsistency" in audit_record.audit_notes.lower()

class TestValidateAllSummaries:
    """Tests for batch validation of multiple summaries."""

    def test_validate_all_summaries_empty_list(self):
        """Empty list should return empty list of records."""
        records = validate_all_summaries([], logger=logger)
        assert records == []

    def test_validate_all_summaries_mixed_results(self):
        """List with mixed consistent/inconsistent results."""
        summaries = [
            ABTestSummary(
                url="https://example.com/test1",
                domain="example.com",
                n_control=1000,
                n_treatment=1000,
                baseline_rate=0.10,
                variant_rate=0.12,
                reported_p_value=0.03,
                reconstructed_p_value=0.035,
                outcome_type="binary",
                test_type="z-test"
            ),
            ABTestSummary(
                url="https://example.com/test2",
                domain="example.com",
                n_control=1000,
                n_treatment=1500,
                baseline_rate=0.10,
                variant_rate=0.12,
                reported_p_value=0.01,
                reconstructed_p_value=0.08,
                outcome_type="binary",
                test_type="z-test"
            )
        ]
        
        records = validate_all_summaries(summaries, logger=logger)
        
        assert len(records) == 2
        assert records[0].is_inconsistent is False
        assert records[1].is_inconsistent is True
        assert records[1].data_quality_warning is True

class TestCreateAuditRecord:
    """Tests for AuditRecord creation logic."""

    def test_create_audit_record_basic(self):
        """Basic record creation with minimal fields."""
        summary = ABTestSummary(
            url="https://example.com/test",
            domain="example.com",
            n_control=1000,
            n_treatment=1000,
            baseline_rate=0.10,
            variant_rate=0.12,
            reported_p_value=0.03,
            outcome_type="binary",
            test_type="z-test"
        )
        
        record = create_audit_record(
            summary=summary,
            is_inconsistent=False,
            p_difference=0.005,
            effect_size_difference=0.01,
            sample_size_mismatch=False,
            audit_notes="All checks passed",
            logger=logger
        )
        
        assert record.url == "https://example.com/test"
        assert record.domain == "example.com"
        assert record.is_inconsistent is False
        assert record.data_quality_warning is False

    def test_create_audit_record_with_warnings(self):
        """Record creation with multiple flags."""
        summary = ABTestSummary(
            url="https://example.com/test",
            domain="example.com",
            n_control=1000,
            n_treatment=1500,
            baseline_rate=0.10,
            variant_rate=0.12,
            reported_p_value=0.01,
            outcome_type="binary",
            test_type="z-test"
        )
        
        record = create_audit_record(
            summary=summary,
            is_inconsistent=True,
            p_difference=0.07,
            effect_size_difference=0.06,
            sample_size_mismatch=True,
            audit_notes="Multiple inconsistencies detected",
            logger=logger
        )
        
        assert record.is_inconsistent is True
        assert record.data_quality_warning is True
        assert "sample-size mismatch" in record.audit_notes.lower()