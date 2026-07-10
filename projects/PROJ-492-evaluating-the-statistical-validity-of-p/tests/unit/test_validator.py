"""
Unit tests for the validator module covering:
- Absolute p-value difference > 0.05 threshold
- Relative effect-size difference > 5% threshold
- Inequality p-value handling
- Sample-size mismatch detection and data_quality_warning generation
"""

import json
import pytest
from pathlib import Path
from typing import Dict, Any, List

from code.src.models.data_models import ABTestSummary, AuditRecord
from code.src.audit.validator import (
    validate_single_summary,
    validate_all_summaries,
    check_p_value_consistency,
    check_effect_size_consistency,
    check_sample_size_consistency,
    apply_validation_rules
)
from code.src.utils.logger import get_error_message, AuditLogger


class TestPValueConsistency:
    """Tests for absolute p-value difference threshold (FR-004)"""

    def test_p_difference_within_threshold(self):
        """p-value difference <= 0.05 should pass"""
        reconstructed_p = 0.042
        reported_p = 0.045
        result = check_p_value_consistency(reconstructed_p, reported_p)
        
        assert result["is_consistent"] is True
        assert result["p_difference"] <= 0.05

    def test_p_difference_exceeds_threshold(self):
        """p-value difference > 0.05 should fail"""
        reconstructed_p = 0.03
        reported_p = 0.10
        result = check_p_value_consistency(reconstructed_p, reported_p)
        
        assert result["is_consistent"] is False
        assert result["p_difference"] > 0.05
        assert result["violation_type"] == "p_value_threshold"

    def test_p_difference_exact_threshold_boundary(self):
        """p-value difference exactly 0.05 should pass (boundary case)"""
        reconstructed_p = 0.05
        reported_p = 0.10
        result = check_p_value_consistency(reconstructed_p, reported_p)
        
        assert result["is_consistent"] is True
        assert abs(result["p_difference"] - 0.05) < 1e-9


class TestEffectSizeConsistency:
    """Tests for relative effect-size difference threshold (FR-004)"""

    def test_effect_size_within_threshold(self):
        """Relative effect-size difference <= 5% should pass"""
        reconstructed_effect = 0.10
        reported_effect = 0.104
        result = check_effect_size_consistency(reconstructed_effect, reported_effect)
        
        assert result["is_consistent"] is True
        assert result["relative_difference"] <= 0.05

    def test_effect_size_exceeds_threshold(self):
        """Relative effect-size difference > 5% should fail"""
        reconstructed_effect = 0.10
        reported_effect = 0.12
        result = check_effect_size_consistency(reconstructed_effect, reported_effect)
        
        assert result["is_consistent"] is False
        assert result["relative_difference"] > 0.05
        assert result["violation_type"] == "effect_size_threshold"

    def test_effect_size_zero_baseline(self):
        """Zero reported effect size should handle gracefully"""
        reconstructed_effect = 0.05
        reported_effect = 0.0
        result = check_effect_size_consistency(reconstructed_effect, reported_effect)
        
        # Should flag as inconsistent due to division by zero or large relative diff
        assert result["is_consistent"] is False


class TestInequalityHandling:
    """Tests for inequality p-value handling (e.g., p < 0.001)"""

    def test_inequality_p_value_parsed_correctly(self):
        """Inequality p-value should be converted to numeric for comparison"""
        # When reported_p is "p < 0.001", we use 0.001 as the value
        reconstructed_p = 0.0005
        reported_p_str = "p < 0.001"
        
        # The validator should handle this by parsing the numeric part
        result = check_p_value_consistency(reconstructed_p, reported_p_str)
        
        # Should be consistent since 0.0005 < 0.001
        assert result["is_consistent"] is True

    def test_inequality_p_value_exceeds_threshold(self):
        """Inequality p-value that violates threshold should fail"""
        reconstructed_p = 0.02
        reported_p_str = "p < 0.001"
        
        result = check_p_value_consistency(reconstructed_p, reported_p_str)
        
        # 0.02 vs 0.001 -> difference > 0.05
        assert result["is_consistent"] is False

    def test_greater_than_inequality(self):
        """Handle p > 0.05 cases"""
        reconstructed_p = 0.08
        reported_p_str = "p > 0.05"
        
        result = check_p_value_consistency(reconstructed_p, reported_p_str)
        
        # Should use 0.05 as the boundary for comparison
        assert result["is_consistent"] is True  # 0.08 vs 0.05 diff is 0.03


class TestSampleSizeMismatch:
    """Tests for sample-size mismatch detection and warning generation"""

    def test_matching_sample_sizes(self):
        """Matching sample sizes should not trigger warning"""
        summary = ABTestSummary(
            url="http://example.com/test",
            domain="example.com",
            baseline_n=1000,
            treatment_n=1000,
            baseline_rate=0.10,
            treatment_rate=0.12,
            reported_p_value=0.045,
            test_type="binary"
        )
        
        result = check_sample_size_consistency(summary)
        
        assert result["is_consistent"] is True
        assert result["has_warning"] is False

    def test_mismatched_sample_sizes(self):
        """Mismatched sample sizes should trigger data_quality_warning"""
        summary = ABTestSummary(
            url="http://example.com/test",
            domain="example.com",
            baseline_n=1000,
            treatment_n=1500,  # Different from baseline
            baseline_rate=0.10,
            treatment_rate=0.12,
            reported_p_value=0.045,
            test_type="binary"
        )
        
        result = check_sample_size_consistency(summary)
        
        assert result["is_consistent"] is False
        assert result["has_warning"] is True
        assert "sample_size_mismatch" in result["violation_type"]

    def test_missing_sample_size(self):
        """Missing sample size should trigger warning"""
        summary = ABTestSummary(
            url="http://example.com/test",
            domain="example.com",
            baseline_n=None,
            treatment_n=1000,
            baseline_rate=0.10,
            treatment_rate=0.12,
            reported_p_value=0.045,
            test_type="binary"
        )
        
        result = check_sample_size_consistency(summary)
        
        assert result["has_warning"] is True
        assert "missing_sample_size" in result["violation_type"]


class TestAuditRecordGeneration:
    """Tests that AuditRecord objects are correctly generated with warnings"""

    def test_audit_record_with_p_value_violation(self):
        """AuditRecord should include p_value_violation in notes"""
        summary = ABTestSummary(
            url="http://example.com/test1",
            domain="example.com",
            baseline_n=1000,
            treatment_n=1000,
            baseline_rate=0.10,
            treatment_rate=0.12,
            reported_p_value=0.10,
            reconstructed_p_value=0.03,
            test_type="binary"
        )
        
        audit_record = validate_single_summary(summary)
        
        assert isinstance(audit_record, AuditRecord)
        assert audit_record.url == summary.url
        assert audit_record.is_inconsistent is True
        assert "p_value" in audit_record.notes.lower() or "inconsistent" in audit_record.notes.lower()

    def test_audit_record_with_sample_size_warning(self):
        """AuditRecord should include data_quality_warning for sample-size mismatch"""
        summary = ABTestSummary(
            url="http://example.com/test2",
            domain="example.com",
            baseline_n=1000,
            treatment_n=2000,
            baseline_rate=0.10,
            treatment_rate=0.12,
            reported_p_value=0.045,
            reconstructed_p_value=0.042,
            test_type="binary"
        )
        
        audit_record = validate_single_summary(summary)
        
        assert isinstance(audit_record, AuditRecord)
        assert audit_record.has_data_quality_warning is True
        assert "sample_size" in audit_record.notes.lower()

    def test_audit_record_consistent_no_warnings(self):
        """Consistent summary should have no warnings"""
        summary = ABTestSummary(
            url="http://example.com/test3",
            domain="example.com",
            baseline_n=1000,
            treatment_n=1000,
            baseline_rate=0.10,
            treatment_rate=0.12,
            reported_p_value=0.045,
            reconstructed_p_value=0.044,
            test_type="binary"
        )
        
        audit_record = validate_single_summary(summary)
        
        assert isinstance(audit_record, AuditRecord)
        assert audit_record.is_inconsistent is False
        assert audit_record.has_data_quality_warning is False


class TestValidateAllSummaries:
    """Tests for batch validation of multiple summaries"""

    def test_mixed_consistency_results(self):
        """Batch validation should correctly classify mixed results"""
        summaries = [
            ABTestSummary(
                url="http://example.com/consistent",
                domain="example.com",
                baseline_n=1000,
                treatment_n=1000,
                baseline_rate=0.10,
                treatment_rate=0.12,
                reported_p_value=0.045,
                reconstructed_p_value=0.044,
                test_type="binary"
            ),
            ABTestSummary(
                url="http://example.com/inconsistent",
                domain="example.com",
                baseline_n=1000,
                treatment_n=1000,
                baseline_rate=0.10,
                treatment_rate=0.12,
                reported_p_value=0.10,
                reconstructed_p_value=0.03,
                test_type="binary"
            )
        ]
        
        records = validate_all_summaries(summaries)
        
        assert len(records) == 2
        consistent_count = sum(1 for r in records if not r.is_inconsistent)
        inconsistent_count = sum(1 for r in records if r.is_inconsistent)
        
        assert consistent_count == 1
        assert inconsistent_count == 1

    def test_all_have_sample_size_warnings(self):
        """All records with sample-size mismatch should have warnings"""
        summaries = [
            ABTestSummary(
                url=f"http://example.com/test{i}",
                domain="example.com",
                baseline_n=1000,
                treatment_n=1500,
                baseline_rate=0.10,
                treatment_rate=0.12,
                reported_p_value=0.045,
                reconstructed_p_value=0.044,
                test_type="binary"
            )
            for i in range(3)
        ]
        
        records = validate_all_summaries(summaries)
        
        assert all(r.has_data_quality_warning for r in records)
        assert all("sample_size" in r.notes.lower() for r in records)


class TestValidationThresholds:
    """Integration tests for the exact thresholds specified in FR-004"""

    def test_absolute_p_threshold_0_05(self):
        """Verify the exact 0.05 threshold from FR-004"""
        # Edge case: exactly 0.05 difference should pass
        result_pass = check_p_value_consistency(0.05, 0.10)
        assert result_pass["is_consistent"] is True
        
        # Just over 0.05 should fail
        result_fail = check_p_value_consistency(0.05, 0.1001)
        assert result_fail["is_consistent"] is False

    def test_relative_effect_size_5_percent(self):
        """Verify the exact 5% threshold from FR-004"""
        # 5% relative difference should pass
        result_pass = check_effect_size_consistency(0.10, 0.105)
        assert result_pass["is_consistent"] is True
        
        # Just over 5% should fail
        result_fail = check_effect_size_consistency(0.10, 0.1051)
        assert result_fail["is_consistent"] is False


class TestDataQualityWarningGeneration:
    """Specific tests for data_quality_warning field in AuditRecord"""

    def test_warning_generated_for_sample_mismatch(self):
        """data_quality_warning should be True when sample sizes mismatch"""
        summary = ABTestSummary(
            url="http://example.com/mismatch",
            domain="example.com",
            baseline_n=500,
            treatment_n=800,
            baseline_rate=0.15,
            treatment_rate=0.18,
            reported_p_value=0.04,
            reconstructed_p_value=0.039,
            test_type="binary"
        )
        
        record = validate_single_summary(summary)
        
        assert record.has_data_quality_warning is True
        assert "sample" in record.notes.lower() or "mismatch" in record.notes.lower()

    def test_warning_not_generated_for_consistent_sample(self):
        """data_quality_warning should be False when samples match"""
        summary = ABTestSummary(
            url="http://example.com/match",
            domain="example.com",
            baseline_n=500,
            treatment_n=500,
            baseline_rate=0.15,
            treatment_rate=0.18,
            reported_p_value=0.04,
            reconstructed_p_value=0.039,
            test_type="binary"
        )
        
        record = validate_single_summary(summary)
        
        assert record.has_data_quality_warning is False

    def test_warning_independent_of_p_value_consistency(self):
        """Sample-size warning should be generated even if p-values are consistent"""
        summary = ABTestSummary(
            url="http://example.com/both",
            domain="example.com",
            baseline_n=500,
            treatment_n=900,  # Mismatch
            baseline_rate=0.15,
            treatment_rate=0.18,
            reported_p_value=0.04,
            reconstructed_p_value=0.039,  # Consistent
            test_type="binary"
        )
        
        record = validate_single_summary(summary)
        
        # P-value is consistent
        assert record.is_inconsistent is False
        # But sample-size warning is present
        assert record.has_data_quality_warning is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])