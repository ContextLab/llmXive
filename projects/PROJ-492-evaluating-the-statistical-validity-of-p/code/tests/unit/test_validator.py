"""
Unit tests for the inconsistency validator (T025).

Tests cover:
- Absolute p-difference > 0.05 threshold
- Relative effect-size difference > 5% threshold
- Inequality handling
- Sample-size mismatch detection and exclusion
- data_quality_warning generation
"""
import json
import pytest
from pathlib import Path
from datetime import datetime
from unittest.mock import patch, MagicMock

import numpy as np

from code.src.audit.validator import (
    calculate_absolute_p_difference,
    calculate_relative_effect_size_difference,
    detect_sample_size_mismatch,
    check_p_value_consistency,
    check_effect_size_consistency,
    create_audit_record,
    validate_summary,
    validate_all_summaries,
    filter_for_prevalence,
    write_audit_report,
    main
)
from code.src.models.data_models import ABTestSummary, AuditRecord


class TestCalculateAbsolutePDifference:
    """Tests for absolute p-difference calculation."""

    def test_identical_p_values(self):
        """When p-values are identical, difference should be 0."""
        diff = calculate_absolute_p_difference(0.03, 0.03)
        assert diff == 0.0

    def test_small_difference(self):
        """Small difference below threshold."""
        diff = calculate_absolute_p_difference(0.04, 0.05)
        assert abs(diff - 0.01) < 1e-9

    def test_large_difference(self):
        """Large difference above threshold."""
        diff = calculate_absolute_p_difference(0.01, 0.10)
        assert abs(diff - 0.09) < 1e-9

    def test_zero_vs_nonzero(self):
        """Difference between zero and non-zero."""
        diff = calculate_absolute_p_difference(0.0, 0.05)
        assert diff == 0.05


class TestCalculateRelativeEffectSizeDifference:
    """Tests for relative effect-size difference calculation."""

    def test_identical_effect_sizes(self):
        """When effect sizes are identical, difference should be 0%."""
        diff = calculate_relative_effect_size_difference(0.10, 0.10)
        assert diff == 0.0

    def test_small_relative_difference(self):
        """Small relative difference below 5% threshold."""
        # 10% vs 10.4% is a 4% relative difference
        diff = calculate_relative_effect_size_difference(0.10, 0.104)
        assert abs(diff - 4.0) < 1e-6

    def test_large_relative_difference(self):
        """Large relative difference above 5% threshold."""
        # 10% vs 11% is a 10% relative difference
        diff = calculate_relative_effect_size_difference(0.10, 0.11)
        assert abs(diff - 10.0) < 1e-6

    def test_zero_reconstructed(self):
        """When reconstructed is zero, should handle gracefully."""
        diff = calculate_relative_effect_size_difference(0.05, 0.0)
        assert diff == float('inf')

    def test_both_zero(self):
        """When both are zero, difference should be 0."""
        diff = calculate_relative_effect_size_difference(0.0, 0.0)
        assert diff == 0.0


class TestDetectSampleSizeMismatch:
    """Tests for sample-size mismatch detection."""

    def test_no_mismatch(self):
        """Valid sample sizes should not trigger mismatch."""
        summary = ABTestSummary(
            url="https://example.com/test1",
            domain="example.com",
            outcome_type="binary",
            sample_size_control=1000,
            sample_size_treatment=1000,
            reported_p_value=0.04,
            reconstructed_p_value=0.041,
            reported_effect_size=0.05,
            reconstructed_effect_size=0.051
        )
        has_mismatch, warning = detect_sample_size_mismatch(summary)
        assert not has_mismatch
        assert warning is None

    def test_missing_control_size(self):
        """Missing control size should trigger mismatch."""
        summary = ABTestSummary(
            url="https://example.com/test2",
            domain="example.com",
            outcome_type="binary",
            sample_size_control=None,
            sample_size_treatment=1000,
            reported_p_value=0.04,
            reconstructed_p_value=0.041,
            reported_effect_size=0.05,
            reconstructed_effect_size=0.051
        )
        has_mismatch, warning = detect_sample_size_mismatch(summary)
        assert has_mismatch
        assert "Missing sample size data" in warning

    def test_missing_treatment_size(self):
        """Missing treatment size should trigger mismatch."""
        summary = ABTestSummary(
            url="https://example.com/test3",
            domain="example.com",
            outcome_type="binary",
            sample_size_control=1000,
            sample_size_treatment=None,
            reported_p_value=0.04,
            reconstructed_p_value=0.041,
            reported_effect_size=0.05,
            reconstructed_effect_size=0.051
        )
        has_mismatch, warning = detect_sample_size_mismatch(summary)
        assert has_mismatch
        assert "Missing sample size data" in warning

    def test_both_missing(self):
        """Both missing should trigger mismatch."""
        summary = ABTestSummary(
            url="https://example.com/test4",
            domain="example.com",
            outcome_type="binary",
            sample_size_control=None,
            sample_size_treatment=None,
            reported_p_value=0.04,
            reconstructed_p_value=0.041,
            reported_effect_size=0.05,
            reconstructed_effect_size=0.051
        )
        has_mismatch, warning = detect_sample_size_mismatch(summary)
        assert has_mismatch
        assert "Missing sample size data" in warning

    def test_zero_control_size(self):
        """Zero control size should trigger mismatch."""
        summary = ABTestSummary(
            url="https://example.com/test5",
            domain="example.com",
            outcome_type="binary",
            sample_size_control=0,
            sample_size_treatment=1000,
            reported_p_value=0.04,
            reconstructed_p_value=0.041,
            reported_effect_size=0.05,
            reconstructed_effect_size=0.051
        )
        has_mismatch, warning = detect_sample_size_mismatch(summary)
        assert has_mismatch
        assert "Control group sample size is non-positive" in warning

    def test_zero_treatment_size(self):
        """Zero treatment size should trigger mismatch."""
        summary = ABTestSummary(
            url="https://example.com/test6",
            domain="example.com",
            outcome_type="binary",
            sample_size_control=1000,
            sample_size_treatment=0,
            reported_p_value=0.04,
            reconstructed_p_value=0.041,
            reported_effect_size=0.05,
            reconstructed_effect_size=0.051
        )
        has_mismatch, warning = detect_sample_size_mismatch(summary)
        assert has_mismatch
        assert "Treatment group sample size is non-positive" in warning


class TestCheckPValueConsistency:
    """Tests for p-value consistency checking."""

    def test_consistent_p_values(self):
        """P-values within threshold should be consistent."""
        summary = ABTestSummary(
            url="https://example.com/test7",
            domain="example.com",
            outcome_type="binary",
            sample_size_control=1000,
            sample_size_treatment=1000,
            reported_p_value=0.04,
            reconstructed_p_value=0.041,
            reported_effect_size=0.05,
            reconstructed_effect_size=0.051
        )
        is_consistent, diff, reason = check_p_value_consistency(summary, threshold=0.05)
        assert is_consistent
        assert abs(diff - 0.001) < 1e-9
        assert reason is None

    def test_inconsistent_p_values(self):
        """P-values exceeding threshold should be inconsistent."""
        summary = ABTestSummary(
            url="https://example.com/test8",
            domain="example.com",
            outcome_type="binary",
            sample_size_control=1000,
            sample_size_treatment=1000,
            reported_p_value=0.01,
            reconstructed_p_value=0.10,
            reported_effect_size=0.05,
            reconstructed_effect_size=0.051
        )
        is_consistent, diff, reason = check_p_value_consistency(summary, threshold=0.05)
        assert not is_consistent
        assert abs(diff - 0.09) < 1e-9
        assert "exceeds threshold" in reason

    def test_missing_reconstructed_p(self):
        """Missing reconstructed p-value should be consistent (no comparison possible)."""
        summary = ABTestSummary(
            url="https://example.com/test9",
            domain="example.com",
            outcome_type="binary",
            sample_size_control=1000,
            sample_size_treatment=1000,
            reported_p_value=0.04,
            reconstructed_p_value=None,
            reported_effect_size=0.05,
            reconstructed_effect_size=0.051
        )
        is_consistent, diff, reason = check_p_value_consistency(summary, threshold=0.05)
        assert is_consistent
        assert diff == 0.0
        assert "Missing p-value data" in reason


class TestCheckEffectSizeConsistency:
    """Tests for effect-size consistency checking."""

    def test_consistent_effect_sizes(self):
        """Effect sizes within threshold should be consistent."""
        summary = ABTestSummary(
            url="https://example.com/test10",
            domain="example.com",
            outcome_type="binary",
            sample_size_control=1000,
            sample_size_treatment=1000,
            reported_p_value=0.04,
            reconstructed_p_value=0.041,
            reported_effect_size=0.05,
            reconstructed_effect_size=0.051
        )
        is_consistent, diff, reason = check_effect_size_consistency(summary, threshold=5.0)
        assert is_consistent
        assert abs(diff - 2.0) < 1e-6
        assert reason is None

    def test_inconsistent_effect_sizes(self):
        """Effect sizes exceeding threshold should be inconsistent."""
        summary = ABTestSummary(
            url="https://example.com/test11",
            domain="example.com",
            outcome_type="binary",
            sample_size_control=1000,
            sample_size_treatment=1000,
            reported_p_value=0.04,
            reconstructed_p_value=0.041,
            reported_effect_size=0.05,
            reconstructed_effect_size=0.055
        )
        is_consistent, diff, reason = check_effect_size_consistency(summary, threshold=5.0)
        assert not is_consistent
        assert abs(diff - 9.09) < 0.1
        assert "exceeds threshold" in reason

    def test_missing_reconstructed_effect(self):
        """Missing reconstructed effect size should be consistent."""
        summary = ABTestSummary(
            url="https://example.com/test12",
            domain="example.com",
            outcome_type="binary",
            sample_size_control=1000,
            sample_size_treatment=1000,
            reported_p_value=0.04,
            reconstructed_p_value=0.041,
            reported_effect_size=0.05,
            reconstructed_effect_size=None
        )
        is_consistent, diff, reason = check_effect_size_consistency(summary, threshold=5.0)
        assert is_consistent
        assert diff == 0.0
        assert "Missing effect size data" in reason


class TestValidateSummary:
    """Tests for the main validation function."""

    def test_all_consistent(self):
        """Summary with all consistent values should pass."""
        summary = ABTestSummary(
            url="https://example.com/test13",
            domain="example.com",
            outcome_type="binary",
            sample_size_control=1000,
            sample_size_treatment=1000,
            reported_p_value=0.04,
            reconstructed_p_value=0.041,
            reported_effect_size=0.05,
            reconstructed_effect_size=0.051
        )
        record = validate_summary(summary)
        
        assert not record.is_inconsistent
        assert record.data_quality_warnings is None
        assert "p_difference" in str(record.p_difference) or abs(record.p_difference - 0.001) < 1e-9

    def test_p_inconsistent(self):
        """Summary with p-value inconsistency should be marked inconsistent."""
        summary = ABTestSummary(
            url="https://example.com/test14",
            domain="example.com",
            outcome_type="binary",
            sample_size_control=1000,
            sample_size_treatment=1000,
            reported_p_value=0.01,
            reconstructed_p_value=0.10,
            reported_effect_size=0.05,
            reconstructed_effect_size=0.051
        )
        record = validate_summary(summary)
        
        assert record.is_inconsistent
        assert "P-value inconsistency" in record.notes

    def test_effect_inconsistent(self):
        """Summary with effect-size inconsistency should be marked inconsistent."""
        summary = ABTestSummary(
            url="https://example.com/test15",
            domain="example.com",
            outcome_type="binary",
            sample_size_control=1000,
            sample_size_treatment=1000,
            reported_p_value=0.04,
            reconstructed_p_value=0.041,
            reported_effect_size=0.05,
            reconstructed_effect_size=0.06
        )
        record = validate_summary(summary)
        
        assert record.is_inconsistent
        assert "Effect size inconsistency" in record.notes

    def test_sample_mismatch_warning(self):
        """Summary with sample-size mismatch should have data_quality_warning."""
        summary = ABTestSummary(
            url="https://example.com/test16",
            domain="example.com",
            outcome_type="binary",
            sample_size_control=0,
            sample_size_treatment=1000,
            reported_p_value=0.04,
            reconstructed_p_value=0.041,
            reported_effect_size=0.05,
            reconstructed_effect_size=0.051
        )
        record = validate_summary(summary)
        
        # Sample mismatch alone doesn't make it inconsistent
        assert not record.is_inconsistent
        assert record.data_quality_warnings is not None
        assert len(record.data_quality_warnings) > 0
        assert any("sample" in w.lower() for w in record.data_quality_warnings)


class TestFilterForPrevalence:
    """Tests for filtering records for prevalence calculation (FR-004b)."""

    def test_filter_excludes_sample_mismatch(self):
        """Records with sample-size mismatches should be excluded."""
        # Create a record with sample-size mismatch
        record_with_mismatch = AuditRecord(
            url="https://example.com/test17",
            domain="example.com",
            outcome_type="binary",
            is_inconsistent=False,
            data_quality_warnings=["Sample size mismatch detected"]
        )
        
        # Create a record without mismatch
        record_clean = AuditRecord(
            url="https://example.com/test18",
            domain="example.com",
            outcome_type="binary",
            is_inconsistent=True,
            data_quality_warnings=None
        )
        
        records = [record_with_mismatch, record_clean]
        filtered = filter_for_prevalence(records)
        
        assert len(filtered) == 1
        assert filtered[0].url == "https://example.com/test18"

    def test_filter_keeps_non_sample_warnings(self):
        """Records with non-sample warnings should be kept."""
        record_with_other_warning = AuditRecord(
            url="https://example.com/test19",
            domain="example.com",
            outcome_type="binary",
            is_inconsistent=True,
            data_quality_warnings=["Some other warning"]
        )
        
        filtered = filter_for_prevalence([record_with_other_warning])
        assert len(filtered) == 1


class TestWriteAuditReport:
    """Tests for writing audit report to JSON."""

    def test_write_creates_file(self, tmp_path):
        """Report should be written to specified path."""
        output_path = tmp_path / "audit_report.json"
        
        records = [
            AuditRecord(
                url="https://example.com/test20",
                domain="example.com",
                outcome_type="binary",
                is_inconsistent=True,
                notes="Test notes"
            )
        ]
        
        write_audit_report(records, str(output_path))
        
        assert output_path.exists()
        
        with open(output_path, 'r') as f:
            data = json.load(f)
        
        assert len(data) == 1
        assert data[0]["url"] == "https://example.com/test20"
        assert data[0]["is_inconsistent"] is True


class TestValidateAllSummaries:
    """Tests for batch validation."""

    def test_validate_multiple_summaries(self):
        """Should validate multiple summaries correctly."""
        summaries = [
            ABTestSummary(
                url=f"https://example.com/test{i}",
                domain="example.com",
                outcome_type="binary",
                sample_size_control=1000,
                sample_size_treatment=1000,
                reported_p_value=0.04,
                reconstructed_p_value=0.041,
                reported_effect_size=0.05,
                reconstructed_effect_size=0.051
            )
            for i in range(3)
        ]
        
        records = validate_all_summaries(summaries)
        
        assert len(records) == 3
        for record in records:
            assert not record.is_inconsistent

    def test_validate_with_mixed_results(self):
        """Should handle mixed consistent/inconsistent summaries."""
        summaries = [
            ABTestSummary(
                url="https://example.com/good",
                domain="example.com",
                outcome_type="binary",
                sample_size_control=1000,
                sample_size_treatment=1000,
                reported_p_value=0.04,
                reconstructed_p_value=0.041,
                reported_effect_size=0.05,
                reconstructed_effect_size=0.051
            ),
            ABTestSummary(
                url="https://example.com/bad",
                domain="example.com",
                outcome_type="binary",
                sample_size_control=1000,
                sample_size_treatment=1000,
                reported_p_value=0.01,
                reconstructed_p_value=0.10,
                reported_effect_size=0.05,
                reconstructed_effect_size=0.051
            )
        ]
        
        records = validate_all_summaries(summaries)
        
        assert len(records) == 2
        assert not records[0].is_inconsistent
        assert records[1].is_inconsistent


if __name__ == "__main__":
    pytest.main([__file__, "-v"])