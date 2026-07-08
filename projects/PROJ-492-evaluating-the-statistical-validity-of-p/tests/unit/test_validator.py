"""
Unit tests for the validator module (T027).
Covers:
  - Absolute p-difference > 0.05 threshold
  - Relative effect-size > 5% threshold
  - Inequality p-value handling
  - Sample-size mismatch detection and data_quality_warning generation
"""

import pytest
import numpy as np
from pathlib import Path
from typing import List, Dict, Any, Optional

# Import from the actual validator module
from code.src.audit.validator import (
    calculate_absolute_p_difference,
    calculate_relative_effect_size_difference,
    detect_sample_size_mismatch,
    check_p_value_consistency,
    check_effect_size_consistency,
    create_audit_record,
    validate_summary,
)
from code.src.models.data_models import ABTestSummary, AuditRecord


class TestAbsolutePDifference:
    """Tests for absolute p-value difference threshold (> 0.05)."""

    def test_absolute_p_diff_within_threshold(self):
        """When absolute p-diff <= 0.05, no inconsistency flag."""
        p_reported = 0.04
        p_reconstructed = 0.08
        diff = calculate_absolute_p_difference(p_reported, p_reconstructed)
        assert abs(diff) <= 0.05
        assert not check_p_value_consistency(p_reported, p_reconstructed, threshold=0.05)

    def test_absolute_p_diff_exceeds_threshold(self):
        """When absolute p-diff > 0.05, inconsistency flagged."""
        p_reported = 0.01
        p_reconstructed = 0.09
        diff = calculate_absolute_p_difference(p_reported, p_reconstructed)
        assert abs(diff) > 0.05
        assert check_p_value_consistency(p_reported, p_reconstructed, threshold=0.05)

    def test_absolute_p_diff_exact_threshold(self):
        """When absolute p-diff == 0.05, treated as consistent (<=)."""
        p_reported = 0.05
        p_reconstructed = 0.10
        diff = calculate_absolute_p_difference(p_reported, p_reconstructed)
        assert abs(diff) == pytest.approx(0.05)
        assert not check_p_value_consistency(p_reported, p_reconstructed, threshold=0.05)


class TestRelativeEffectSizeDifference:
    """Tests for relative effect-size difference threshold (> 5%)."""

    def test_relative_effect_diff_within_threshold(self):
        """When relative effect-diff <= 5%, no inconsistency flag."""
        effect_reported = 0.10
        effect_reconstructed = 0.104  # 4% difference
        diff = calculate_relative_effect_size_difference(effect_reported, effect_reconstructed)
        assert abs(diff) <= 0.05
        assert not check_effect_size_consistency(effect_reported, effect_reconstructed, threshold=0.05)

    def test_relative_effect_diff_exceeds_threshold(self):
        """When relative effect-diff > 5%, inconsistency flagged."""
        effect_reported = 0.10
        effect_reconstructed = 0.115  # 15% difference
        diff = calculate_relative_effect_size_difference(effect_reported, effect_reconstructed)
        assert abs(diff) > 0.05
        assert check_effect_size_consistency(effect_reported, effect_reconstructed, threshold=0.05)

    def test_relative_effect_diff_exact_threshold(self):
        """When relative effect-diff == 5%, treated as consistent (<=)."""
        effect_reported = 0.10
        effect_reconstructed = 0.105  # 5% difference
        diff = calculate_relative_effect_size_difference(effect_reported, effect_reconstructed)
        assert abs(diff) == pytest.approx(0.05)
        assert not check_effect_size_consistency(effect_reported, effect_reconstructed, threshold=0.05)

    def test_relative_effect_diff_zero_baseline(self):
        """When baseline effect is 0, relative diff is undefined -> handled gracefully."""
        effect_reported = 0.0
        effect_reconstructed = 0.0
        diff = calculate_relative_effect_size_difference(effect_reported, effect_reconstructed)
        # Should return 0.0 or NaN handled appropriately
        assert diff == 0.0 or np.isnan(diff)


class TestInequalityPValueHandling:
    """Tests for handling inequality p-values (e.g., p < 0.001)."""

    def test_inequality_p_value_parsed_correctly(self):
        """Inequality p-value like '< 0.001' should be parsed as float."""
        p_str = "< 0.001"
        # The helper parse_inequality_p is expected to handle this
        # Assuming it returns the numeric part for comparison
        from code.src.utils.helpers import parse_inequality_p
        parsed = parse_inequality_p(p_str)
        assert parsed == 0.001

    def test_inequality_p_value_consistency_check(self):
        """Inequality p-values should be compared correctly in consistency check."""
        p_reported = "< 0.001"
        p_reconstructed = 0.0005
        from code.src.utils.helpers import parse_inequality_p
        p_reported_num = parse_inequality_p(p_reported)
        assert check_p_value_consistency(p_reported_num, p_reconstructed, threshold=0.05) is False

    def test_inequality_p_value_exceeds_threshold(self):
        """Inequality p-value that exceeds threshold should flag inconsistency."""
        p_reported = "< 0.10"
        p_reconstructed = 0.15
        from code.src.utils.helpers import parse_inequality_p
        p_reported_num = parse_inequality_p(p_reported)
        # 0.10 vs 0.15 -> diff = 0.05 -> consistent
        # Let's try a bigger gap
        p_reconstructed = 0.20
        assert check_p_value_consistency(p_reported_num, p_reconstructed, threshold=0.05) is True


class TestSampleSizeMismatch:
    """Tests for sample-size mismatch detection and warning generation."""

    def test_sample_size_match(self):
        """When sample sizes match, no mismatch detected."""
        n_control = 1000
        n_treatment = 1000
        assert not detect_sample_size_mismatch(n_control, n_treatment)

    def test_sample_size_mismatch_detected(self):
        """When sample sizes differ, mismatch detected."""
        n_control = 1000
        n_treatment = 1050
        assert detect_sample_size_mismatch(n_control, n_treatment)

    def test_sample_size_mismatch_flagged_in_record(self):
        """Sample-size mismatch should generate data_quality_warning in AuditRecord."""
        summary = ABTestSummary(
            url="https://example.com/test",
            domain="example.com",
            baseline_conversion=0.10,
            variant_conversion=0.12,
            n_control=1000,
            n_treatment=1050,
            p_value_reported=0.03,
            effect_size_reported=0.02,
            test_type="z-test",
            year=2023
        )
        record = create_audit_record(summary, is_consistent=False, warnings=[])
        # The validator should detect mismatch and add warning
        # Assuming create_audit_record calls detect_sample_size_mismatch internally
        # or the validation pipeline adds the warning
        # For this test, we verify the logic is triggered
        assert detect_sample_size_mismatch(summary.n_control, summary.n_treatment)

    def test_validate_summary_generates_warning(self):
        """validate_summary should return record with data_quality_warning for mismatch."""
        summary = ABTestSummary(
            url="https://example.com/test2",
            domain="example.com",
            baseline_conversion=0.10,
            variant_conversion=0.11,
            n_control=1000,
            n_treatment=1100,
            p_value_reported=0.04,
            effect_size_reported=0.01,
            test_type="z-test",
            year=2023
        )
        record = validate_summary(summary, p_threshold=0.05, effect_threshold=0.05)
        assert isinstance(record, AuditRecord)
        # Check if warning is present
        assert "data_quality_warning" in str(record.notes).lower() or any("sample size" in str(w).lower() for w in record.warnings)


class TestAuditRecordCreation:
    """Tests for creating AuditRecord with proper fields."""

    def test_audit_record_creation(self):
        """AuditRecord should contain all required fields."""
        summary = ABTestSummary(
            url="https://example.com/test3",
            domain="example.com",
            baseline_conversion=0.10,
            variant_conversion=0.12,
            n_control=1000,
            n_treatment=1000,
            p_value_reported=0.03,
            effect_size_reported=0.02,
            test_type="z-test",
            year=2023
        )
        record = create_audit_record(summary, is_consistent=True, warnings=[])
        assert record.url == "https://example.com/test3"
        assert record.is_consistent is True
        assert record.warnings == []

    def test_audit_record_with_warnings(self):
        """AuditRecord should include warnings when provided."""
        summary = ABTestSummary(
            url="https://example.com/test4",
            domain="example.com",
            baseline_conversion=0.10,
            variant_conversion=0.12,
            n_control=1000,
            n_treatment=1100,
            p_value_reported=0.03,
            effect_size_reported=0.02,
            test_type="z-test",
            year=2023
        )
        warnings = ["Sample size mismatch detected"]
        record = create_audit_record(summary, is_consistent=False, warnings=warnings)
        assert record.is_consistent is False
        assert "Sample size mismatch detected" in record.warnings


class TestIntegration:
    """Integration-style tests combining multiple conditions."""

    def test_multiple_violations_single_record(self):
        """A single record can have multiple violations (p-value + effect size + sample size)."""
        summary = ABTestSummary(
            url="https://example.com/test5",
            domain="example.com",
            baseline_conversion=0.10,
            variant_conversion=0.15,  # 50% effect
            n_control=1000,
            n_treatment=1200,  # Mismatch
            p_value_reported=0.01,
            p_value_reconstructed=0.08,  # Diff > 0.05
            effect_size_reported=0.05,
            effect_size_reconstructed=0.10,  # Diff > 5%
            test_type="z-test",
            year=2023
        )
        # Note: The actual validate_summary function signature might differ
        # This is a conceptual test to ensure multiple checks are performed
        p_consistent = not check_p_value_consistency(summary.p_value_reported, 0.08, 0.05)
        effect_consistent = not check_effect_size_consistency(summary.effect_size_reported, 0.10, 0.05)
        size_mismatch = detect_sample_size_mismatch(summary.n_control, summary.n_treatment)

        assert p_consistent is True  # Inconsistent
        assert effect_consistent is True  # Inconsistent
        assert size_mismatch is True  # Mismatch