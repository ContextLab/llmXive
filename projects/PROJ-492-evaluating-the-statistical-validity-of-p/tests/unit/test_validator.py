"""
Unit tests for the validator module (T025).

Tests FR-004 thresholds and FR-004b sample-size mismatch exclusion.
"""

import json
import pytest
from pathlib import Path
from datetime import datetime

from code.src.models.data_models import ABTestSummary, AuditRecord
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
)


class TestCalculateAbsolutePDifference:
    def test_normal_difference(self):
        assert calculate_absolute_p_difference(0.03, 0.08) == 0.05

    def test_zero_difference(self):
        assert calculate_absolute_p_difference(0.05, 0.05) == 0.0

    def test_negative_values(self):
        assert calculate_absolute_p_difference(0.01, 0.09) == 0.08

    def test_none_values(self):
        assert calculate_absolute_p_difference(None, 0.05) != 0.0
        assert calculate_absolute_p_difference(0.05, None) != 0.0


class TestCalculateRelativeEffectSizeDifference:
    def test_normal_relative_diff(self):
        # 5% difference on 0.10 effect
        assert abs(calculate_relative_effect_size_difference(0.10, 0.105) - 0.05) < 1e-10

    def test_large_relative_diff(self):
        # 20% difference
        assert abs(calculate_relative_effect_size_difference(0.10, 0.12) - 0.20) < 1e-10

    def test_zero_reported_effect(self):
        result = calculate_relative_effect_size_difference(0.0, 0.10)
        assert result != result  # NaN check

    def test_none_values(self):
        assert calculate_relative_effect_size_difference(None, 0.10) != 0.0
        assert calculate_relative_effect_size_difference(0.10, None) != 0.0


class TestDetectSampleSizeMismatch:
    def test_no_mismatch(self):
        is_mismatch, warning = detect_sample_size_mismatch(
            1000, 1000, 1000, 1000
        )
        assert not is_mismatch
        assert warning == ""

    def test_small_mismatch_within_tolerance(self):
        # 0.5% difference, tolerance is 1%
        is_mismatch, warning = detect_sample_size_mismatch(
            1000, 1000, 1005, 1005
        )
        assert not is_mismatch
        assert warning == ""

    def test_large_mismatch_exceeds_tolerance(self):
        # 5% difference, exceeds 1% tolerance
        is_mismatch, warning = detect_sample_size_mismatch(
            1000, 1000, 1050, 1050
        )
        assert is_mismatch
        assert "Control group" in warning or "Treatment group" in warning

    def test_mismatch_only_control(self):
        is_mismatch, warning = detect_sample_size_mismatch(
            1000, 1000, 1100, 1000
        )
        assert is_mismatch
        assert "Control group" in warning

    def test_mismatch_only_treatment(self):
        is_mismatch, warning = detect_sample_size_mismatch(
            1000, 1000, 1000, 1100
        )
        assert is_mismatch
        assert "Treatment group" in warning

    def test_none_values(self):
        is_mismatch, warning = detect_sample_size_mismatch(
            None, 1000, None, 1000
        )
        assert not is_mismatch


class TestCheckPValueConsistency:
    def test_consistent_p_values(self):
        is_inconsistent, reason = check_p_value_consistency(0.03, 0.05, threshold=0.05)
        assert not is_inconsistent

    def test_inconsistent_p_values(self):
        is_inconsistent, reason = check_p_value_consistency(0.01, 0.08, threshold=0.05)
        assert is_inconsistent
        assert "0.07" in reason

    def test_missing_p_value(self):
        is_inconsistent, reason = check_p_value_consistency(None, 0.05)
        assert not is_inconsistent
        assert "Missing" in reason


class TestCheckEffectSizeConsistency:
    def test_consistent_effect_sizes(self):
        is_inconsistent, reason = check_effect_size_consistency(0.10, 0.104, threshold=0.05)
        assert not is_inconsistent

    def test_inconsistent_effect_sizes(self):
        is_inconsistent, reason = check_effect_size_consistency(0.10, 0.16, threshold=0.05)
        assert is_inconsistent
        assert "50.00%" in reason

    def test_missing_effect_size(self):
        is_inconsistent, reason = check_effect_size_consistency(None, 0.10)
        assert not is_inconsistent
        assert "Missing" in reason


class TestValidateSummary:
    def create_test_summary(
        self,
        p_reported=0.05,
        p_reconstructed=0.05,
        effect_reported=0.10,
        effect_reconstructed=0.10,
        n_control_reported=1000,
        n_treatment_reported=1000,
        n_control_reconstructed=1000,
        n_treatment_reconstructed=1000
    ):
        return ABTestSummary(
            url="https://example.com/test",
            domain="example.com",
            p_value=p_reported,
            reconstructed_p_value=p_reconstructed,
            effect_size=effect_reported,
            reconstructed_effect_size=effect_reconstructed,
            n_control=n_control_reported,
            n_treatment=n_treatment_reported,
            reconstructed_n_control=n_control_reconstructed,
            reconstructed_n_treatment=n_treatment_reconstructed,
            outcome_type="binary",
            test_type="z-test"
        )

    def test_consistent_summary(self):
        summary = self.create_test_summary()
        record = validate_summary(summary)

        assert not record.is_inconsistent
        assert record.inconsistency_reasons is None or len(record.inconsistency_reasons) == 0
        assert record.data_quality_warnings is None or len(record.data_quality_warnings) == 0

    def test_inconsistent_p_value(self):
        summary = self.create_test_summary(p_reported=0.01, p_reconstructed=0.08)
        record = validate_summary(summary)

        assert record.is_inconsistent
        assert any("P-value difference" in r for r in record.inconsistency_reasons)

    def test_inconsistent_effect_size(self):
        summary = self.create_test_summary(effect_reported=0.10, effect_reconstructed=0.16)
        record = validate_summary(summary)

        assert record.is_inconsistent
        assert any("Effect size" in r for r in record.inconsistency_reasons)

    def test_sample_size_mismatch_warning(self):
        summary = self.create_test_summary(
            n_control_reported=1000,
            n_control_reconstructed=1100
        )
        record = validate_summary(summary)

        assert record.data_quality_warnings is not None
        assert any("data_quality_warning" in w for w in record.data_quality_warnings)

    def test_both_inconsistency_and_warning(self):
        summary = self.create_test_summary(
            p_reported=0.01,
            p_reconstructed=0.08,
            n_control_reported=1000,
            n_control_reconstructed=1100
        )
        record = validate_summary(summary)

        assert record.is_inconsistent
        assert record.data_quality_warnings is not None


class TestValidateAllSummaries:
    def test_multiple_summaries(self):
        summaries = [
            ABTestSummary(
                url="https://example.com/1",
                domain="example.com",
                p_value=0.05,
                reconstructed_p_value=0.05,
                effect_size=0.10,
                reconstructed_effect_size=0.10,
                n_control=1000,
                n_treatment=1000,
                reconstructed_n_control=1000,
                reconstructed_n_treatment=1000,
                outcome_type="binary",
                test_type="z-test"
            ),
            ABTestSummary(
                url="https://example.com/2",
                domain="example.com",
                p_value=0.01,
                reconstructed_p_value=0.08,
                effect_size=0.10,
                reconstructed_effect_size=0.10,
                n_control=1000,
                n_treatment=1000,
                reconstructed_n_control=1000,
                reconstructed_n_treatment=1000,
                outcome_type="binary",
                test_type="z-test"
            )
        ]

        records = validate_all_summaries(summaries)

        assert len(records) == 2
        assert not records[0].is_inconsistent
        assert records[1].is_inconsistent


class TestFilterForPrevalence:
    def create_test_record(self, has_sample_size_warning=False):
        warnings = ["data_quality_warning: sample-size mismatch"] if has_sample_size_warning else None
        return AuditRecord(
            url="https://example.com/test",
            domain="example.com",
            is_inconsistent=False,
            inconsistency_reasons=None,
            data_quality_warnings=warnings,
            reported_p_value=0.05,
            reconstructed_p_value=0.05,
            reported_effect_size=0.10,
            reconstructed_effect_size=0.10,
            reported_n_control=1000,
            reported_n_treatment=1000,
            reconstructed_n_control=1000,
            reconstructed_n_treatment=1000,
            audit_timestamp=datetime.utcnow().isoformat(),
            source="test"
        )

    def test_filter_removes_mismatched(self):
        records = [
            self.create_test_record(has_sample_size_warning=False),
            self.create_test_record(has_sample_size_warning=True),
            self.create_test_record(has_sample_size_warning=False),
        ]

        filtered = filter_for_prevalence(records)

        assert len(filtered) == 2
        assert all(r.data_quality_warnings is None for r in filtered)

    def test_filter_all_mismatched(self):
        records = [
            self.create_test_record(has_sample_size_warning=True),
            self.create_test_record(has_sample_size_warning=True),
        ]

        filtered = filter_for_prevalence(records)

        assert len(filtered) == 0

    def test_filter_no_mismatched(self):
        records = [
            self.create_test_record(has_sample_size_warning=False),
            self.create_test_record(has_sample_size_warning=False),
        ]

        filtered = filter_for_prevalence(records)

        assert len(filtered) == 2


class TestWriteAuditReport:
    def test_write_report_creates_file(self, tmp_path):
        records = [
            AuditRecord(
                url="https://example.com/test",
                domain="example.com",
                is_inconsistent=False,
                inconsistency_reasons=None,
                data_quality_warnings=None,
                reported_p_value=0.05,
                reconstructed_p_value=0.05,
                reported_effect_size=0.10,
                reconstructed_effect_size=0.10,
                reported_n_control=1000,
                reported_n_treatment=1000,
                reconstructed_n_control=1000,
                reconstructed_n_treatment=1000,
                audit_timestamp=datetime.utcnow().isoformat(),
                source="test"
            )
        ]

        output_path = tmp_path / "audit_report.json"
        write_audit_report(records, output_path)

        assert output_path.exists()

        with open(output_path, 'r') as f:
            data = json.load(f)

        assert data["total_records"] == 1
        assert data["inconsistent_count"] == 0
        assert len(data["records"]) == 1
        assert data["records"][0]["url"] == "https://example.com/test"