"""
Unit tests for the inconsistency validator.

Tests cover:
- Absolute p-difference > 0.05 threshold
- Relative effect-size > 5% threshold
- Sample-size mismatch detection
- data_quality_warning generation
- Exclusion from prevalence estimates
"""

import json
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

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
    ABSOLUTE_P_THRESHOLD,
    RELATIVE_EFFECT_SIZE_THRESHOLD
)


class TestCalculateAbsolutePDifference:
    def test_normal_case(self):
        diff = calculate_absolute_p_difference(0.03, 0.08)
        assert abs(diff - 0.05) < 1e-9

    def test_zero_difference(self):
        diff = calculate_absolute_p_difference(0.05, 0.05)
        assert diff == 0.0

    def test_negative_difference(self):
        diff = calculate_absolute_p_difference(0.10, 0.02)
        assert abs(diff - 0.08) < 1e-9

    def test_none_values(self):
        diff = calculate_absolute_p_difference(None, 0.05)
        assert diff == float('inf')

        diff = calculate_absolute_p_difference(0.05, None)
        assert diff == float('inf')

        diff = calculate_absolute_p_difference(None, None)
        assert diff == float('inf')


class TestCalculateRelativeEffectSizeDifference:
    def test_normal_case(self):
        # 10% vs 10.5% -> 0.5% / 10% = 0.05
        diff = calculate_relative_effect_size_difference(0.105, 0.10)
        assert abs(diff - 0.05) < 1e-9

    def test_zero_effect_size(self):
        # When reported is 0, should return absolute difference
        diff = calculate_relative_effect_size_difference(0.05, 0.0)
        assert abs(diff - 0.05) < 1e-9

    def test_none_values(self):
        diff = calculate_relative_effect_size_difference(None, 0.10)
        assert diff == float('inf')

        diff = calculate_relative_effect_size_difference(0.10, None)
        assert diff == float('inf')

    def test_negative_effect_sizes(self):
        # -0.10 vs -0.105 -> 0.005 / 0.10 = 0.05
        diff = calculate_relative_effect_size_difference(-0.105, -0.10)
        assert abs(diff - 0.05) < 1e-9


class TestDetectSampleSizeMismatch:
    def test_no_mismatch(self):
        summary = ABTestSummary(
            source_url="http://example.com",
            domain="tech",
            n_control=100,
            n_treatment=100,
            reconstructed_n_control=100,
            reconstructed_n_treatment=100,
            reported_p_value=0.05,
            reconstructed_p_value=0.05,
            reported_effect_size=0.10,
            reconstructed_effect_size=0.10
        )
        assert not detect_sample_size_mismatch(summary)

    def test_control_mismatch(self):
        summary = ABTestSummary(
            source_url="http://example.com",
            domain="tech",
            n_control=100,
            n_treatment=100,
            reconstructed_n_control=105,
            reconstructed_n_treatment=100,
            reported_p_value=0.05,
            reconstructed_p_value=0.05,
            reported_effect_size=0.10,
            reconstructed_effect_size=0.10
        )
        assert detect_sample_size_mismatch(summary)

    def test_treatment_mismatch(self):
        summary = ABTestSummary(
            source_url="http://example.com",
            domain="tech",
            n_control=100,
            n_treatment=100,
            reconstructed_n_control=100,
            reconstructed_n_treatment=95,
            reported_p_value=0.05,
            reconstructed_p_value=0.05,
            reported_effect_size=0.10,
            reconstructed_effect_size=0.10
        )
        assert detect_sample_size_mismatch(summary)

    def test_missing_reconstructed(self):
        summary = ABTestSummary(
            source_url="http://example.com",
            domain="tech",
            n_control=100,
            n_treatment=100,
            reconstructed_n_control=None,
            reconstructed_n_treatment=None,
            reported_p_value=0.05,
            reconstructed_p_value=0.05,
            reported_effect_size=0.10,
            reconstructed_effect_size=0.10
        )
        assert not detect_sample_size_mismatch(summary)

    def test_missing_reported(self):
        summary = ABTestSummary(
            source_url="http://example.com",
            domain="tech",
            n_control=None,
            n_treatment=None,
            reconstructed_n_control=100,
            reconstructed_n_treatment=100,
            reported_p_value=0.05,
            reconstructed_p_value=0.05,
            reported_effect_size=0.10,
            reconstructed_effect_size=0.10
        )
        assert not detect_sample_size_mismatch(summary)


class TestCheckPValueConsistency:
    def test_consistent(self):
        summary = ABTestSummary(
            source_url="http://example.com",
            domain="tech",
            n_control=100,
            n_treatment=100,
            reconstructed_n_control=100,
            reconstructed_n_treatment=100,
            reported_p_value=0.05,
            reconstructed_p_value=0.08,  # diff = 0.03 <= 0.05
            reported_effect_size=0.10,
            reconstructed_effect_size=0.10
        )
        is_consistent, diff = check_p_value_consistency(summary)
        assert is_consistent
        assert abs(diff - 0.03) < 1e-9

    def test_inconsistent(self):
        summary = ABTestSummary(
            source_url="http://example.com",
            domain="tech",
            n_control=100,
            n_treatment=100,
            reconstructed_n_control=100,
            reconstructed_n_treatment=100,
            reported_p_value=0.01,
            reconstructed_p_value=0.08,  # diff = 0.07 > 0.05
            reported_effect_size=0.10,
            reconstructed_effect_size=0.10
        )
        is_consistent, diff = check_p_value_consistency(summary)
        assert not is_consistent
        assert abs(diff - 0.07) < 1e-9

    def test_missing_p_values(self):
        summary = ABTestSummary(
            source_url="http://example.com",
            domain="tech",
            n_control=100,
            n_treatment=100,
            reconstructed_n_control=100,
            reconstructed_n_treatment=100,
            reported_p_value=None,
            reconstructed_p_value=0.05,
            reported_effect_size=0.10,
            reconstructed_effect_size=0.10
        )
        is_consistent, diff = check_p_value_consistency(summary)
        assert not is_consistent
        assert diff == float('inf')


class TestCheckEffectSizeConsistency:
    def test_consistent(self):
        summary = ABTestSummary(
            source_url="http://example.com",
            domain="tech",
            n_control=100,
            n_treatment=100,
            reconstructed_n_control=100,
            reconstructed_n_treatment=100,
            reported_p_value=0.05,
            reconstructed_p_value=0.05,
            reported_effect_size=0.10,
            reconstructed_effect_size=0.104  # 4% difference <= 5%
        )
        is_consistent, diff = check_effect_size_consistency(summary)
        assert is_consistent
        assert abs(diff - 0.04) < 1e-9

    def test_inconsistent(self):
        summary = ABTestSummary(
            source_url="http://example.com",
            domain="tech",
            n_control=100,
            n_treatment=100,
            reconstructed_n_control=100,
            reconstructed_n_treatment=100,
            reported_p_value=0.05,
            reconstructed_p_value=0.05,
            reported_effect_size=0.10,
            reconstructed_effect_size=0.12  # 20% difference > 5%
        )
        is_consistent, diff = check_effect_size_consistency(summary)
        assert not is_consistent
        assert abs(diff - 0.20) < 1e-9

    def test_missing_effect_sizes(self):
        summary = ABTestSummary(
            source_url="http://example.com",
            domain="tech",
            n_control=100,
            n_treatment=100,
            reconstructed_n_control=100,
            reconstructed_n_treatment=100,
            reported_p_value=0.05,
            reconstructed_p_value=0.05,
            reported_effect_size=None,
            reconstructed_effect_size=0.10
        )
        is_consistent, diff = check_effect_size_consistency(summary)
        assert not is_consistent
        assert diff == float('inf')


class TestCreateAuditRecord:
    def test_consistent_no_warnings(self):
        summary = ABTestSummary(
            source_url="http://example.com",
            domain="tech",
            n_control=100,
            n_treatment=100,
            reconstructed_n_control=100,
            reconstructed_n_treatment=100,
            reported_p_value=0.05,
            reconstructed_p_value=0.06,
            reported_effect_size=0.10,
            reconstructed_effect_size=0.101
        )
        record = create_audit_record(
            summary,
            p_consistent=True,
            p_diff=0.01,
            effect_consistent=True,
            effect_diff=0.01,
            sample_size_mismatch=False
        )

        assert record.source_url == "http://example.com"
        assert record.is_inconsistent is False
        assert record.p_value_consistent is True
        assert record.effect_size_consistent is True
        assert record.sample_size_mismatch is False
        assert record.data_quality_warnings is None
        assert record.audit_notes is None

    def test_sample_size_mismatch_generates_warning(self):
        summary = ABTestSummary(
            source_url="http://example.com",
            domain="tech",
            n_control=100,
            n_treatment=100,
            reconstructed_n_control=105,
            reconstructed_n_treatment=100,
            reported_p_value=0.05,
            reconstructed_p_value=0.06,
            reported_effect_size=0.10,
            reconstructed_effect_size=0.101
        )
        record = create_audit_record(
            summary,
            p_consistent=True,
            p_diff=0.01,
            effect_consistent=True,
            effect_diff=0.01,
            sample_size_mismatch=True
        )

        assert record.sample_size_mismatch is True
        assert record.data_quality_warnings is not None
        assert len(record.data_quality_warnings) == 1
        assert "Sample size mismatch" in record.data_quality_warnings[0]

    def test_inconsistent_generates_notes(self):
        summary = ABTestSummary(
            source_url="http://example.com",
            domain="tech",
            n_control=100,
            n_treatment=100,
            reconstructed_n_control=100,
            reconstructed_n_treatment=100,
            reported_p_value=0.01,
            reconstructed_p_value=0.08,
            reported_effect_size=0.10,
            reconstructed_effect_size=0.12
        )
        record = create_audit_record(
            summary,
            p_consistent=False,
            p_diff=0.07,
            effect_consistent=False,
            effect_diff=0.20,
            sample_size_mismatch=False
        )

        assert record.is_inconsistent is True
        assert record.audit_notes is not None
        assert len(record.audit_notes) == 2
        assert any("P-value difference" in note for note in record.audit_notes)
        assert any("Effect size" in note for note in record.audit_notes)


class TestValidateSummary:
    def test_valid_summary(self):
        summary = ABTestSummary(
            source_url="http://example.com",
            domain="tech",
            n_control=100,
            n_treatment=100,
            reconstructed_n_control=100,
            reconstructed_n_treatment=100,
            reported_p_value=0.05,
            reconstructed_p_value=0.06,
            reported_effect_size=0.10,
            reconstructed_effect_size=0.101
        )
        record = validate_summary(summary)

        assert record.is_inconsistent is False
        assert record.sample_size_mismatch is False

    def test_inconsistent_summary(self):
        summary = ABTestSummary(
            source_url="http://example.com",
            domain="tech",
            n_control=100,
            n_treatment=100,
            reconstructed_n_control=100,
            reconstructed_n_treatment=100,
            reported_p_value=0.01,
            reconstructed_p_value=0.08,
            reported_effect_size=0.10,
            reconstructed_effect_size=0.12
        )
        record = validate_summary(summary)

        assert record.is_inconsistent is True
        assert record.sample_size_mismatch is False

    def test_sample_size_mismatch_summary(self):
        summary = ABTestSummary(
            source_url="http://example.com",
            domain="tech",
            n_control=100,
            n_treatment=100,
            reconstructed_n_control=105,
            reconstructed_n_treatment=100,
            reported_p_value=0.05,
            reconstructed_p_value=0.06,
            reported_effect_size=0.10,
            reconstructed_effect_size=0.101
        )
        record = validate_summary(summary)

        assert record.sample_size_mismatch is True
        assert record.data_quality_warnings is not None


class TestValidateAllSummaries:
    def test_multiple_summaries(self):
        summaries = [
            ABTestSummary(
                source_url="http://example1.com",
                domain="tech",
                n_control=100,
                n_treatment=100,
                reconstructed_n_control=100,
                reconstructed_n_treatment=100,
                reported_p_value=0.05,
                reconstructed_p_value=0.06,
                reported_effect_size=0.10,
                reconstructed_effect_size=0.101
            ),
            ABTestSummary(
                source_url="http://example2.com",
                domain="health",
                n_control=100,
                n_treatment=100,
                reconstructed_n_control=105,
                reconstructed_n_treatment=100,
                reported_p_value=0.01,
                reconstructed_p_value=0.08,
                reported_effect_size=0.10,
                reconstructed_effect_size=0.12
            )
        ]
        records = validate_all_summaries(summaries)

        assert len(records) == 2
        assert records[0].is_inconsistent is False
        assert records[0].sample_size_mismatch is False
        assert records[1].is_inconsistent is True
        assert records[1].sample_size_mismatch is True


class TestFilterForPrevalence:
    def test_filters_mismatched(self):
        records = [
            AuditRecord(
                source_url="http://example1.com",
                domain="tech",
                reported_p_value=0.05,
                reconstructed_p_value=0.06,
                reported_effect_size=0.10,
                reconstructed_effect_size=0.101,
                n_control=100,
                n_treatment=100,
                reconstructed_n_control=100,
                reconstructed_n_treatment=100,
                is_inconsistent=False,
                p_value_consistent=True,
                effect_size_consistent=True,
                sample_size_mismatch=False,
                data_quality_warnings=None,
                audit_notes=None,
                validation_timestamp="2026-06-27T19:30:00Z"
            ),
            AuditRecord(
                source_url="http://example2.com",
                domain="health",
                reported_p_value=0.01,
                reconstructed_p_value=0.08,
                reported_effect_size=0.10,
                reconstructed_effect_size=0.12,
                n_control=100,
                n_treatment=100,
                reconstructed_n_control=105,
                reconstructed_n_treatment=100,
                is_inconsistent=True,
                p_value_consistent=False,
                effect_size_consistent=False,
                sample_size_mismatch=True,
                data_quality_warnings=["Sample size mismatch"],
                audit_notes=["P-value difference"],
                validation_timestamp="2026-06-27T19:30:00Z"
            )
        ]

        filtered = filter_for_prevalence(records)

        assert len(filtered) == 1
        assert filtered[0].source_url == "http://example1.com"
        assert filtered[0].sample_size_mismatch is False

    def test_all_valid(self):
        records = [
            AuditRecord(
                source_url="http://example1.com",
                domain="tech",
                reported_p_value=0.05,
                reconstructed_p_value=0.06,
                reported_effect_size=0.10,
                reconstructed_effect_size=0.101,
                n_control=100,
                n_treatment=100,
                reconstructed_n_control=100,
                reconstructed_n_treatment=100,
                is_inconsistent=False,
                p_value_consistent=True,
                effect_size_consistent=True,
                sample_size_mismatch=False,
                data_quality_warnings=None,
                audit_notes=None,
                validation_timestamp="2026-06-27T19:30:00Z"
            )
        ]
        filtered = filter_for_prevalence(records)
        assert len(filtered) == 1

    def test_all_mismatched(self):
        records = [
            AuditRecord(
                source_url="http://example1.com",
                domain="tech",
                reported_p_value=0.05,
                reconstructed_p_value=0.06,
                reported_effect_size=0.10,
                reconstructed_effect_size=0.101,
                n_control=100,
                n_treatment=100,
                reconstructed_n_control=105,
                reconstructed_n_treatment=100,
                is_inconsistent=False,
                p_value_consistent=True,
                effect_size_consistent=True,
                sample_size_mismatch=True,
                data_quality_warnings=["Mismatch"],
                audit_notes=None,
                validation_timestamp="2026-06-27T19:30:00Z"
            )
        ]
        filtered = filter_for_prevalence(records)
        assert len(filtered) == 0


class TestWriteAuditReport:
    def test_writes_json_file(self, tmp_path):
        records = [
            AuditRecord(
                source_url="http://example1.com",
                domain="tech",
                reported_p_value=0.05,
                reconstructed_p_value=0.06,
                reported_effect_size=0.10,
                reconstructed_effect_size=0.101,
                n_control=100,
                n_treatment=100,
                reconstructed_n_control=100,
                reconstructed_n_treatment=100,
                is_inconsistent=False,
                p_value_consistent=True,
                effect_size_consistent=True,
                sample_size_mismatch=False,
                data_quality_warnings=None,
                audit_notes=None,
                validation_timestamp="2026-06-27T19:30:00Z"
            )
        ]

        output_path = tmp_path / "output" / "audit_report.json"
        write_audit_report(records, output_path)

        assert output_path.exists()

        with open(output_path, 'r') as f:
            data = json.load(f)

        assert data["total_records"] == 1
        assert len(data["records"]) == 1
        assert data["records"][0]["source_url"] == "http://example1.com"
        assert data["records"][0]["is_inconsistent"] is False
        assert data["records"][0]["sample_size_mismatch"] is False
