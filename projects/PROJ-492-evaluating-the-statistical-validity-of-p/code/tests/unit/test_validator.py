"""
Unit tests for the inconsistency validator (T025).

Tests:
- Absolute p-value difference > 0.05
- Relative effect-size difference > 5%
- Inequality handling
- Sample-size mismatch with data_quality_warning generation
"""
import pytest
from pathlib import Path
import json
from datetime import datetime

from code.src.models.data_models import ABTestSummary, AuditRecord
from code.src.audit.validator import (
    check_sample_size_consistency,
    validate_p_value_consistency,
    validate_effect_size_consistency,
    create_audit_record,
    validate_summary,
    validate_all_summaries,
    write_audit_report,
    run_validator,
    ERR_SAMPLE_SIZE_MISMATCH,
    ERR_P_VALUE_INCONSISTENCY,
    ERR_EFFECT_SIZE_INCONSISTENCY
)


class TestSampleSizeConsistency:
    """Tests for sample size consistency checking."""

    def test_valid_sample_sizes(self):
        """Valid sample sizes should return consistent."""
        summary = ABTestSummary(
            url="http://example.com",
            domain="example.com",
            n_control=1000,
            n_treatment=1000,
            control_rate=0.1,
            treatment_rate=0.12
        )
        is_consistent, msg = check_sample_size_consistency(summary)
        assert is_consistent is True
        assert msg is None

    def test_invalid_sample_size_control_rate(self):
        """Control rate exceeding sample size should be flagged."""
        summary = ABTestSummary(
            url="http://example.com",
            domain="example.com",
            n_control=100,
            n_treatment=100,
            control_rate=1.5,  # Impossible: 150% rate
            treatment_rate=0.1
        )
        is_consistent, msg = check_sample_size_consistency(summary)
        assert is_consistent is False
        assert "inconsistent with n_control" in msg

    def test_invalid_sample_size_treatment_rate(self):
        """Treatment rate exceeding sample size should be flagged."""
        summary = ABTestSummary(
            url="http://example.com",
            domain="example.com",
            n_control=100,
            n_treatment=100,
            control_rate=0.1,
            treatment_rate=1.5  # Impossible
        )
        is_consistent, msg = check_sample_size_consistency(summary)
        assert is_consistent is False
        assert "inconsistent with n_treatment" in msg

    def test_negative_sample_size(self):
        """Negative sample sizes should be flagged."""
        summary = ABTestSummary(
            url="http://example.com",
            domain="example.com",
            n_control=-100,
            n_treatment=100,
            control_rate=0.1,
            treatment_rate=0.12
        )
        is_consistent, msg = check_sample_size_consistency(summary)
        assert is_consistent is False
        assert "Invalid sample sizes" in msg

    def test_missing_sample_sizes(self):
        """Missing sample sizes should not be flagged as mismatch."""
        summary = ABTestSummary(
            url="http://example.com",
            domain="example.com",
            n_control=None,
            n_treatment=None,
            control_rate=0.1,
            treatment_rate=0.12
        )
        is_consistent, msg = check_sample_size_consistency(summary)
        assert is_consistent is True
        assert msg is None


class TestPValueConsistency:
    """Tests for p-value consistency checking."""

    def test_within_threshold(self):
        """P-value difference within 0.05 should be consistent."""
        is_consistent, msg = validate_p_value_consistency(0.03, 0.05)
        assert is_consistent is True
        assert msg is None

    def test_exceeds_threshold(self):
        """P-value difference > 0.05 should be inconsistent."""
        is_consistent, msg = validate_p_value_consistency(0.01, 0.10)
        assert is_consistent is False
        assert "P-value discrepancy" in msg
        assert "diff=0.09" in msg

    def test_missing_values(self):
        """Missing p-values should not be flagged."""
        is_consistent, msg = validate_p_value_consistency(None, 0.05)
        assert is_consistent is True
        assert msg is None

        is_consistent, msg = validate_p_value_consistency(0.03, None)
        assert is_consistent is True
        assert msg is None


class TestEffectSizeConsistency:
    """Tests for effect size consistency checking."""

    def test_within_threshold(self):
        """Effect size difference within 5% should be consistent."""
        # 5% relative difference on 0.20 is 0.01
        is_consistent, msg = validate_effect_size_consistency(0.20, 0.209)
        assert is_consistent is True
        assert msg is None

    def test_exceeds_threshold(self):
        """Effect size difference > 5% should be inconsistent."""
        # 10% relative difference on 0.20 is 0.02
        is_consistent, msg = validate_effect_size_consistency(0.20, 0.22)
        assert is_consistent is False
        assert "Effect size discrepancy" in msg
        assert "rel_diff=10.00%" in msg

    def test_missing_values(self):
        """Missing effect sizes should not be flagged."""
        is_consistent, msg = validate_effect_size_consistency(None, 0.20)
        assert is_consistent is True
        assert msg is None

        is_consistent, msg = validate_effect_size_consistency(0.20, None)
        assert is_consistent is True
        assert msg is None

    def test_zero_reported_effect(self):
        """Zero reported effect with non-zero reconstructed should be flagged."""
        is_consistent, msg = validate_effect_size_consistency(0.0, 0.05)
        assert is_consistent is False
        assert "Effect size mismatch" in msg

    def test_zero_both(self):
        """Zero reported and reconstructed should be consistent."""
        is_consistent, msg = validate_effect_size_consistency(0.0, 0.0)
        assert is_consistent is True
        assert msg is None


class TestAuditRecordCreation:
    """Tests for AuditRecord creation."""

    def test_no_warnings(self):
        """No warnings should result in is_inconsistent=False."""
        summary = ABTestSummary(
            url="http://example.com",
            domain="example.com",
            n_control=1000,
            n_treatment=1000,
            p_value=0.05,
            effect_size=0.10
        )
        record = create_audit_record(
            summary=summary,
            reconstructed_p=0.05,
            reconstructed_effect=0.10
        )
        assert record.is_inconsistent is False
        assert record.warnings is None

    def test_sample_size_warning(self):
        """Sample size warning should set is_inconsistent=True and add warning."""
        summary = ABTestSummary(
            url="http://example.com",
            domain="example.com",
            n_control=100,
            n_treatment=100,
            p_value=0.05,
            effect_size=0.10
        )
        record = create_audit_record(
            summary=summary,
            reconstructed_p=0.05,
            reconstructed_effect=0.10,
            sample_size_warning="Invalid sample sizes"
        )
        assert record.is_inconsistent is True
        assert record.warnings is not None
        assert len(record.warnings) == 1
        assert record.warnings[0]["code"] == ERR_SAMPLE_SIZE_MISMATCH
        assert record.warnings[0]["type"] == "data_quality_warning"

    def test_p_value_warning(self):
        """P-value warning should set is_inconsistent=True and add warning."""
        summary = ABTestSummary(
            url="http://example.com",
            domain="example.com",
            n_control=1000,
            n_treatment=1000,
            p_value=0.01,
            effect_size=0.10
        )
        record = create_audit_record(
            summary=summary,
            reconstructed_p=0.10,
            reconstructed_effect=0.10,
            p_value_warning="P-value discrepancy"
        )
        assert record.is_inconsistent is True
        assert record.warnings is not None
        assert len(record.warnings) == 1
        assert record.warnings[0]["code"] == ERR_P_VALUE_INCONSISTENCY
        assert record.warnings[0]["type"] == "statistical_inconsistency"

    def test_effect_size_warning(self):
        """Effect size warning should set is_inconsistent=True and add warning."""
        summary = ABTestSummary(
            url="http://example.com",
            domain="example.com",
            n_control=1000,
            n_treatment=1000,
            p_value=0.05,
            effect_size=0.20
        )
        record = create_audit_record(
            summary=summary,
            reconstructed_p=0.05,
            reconstructed_effect=0.25,
            effect_size_warning="Effect size discrepancy"
        )
        assert record.is_inconsistent is True
        assert record.warnings is not None
        assert len(record.warnings) == 1
        assert record.warnings[0]["code"] == ERR_EFFECT_SIZE_INCONSISTENCY
        assert record.warnings[0]["type"] == "statistical_inconsistency"

    def test_multiple_warnings(self):
        """Multiple warnings should all be included."""
        summary = ABTestSummary(
            url="http://example.com",
            domain="example.com",
            n_control=-100,
            n_treatment=100,
            p_value=0.01,
            effect_size=0.20
        )
        record = create_audit_record(
            summary=summary,
            reconstructed_p=0.10,
            reconstructed_effect=0.25,
            sample_size_warning="Invalid sample sizes",
            p_value_warning="P-value discrepancy",
            effect_size_warning="Effect size discrepancy"
        )
        assert record.is_inconsistent is True
        assert record.warnings is not None
        assert len(record.warnings) == 3
        codes = [w["code"] for w in record.warnings]
        assert ERR_SAMPLE_SIZE_MISMATCH in codes
        assert ERR_P_VALUE_INCONSISTENCY in codes
        assert ERR_EFFECT_SIZE_INCONSISTENCY in codes


class TestValidateSummary:
    """Tests for the validate_summary function."""

    def test_all_consistent(self):
        """All checks consistent should result in is_inconsistent=False."""
        summary = ABTestSummary(
            url="http://example.com",
            domain="example.com",
            n_control=1000,
            n_treatment=1000,
            p_value=0.05,
            effect_size=0.10
        )
        record = validate_summary(summary, 0.05, 0.10)
        assert record.is_inconsistent is False
        assert record.warnings is None

    def test_sample_size_inconsistent(self):
        """Sample size inconsistent should result in is_inconsistent=True."""
        summary = ABTestSummary(
            url="http://example.com",
            domain="example.com",
            n_control=-100,
            n_treatment=100,
            p_value=0.05,
            effect_size=0.10
        )
        record = validate_summary(summary, 0.05, 0.10)
        assert record.is_inconsistent is True
        assert record.warnings is not None
        assert len(record.warnings) == 1
        assert record.warnings[0]["code"] == ERR_SAMPLE_SIZE_MISMATCH
        assert record.warnings[0]["type"] == "data_quality_warning"

    def test_p_value_inconsistent(self):
        """P-value inconsistent should result in is_inconsistent=True."""
        summary = ABTestSummary(
            url="http://example.com",
            domain="example.com",
            n_control=1000,
            n_treatment=1000,
            p_value=0.01,
            effect_size=0.10
        )
        record = validate_summary(summary, 0.10, 0.10)
        assert record.is_inconsistent is True
        assert record.warnings is not None
        assert len(record.warnings) == 1
        assert record.warnings[0]["code"] == ERR_P_VALUE_INCONSISTENCY

    def test_effect_size_inconsistent(self):
        """Effect size inconsistent should result in is_inconsistent=True."""
        summary = ABTestSummary(
            url="http://example.com",
            domain="example.com",
            n_control=1000,
            n_treatment=1000,
            p_value=0.05,
            effect_size=0.20
        )
        record = validate_summary(summary, 0.05, 0.25)
        assert record.is_inconsistent is True
        assert record.warnings is not None
        assert len(record.warnings) == 1
        assert record.warnings[0]["code"] == ERR_EFFECT_SIZE_INCONSISTENCY

    def test_multiple_inconsistencies(self):
        """Multiple inconsistencies should all be flagged."""
        summary = ABTestSummary(
            url="http://example.com",
            domain="example.com",
            n_control=-100,
            n_treatment=100,
            p_value=0.01,
            effect_size=0.20
        )
        record = validate_summary(summary, 0.10, 0.25)
        assert record.is_inconsistent is True
        assert record.warnings is not None
        assert len(record.warnings) == 3


class TestValidateAllSummaries:
    """Tests for validate_all_summaries function."""

    def test_all_consistent(self):
        """All summaries consistent should result in all is_inconsistent=False."""
        summaries = [
            ABTestSummary(url="http://a.com", domain="a.com", n_control=1000, n_treatment=1000, p_value=0.05, effect_size=0.10),
            ABTestSummary(url="http://b.com", domain="b.com", n_control=1000, n_treatment=1000, p_value=0.05, effect_size=0.10)
        ]
        reconstructed = [
            {"reconstructed_p": 0.05, "reconstructed_effect": 0.10},
            {"reconstructed_p": 0.05, "reconstructed_effect": 0.10}
        ]
        records = validate_all_summaries(summaries, reconstructed)
        assert len(records) == 2
        assert all(r.is_inconsistent is False for r in records)

    def test_mixed_consistency(self):
        """Mixed consistency should flag only inconsistent ones."""
        summaries = [
            ABTestSummary(url="http://a.com", domain="a.com", n_control=1000, n_treatment=1000, p_value=0.05, effect_size=0.10),
            ABTestSummary(url="http://b.com", domain="b.com", n_control=-100, n_treatment=100, p_value=0.05, effect_size=0.10),
            ABTestSummary(url="http://c.com", domain="c.com", n_control=1000, n_treatment=1000, p_value=0.01, effect_size=0.10)
        ]
        reconstructed = [
            {"reconstructed_p": 0.05, "reconstructed_effect": 0.10},
            {"reconstructed_p": 0.05, "reconstructed_effect": 0.10},
            {"reconstructed_p": 0.10, "reconstructed_effect": 0.10}
        ]
        records = validate_all_summaries(summaries, reconstructed)
        assert len(records) == 3
        assert records[0].is_inconsistent is False
        assert records[1].is_inconsistent is True
        assert records[2].is_inconsistent is True


class TestWriteAuditReport:
    """Tests for write_audit_report function."""

    def test_write_report(self, tmp_path):
        """Report should be written to JSON file with correct structure."""
        summaries = [
            ABTestSummary(url="http://a.com", domain="a.com", n_control=1000, n_treatment=1000, p_value=0.05, effect_size=0.10),
            ABTestSummary(url="http://b.com", domain="b.com", n_control=-100, n_treatment=100, p_value=0.05, effect_size=0.10)
        ]
        reconstructed = [
            {"reconstructed_p": 0.05, "reconstructed_effect": 0.10},
            {"reconstructed_p": 0.05, "reconstructed_effect": 0.10}
        ]
        records = validate_all_summaries(summaries, reconstructed)

        output_path = tmp_path / "audit_report.json"
        write_audit_report(records, output_path)

        assert output_path.exists()
        with open(output_path, 'r') as f:
            report = json.load(f)

        assert report["total_records"] == 2
        assert report["inconsistent_count"] == 1
        assert len(report["records"]) == 2
        assert report["records"][0]["is_inconsistent"] is False
        assert report["records"][1]["is_inconsistent"] is True
        assert "warnings" in report["records"][1]
        assert len(report["records"][1]["warnings"]) == 1
        assert report["records"][1]["warnings"][0]["code"] == ERR_SAMPLE_SIZE_MISMATCH
        assert report["records"][1]["warnings"][0]["type"] == "data_quality_warning"


class TestRunValidator:
    """Tests for run_validator function."""

    def test_run_validator(self, tmp_path):
        """Full validator run should produce correct output."""
        summaries = [
            ABTestSummary(url="http://a.com", domain="a.com", n_control=1000, n_treatment=1000, p_value=0.05, effect_size=0.10),
            ABTestSummary(url="http://b.com", domain="b.com", n_control=-100, n_treatment=100, p_value=0.01, effect_size=0.20)
        ]
        reconstructed = [
            {"reconstructed_p": 0.05, "reconstructed_effect": 0.10},
            {"reconstructed_p": 0.10, "reconstructed_effect": 0.25}
        ]

        output_path = tmp_path / "audit_report.json"
        records = run_validator(summaries, reconstructed, output_path)

        assert len(records) == 2
        assert records[0].is_inconsistent is False
        assert records[1].is_inconsistent is True
        assert output_path.exists()

        with open(output_path, 'r') as f:
            report = json.load(f)

        assert report["total_records"] == 2
        assert report["inconsistent_count"] == 1