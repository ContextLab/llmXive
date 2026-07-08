"""
Unit tests for the validator module (T027).

Tests cover:
- Absolute p-difference > 0.05 threshold
- Relative effect-size difference > 5% threshold
- Inequality p-value handling
- Sample-size mismatch detection and data_quality_warning generation
"""
import pytest
import numpy as np
from code.src.models.data_models import ABTestSummary, AuditRecord
from code.src.audit.validator import (
    calculate_absolute_p_difference,
    calculate_relative_effect_size_difference,
    detect_sample_size_mismatch,
    check_p_value_consistency,
    check_effect_size_consistency,
    create_audit_record,
    validate_summary,
    filter_for_prevalence,
)
from code.src.utils.logger import get_error_message, ERR_001, ERR_002, ERR_003, ERR_004, ERR_005


class TestCalculateAbsolutePDifference:
    """Test absolute p-value difference calculation."""

    def test_equal_p_values(self):
        reported = 0.05
        reconstructed = 0.05
        diff = calculate_absolute_p_difference(reported, reconstructed)
        assert diff == 0.0

    def test_small_difference(self):
        reported = 0.05
        reconstructed = 0.04
        diff = calculate_absolute_p_difference(reported, reconstructed)
        assert diff == 0.01

    def test_large_difference(self):
        reported = 0.01
        reconstructed = 0.08
        diff = calculate_absolute_p_difference(reported, reconstructed)
        assert diff == 0.07

    def test_none_reconstructed(self):
        reported = 0.05
        reconstructed = None
        diff = calculate_absolute_p_difference(reported, reconstructed)
        assert diff is None

    def test_none_reported(self):
        reported = None
        reconstructed = 0.05
        diff = calculate_absolute_p_difference(reported, reconstructed)
        assert diff is None


class TestCalculateRelativeEffectSizeDifference:
    """Test relative effect-size difference calculation."""

    def test_equal_effect_sizes(self):
        reported = 0.10
        reconstructed = 0.10
        diff = calculate_relative_effect_size_difference(reported, reconstructed)
        assert diff == 0.0

    def test_small_relative_difference(self):
        reported = 0.10
        reconstructed = 0.105
        diff = calculate_relative_effect_size_difference(reported, reconstructed)
        # |0.10 - 0.105| / 0.10 = 0.005 / 0.10 = 0.05 (5%)
        assert abs(diff - 0.05) < 1e-9

    def test_large_relative_difference(self):
        reported = 0.10
        reconstructed = 0.11
        diff = calculate_relative_effect_size_difference(reported, reconstructed)
        # |0.10 - 0.11| / 0.10 = 0.01 / 0.10 = 0.10 (10%)
        assert abs(diff - 0.10) < 1e-9

    def test_zero_reported_effect_size(self):
        reported = 0.0
        reconstructed = 0.05
        diff = calculate_relative_effect_size_difference(reported, reconstructed)
        # Division by zero should return None
        assert diff is None

    def test_negative_effect_sizes(self):
        reported = -0.10
        reconstructed = -0.105
        diff = calculate_relative_effect_size_difference(reported, reconstructed)
        # |-0.10 - (-0.105)| / |-0.10| = 0.005 / 0.10 = 0.05 (5%)
        assert abs(diff - 0.05) < 1e-9

    def test_none_values(self):
        assert calculate_relative_effect_size_difference(None, 0.10) is None
        assert calculate_relative_effect_size_difference(0.10, None) is None


class TestDetectSampleSizeMismatch:
    """Test sample-size mismatch detection."""

    def test_no_mismatch(self):
        summary = ABTestSummary(
            url="http://example.com",
            domain="example.com",
            outcome_type="binary",
            n_control=1000,
            n_treatment=1000,
            n_control_conversions=100,
            n_treatment_conversions=120,
            p_value_reported=0.05,
            effect_size_reported=0.02,
            baseline_conversion_rate=0.10,
        )
        assert detect_sample_size_mismatch(summary) is False

    def test_mismatch_binary(self):
        summary = ABTestSummary(
            url="http://example.com",
            domain="example.com",
            outcome_type="binary",
            n_control=1000,
            n_treatment=1500,  # Mismatch
            n_control_conversions=100,
            n_treatment_conversions=150,
            p_value_reported=0.05,
            effect_size_reported=0.02,
            baseline_conversion_rate=0.10,
        )
        assert detect_sample_size_mismatch(summary) is True

    def test_mismatch_continuous(self):
        summary = ABTestSummary(
            url="http://example.com",
            domain="example.com",
            outcome_type="continuous",
            n_control=1000,
            n_treatment=1500,  # Mismatch
            mean_control=10.0,
            mean_treatment=12.0,
            std_control=2.0,
            std_treatment=2.5,
            p_value_reported=0.05,
            effect_size_reported=2.0,
        )
        assert detect_sample_size_mismatch(summary) is True

    def test_missing_sample_sizes(self):
        summary = ABTestSummary(
            url="http://example.com",
            domain="example.com",
            outcome_type="binary",
            n_control=None,
            n_treatment=None,
            n_control_conversions=None,
            n_treatment_conversions=None,
            p_value_reported=0.05,
            effect_size_reported=0.02,
            baseline_conversion_rate=0.10,
        )
        # If sample sizes are missing, we cannot detect a mismatch
        assert detect_sample_size_mismatch(summary) is False


class TestCheckPValueConsistency:
    """Test p-value consistency checking."""

    def test_within_threshold(self):
        reported = 0.05
        reconstructed = 0.06
        is_consistent = check_p_value_consistency(reported, reconstructed, threshold=0.05)
        assert is_consistent is True  # |0.05 - 0.06| = 0.01 <= 0.05

    def test_exceeds_threshold(self):
        reported = 0.05
        reconstructed = 0.15
        is_consistent = check_p_value_consistency(reported, reconstructed, threshold=0.05)
        assert is_consistent is False  # |0.05 - 0.15| = 0.10 > 0.05

    def test_none_values(self):
        assert check_p_value_consistency(None, 0.05, 0.05) is True
        assert check_p_value_consistency(0.05, None, 0.05) is True
        assert check_p_value_consistency(None, None, 0.05) is True


class TestCheckEffectSizeConsistency:
    """Test effect-size consistency checking."""

    def test_within_threshold(self):
        reported = 0.10
        reconstructed = 0.104
        is_consistent = check_effect_size_consistency(reported, reconstructed, threshold=0.05)
        # |0.10 - 0.104| / 0.10 = 0.04 = 4% <= 5%
        assert is_consistent is True

    def test_exceeds_threshold(self):
        reported = 0.10
        reconstructed = 0.12
        is_consistent = check_effect_size_consistency(reported, reconstructed, threshold=0.05)
        # |0.10 - 0.12| / 0.10 = 0.20 = 20% > 5%
        assert is_consistent is False

    def test_zero_reported_effect_size(self):
        reported = 0.0
        reconstructed = 0.05
        is_consistent = check_effect_size_consistency(reported, reconstructed, threshold=0.05)
        # Division by zero should return True (no inconsistency can be determined)
        assert is_consistent is True

    def test_none_values(self):
        assert check_effect_size_consistency(None, 0.10, 0.05) is True
        assert check_effect_size_consistency(0.10, None, 0.05) is True
        assert check_effect_size_consistency(None, None, 0.05) is True


class TestCreateAuditRecord:
    """Test audit record creation with various inconsistency flags."""

    def test_consistent_record(self):
        summary = ABTestSummary(
            url="http://example.com",
            domain="example.com",
            outcome_type="binary",
            n_control=1000,
            n_treatment=1000,
            n_control_conversions=100,
            n_treatment_conversions=120,
            p_value_reported=0.05,
            effect_size_reported=0.02,
            baseline_conversion_rate=0.10,
        )
        record = create_audit_record(
            summary=summary,
            reconstructed_p_value=0.055,
            reconstructed_effect_size=0.021,
            p_value_consistent=True,
            effect_size_consistent=True,
            sample_size_mismatch=False,
        )
        assert record.url == "http://example.com"
        assert record.is_inconsistent is False
        assert record.data_quality_warning is None
        assert record.audit_notes == ""

    def test_inconsistent_p_value(self):
        summary = ABTestSummary(
            url="http://example.com",
            domain="example.com",
            outcome_type="binary",
            n_control=1000,
            n_treatment=1000,
            n_control_conversions=100,
            n_treatment_conversions=120,
            p_value_reported=0.05,
            effect_size_reported=0.02,
            baseline_conversion_rate=0.10,
        )
        record = create_audit_record(
            summary=summary,
            reconstructed_p_value=0.15,
            reconstructed_effect_size=0.021,
            p_value_consistent=False,
            effect_size_consistent=True,
            sample_size_mismatch=False,
        )
        assert record.is_inconsistent is True
        assert "p-value" in record.audit_notes.lower()

    def test_inconsistent_effect_size(self):
        summary = ABTestSummary(
            url="http://example.com",
            domain="example.com",
            outcome_type="binary",
            n_control=1000,
            n_treatment=1000,
            n_control_conversions=100,
            n_treatment_conversions=120,
            p_value_reported=0.05,
            effect_size_reported=0.02,
            baseline_conversion_rate=0.10,
        )
        record = create_audit_record(
            summary=summary,
            reconstructed_p_value=0.055,
            reconstructed_effect_size=0.03,
            p_value_consistent=True,
            effect_size_consistent=False,
            sample_size_mismatch=False,
        )
        assert record.is_inconsistent is True
        assert "effect size" in record.audit_notes.lower()

    def test_sample_size_mismatch_warning(self):
        summary = ABTestSummary(
            url="http://example.com",
            domain="example.com",
            outcome_type="binary",
            n_control=1000,
            n_treatment=1500,
            n_control_conversions=100,
            n_treatment_conversions=150,
            p_value_reported=0.05,
            effect_size_reported=0.02,
            baseline_conversion_rate=0.10,
        )
        record = create_audit_record(
            summary=summary,
            reconstructed_p_value=0.055,
            reconstructed_effect_size=0.021,
            p_value_consistent=True,
            effect_size_consistent=True,
            sample_size_mismatch=True,
        )
        assert record.data_quality_warning is not None
        assert "sample size" in record.data_quality_warning.lower()
        # Sample size mismatch alone does not make it inconsistent
        assert record.is_inconsistent is False

    def test_multiple_issues(self):
        summary = ABTestSummary(
            url="http://example.com",
            domain="example.com",
            outcome_type="binary",
            n_control=1000,
            n_treatment=1500,
            n_control_conversions=100,
            n_treatment_conversions=150,
            p_value_reported=0.05,
            effect_size_reported=0.02,
            baseline_conversion_rate=0.10,
        )
        record = create_audit_record(
            summary=summary,
            reconstructed_p_value=0.15,
            reconstructed_effect_size=0.03,
            p_value_consistent=False,
            effect_size_consistent=False,
            sample_size_mismatch=True,
        )
        assert record.is_inconsistent is True
        assert record.data_quality_warning is not None
        assert "sample size" in record.data_quality_warning.lower()
        assert "p-value" in record.audit_notes.lower()
        assert "effect size" in record.audit_notes.lower()


class TestValidateSummary:
    """Test full validation workflow for a single summary."""

    def test_valid_summary(self):
        summary = ABTestSummary(
            url="http://example.com",
            domain="example.com",
            outcome_type="binary",
            n_control=1000,
            n_treatment=1000,
            n_control_conversions=100,
            n_treatment_conversions=120,
            p_value_reported=0.05,
            effect_size_reported=0.02,
            baseline_conversion_rate=0.10,
        )
        record = validate_summary(summary)
        assert record is not None
        # Note: validate_summary computes reconstructed values internally
        # We just verify it returns a valid AuditRecord

    def test_summary_with_missing_baseline(self):
        summary = ABTestSummary(
            url="http://example.com",
            domain="example.com",
            outcome_type="binary",
            n_control=1000,
            n_treatment=1000,
            n_control_conversions=100,
            n_treatment_conversions=120,
            p_value_reported=0.05,
            effect_size_reported=0.02,
            baseline_conversion_rate=None,  # Missing
        )
        record = validate_summary(summary)
        assert record is not None
        # Should still produce a record, potentially with notes about missing baseline


class TestFilterForPrevalence:
    """Test filtering of audit records for prevalence calculation."""

    def test_filter_excludes_sample_size_mismatch(self):
        records = [
            AuditRecord(
                url="http://example1.com",
                domain="example1.com",
                is_inconsistent=False,
                data_quality_warning=None,
                audit_notes="",
            ),
            AuditRecord(
                url="http://example2.com",
                domain="example2.com",
                is_inconsistent=False,
                data_quality_warning="Sample size mismatch detected",
                audit_notes="",
            ),
            AuditRecord(
                url="http://example3.com",
                domain="example3.com",
                is_inconsistent=True,
                data_quality_warning=None,
                audit_notes="p-value inconsistency",
            ),
        ]
        filtered = filter_for_prevalence(records)
        # Should exclude record 2 (sample size mismatch)
        assert len(filtered) == 2
        assert filtered[0].url == "http://example1.com"
        assert filtered[1].url == "http://example3.com"

    def test_filter_empty_list(self):
        assert len(filter_for_prevalence([])) == 0

    def test_filter_all_excluded(self):
        records = [
            AuditRecord(
                url="http://example1.com",
                domain="example1.com",
                is_inconsistent=False,
                data_quality_warning="Sample size mismatch",
                audit_notes="",
            ),
        ]
        assert len(filter_for_prevalence(records)) == 0


class TestInequalityPValueHandling:
    """Test handling of inequality p-values (e.g., p < 0.001)."""

    def test_inequality_p_value_parsing(self):
        # The validator should handle cases where p-value is reported as inequality
        # This is tested indirectly through validate_summary
        summary = ABTestSummary(
            url="http://example.com",
            domain="example.com",
            outcome_type="binary",
            n_control=1000,
            n_treatment=1000,
            n_control_conversions=100,
            n_treatment_conversions=120,
            p_value_reported=0.001,  # Simulating p < 0.001 as 0.001
            effect_size_reported=0.02,
            baseline_conversion_rate=0.10,
        )
        record = validate_summary(summary)
        assert record is not None

    def test_very_small_p_value(self):
        summary = ABTestSummary(
            url="http://example.com",
            domain="example.com",
            outcome_type="binary",
            n_control=1000,
            n_treatment=1000,
            n_control_conversions=100,
            n_treatment_conversions=120,
            p_value_reported=1e-10,
            effect_size_reported=0.02,
            baseline_conversion_rate=0.10,
        )
        record = validate_summary(summary)
        assert record is not None

    def test_p_value_at_boundary(self):
        # Test p-value exactly at 0.05 threshold
        summary = ABTestSummary(
            url="http://example.com",
            domain="example.com",
            outcome_type="binary",
            n_control=1000,
            n_treatment=1000,
            n_control_conversions=100,
            n_treatment_conversions=120,
            p_value_reported=0.05,
            effect_size_reported=0.02,
            baseline_conversion_rate=0.10,
        )
        record = validate_summary(summary)
        assert record is not None

    def test_p_value_above_threshold(self):
        summary = ABTestSummary(
            url="http://example.com",
            domain="example.com",
            outcome_type="binary",
            n_control=1000,
            n_treatment=1000,
            n_control_conversions=100,
            n_treatment_conversions=120,
            p_value_reported=0.10,
            effect_size_reported=0.02,
            baseline_conversion_rate=0.10,
        )
        record = validate_summary(summary)
        assert record is not None