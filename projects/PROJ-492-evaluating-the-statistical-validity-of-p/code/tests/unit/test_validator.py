"""Unit tests for the validator module covering statistical consistency checks."""
import pytest
import json
import tempfile
from datetime import datetime
from pathlib import Path
from unittest.mock import patch, MagicMock

from code.src.audit.validator import (
    calculate_absolute_p_difference,
    calculate_relative_effect_size_difference,
    detect_sample_size_mismatch,
    check_p_value_consistency,
    check_effect_size_consistency,
    create_audit_record,
    validate_summary,
    validate_all_summaries,
    write_audit_report,
    filter_for_prevalence,
)
from code.src.models.data_models import ABTestSummary, AuditRecord


class TestPValueDifference:
    """Tests for absolute p-value difference calculation."""

    def test_absolute_p_difference_basic(self):
        """Test calculation of absolute p-value difference."""
        reported_p = 0.03
        reconstructed_p = 0.08
        diff = calculate_absolute_p_difference(reported_p, reconstructed_p)
        assert diff == 0.05

    def test_absolute_p_difference_zero(self):
        """Test when p-values are identical."""
        reported_p = 0.05
        reconstructed_p = 0.05
        diff = calculate_absolute_p_difference(reported_p, reconstructed_p)
        assert diff == 0.0

    def test_absolute_p_difference_threshold(self):
        """Test threshold check for inconsistency flagging (> 0.05)."""
        # Below threshold - should NOT flag
        assert calculate_absolute_p_difference(0.05, 0.09) < 0.05
        # Above threshold - should flag
        assert calculate_absolute_p_difference(0.05, 0.11) > 0.05

    def test_absolute_p_difference_handles_none(self):
        """Test handling of None values."""
        assert calculate_absolute_p_difference(None, 0.05) is None
        assert calculate_absolute_p_difference(0.05, None) is None
        assert calculate_absolute_p_difference(None, None) is None


class TestEffectSizeDifference:
    """Tests for relative effect-size difference calculation."""

    def test_relative_effect_size_basic(self):
        """Test calculation of relative effect-size difference."""
        reported_effect = 0.10
        reconstructed_effect = 0.15
        diff = calculate_relative_effect_size_difference(reported_effect, reconstructed_effect)
        # |0.10 - 0.15| / |0.10| = 0.05 / 0.10 = 0.5
        assert abs(diff - 0.5) < 1e-9

    def test_relative_effect_size_zero_baseline(self):
        """Test when baseline effect is zero (division by zero handling)."""
        diff = calculate_relative_effect_size_difference(0.0, 0.10)
        assert diff is None

    def test_relative_effect_size_threshold(self):
        """Test threshold check for inconsistency flagging (> 5%)."""
        # Below threshold (5%)
        assert calculate_relative_effect_size_difference(0.10, 0.104) <= 0.05
        # Above threshold (5%)
        assert calculate_relative_effect_size_difference(0.10, 0.106) > 0.05

    def test_relative_effect_size_handles_none(self):
        """Test handling of None values."""
        assert calculate_relative_effect_size_difference(None, 0.10) is None
        assert calculate_relative_effect_size_difference(0.10, None) is None
        assert calculate_relative_effect_size_difference(None, None) is None


class TestSampleSizeMismatch:
    """Tests for sample-size mismatch detection."""

    def test_sample_size_mismatch_detected(self):
        """Test detection of sample-size mismatch between reported and reconstructed."""
        summary = ABTestSummary(
            url="https://example.com/test",
            reported_sample_size_a=1000,
            reported_sample_size_b=1000,
            reconstructed_sample_size_a=950,
            reconstructed_sample_size_b=950,
            reported_p_value=0.03,
            reconstructed_p_value=0.08,
            reported_effect_size=0.10,
            reconstructed_effect_size=0.15,
            test_type="binary",
            timestamp=datetime.now(),
        )
        assert detect_sample_size_mismatch(summary) is True

    def test_sample_size_match(self):
        """Test when sample sizes match."""
        summary = ABTestSummary(
            url="https://example.com/test",
            reported_sample_size_a=1000,
            reported_sample_size_b=1000,
            reconstructed_sample_size_a=1000,
            reconstructed_sample_size_b=1000,
            reported_p_value=0.03,
            reconstructed_p_value=0.03,
            reported_effect_size=0.10,
            reconstructed_effect_size=0.10,
            test_type="binary",
            timestamp=datetime.now(),
        )
        assert detect_sample_size_mismatch(summary) is False

    def test_sample_size_mismatch_handles_none(self):
        """Test when sample sizes are None."""
        summary = ABTestSummary(
            url="https://example.com/test",
            reported_sample_size_a=None,
            reported_sample_size_b=None,
            reconstructed_sample_size_a=None,
            reconstructed_sample_size_b=None,
            reported_p_value=0.03,
            reconstructed_p_value=0.08,
            reported_effect_size=0.10,
            reconstructed_effect_size=0.15,
            test_type="binary",
            timestamp=datetime.now(),
        )
        assert detect_sample_size_mismatch(summary) is False


class TestPValueConsistency:
    """Tests for p-value consistency checking with inequality handling."""

    def test_p_value_consistency_within_threshold(self):
        """Test p-values within consistency threshold."""
        summary = ABTestSummary(
            url="https://example.com/test",
            reported_sample_size_a=1000,
            reported_sample_size_b=1000,
            reconstructed_sample_size_a=1000,
            reconstructed_sample_size_b=1000,
            reported_p_value=0.05,
            reconstructed_p_value=0.08,
            reported_effect_size=0.10,
            reconstructed_effect_size=0.12,
            test_type="binary",
            timestamp=datetime.now(),
        )
        is_consistent, reason = check_p_value_consistency(summary)
        assert is_consistent is True

    def test_p_value_consistency_exceeds_threshold(self):
        """Test p-values exceeding consistency threshold (> 0.05 absolute diff)."""
        summary = ABTestSummary(
            url="https://example.com/test",
            reported_sample_size_a=1000,
            reported_sample_size_b=1000,
            reconstructed_sample_size_a=1000,
            reconstructed_sample_size_b=1000,
            reported_p_value=0.03,
            reconstructed_p_value=0.10,
            reported_effect_size=0.10,
            reconstructed_effect_size=0.15,
            test_type="binary",
            timestamp=datetime.now(),
        )
        is_consistent, reason = check_p_value_consistency(summary)
        assert is_consistent is False
        assert "p-value" in reason.lower()

    def test_p_value_consistency_inequality_handling(self):
        """Test handling of inequality p-values (e.g., p < 0.05)."""
        # When reported p-value is an inequality, use the bound for comparison
        summary = ABTestSummary(
            url="https://example.com/test",
            reported_sample_size_a=1000,
            reported_sample_size_b=1000,
            reconstructed_sample_size_a=1000,
            reconstructed_sample_size_b=1000,
            reported_p_value=0.001,  # Represents p < 0.001
            reconstructed_p_value=0.05,
            reported_effect_size=0.10,
            reconstructed_effect_size=0.12,
            test_type="binary",
            timestamp=datetime.now(),
        )
        # Large difference should flag inconsistency
        is_consistent, reason = check_p_value_consistency(summary)
        assert is_consistent is False

    def test_p_value_consistency_handles_none(self):
        """Test when p-values are None."""
        summary = ABTestSummary(
            url="https://example.com/test",
            reported_sample_size_a=1000,
            reported_sample_size_b=1000,
            reconstructed_sample_size_a=1000,
            reconstructed_sample_size_b=1000,
            reported_p_value=None,
            reconstructed_p_value=0.05,
            reported_effect_size=0.10,
            reconstructed_effect_size=0.12,
            test_type="binary",
            timestamp=datetime.now(),
        )
        is_consistent, reason = check_p_value_consistency(summary)
        assert is_consistent is False


class TestEffectSizeConsistency:
    """Tests for effect-size consistency checking."""

    def test_effect_size_consistency_within_threshold(self):
        """Test effect sizes within consistency threshold (≤ 5%)."""
        summary = ABTestSummary(
            url="https://example.com/test",
            reported_sample_size_a=1000,
            reported_sample_size_b=1000,
            reconstructed_sample_size_a=1000,
            reconstructed_sample_size_b=1000,
            reported_p_value=0.05,
            reconstructed_p_value=0.08,
            reported_effect_size=0.10,
            reconstructed_effect_size=0.104,
            test_type="binary",
            timestamp=datetime.now(),
        )
        is_consistent, reason = check_effect_size_consistency(summary)
        assert is_consistent is True

    def test_effect_size_consistency_exceeds_threshold(self):
        """Test effect sizes exceeding consistency threshold (> 5%)."""
        summary = ABTestSummary(
            url="https://example.com/test",
            reported_sample_size_a=1000,
            reported_sample_size_b=1000,
            reconstructed_sample_size_a=1000,
            reconstructed_sample_size_b=1000,
            reported_p_value=0.05,
            reconstructed_p_value=0.08,
            reported_effect_size=0.10,
            reconstructed_effect_size=0.16,
            test_type="binary",
            timestamp=datetime.now(),
        )
        is_consistent, reason = check_effect_size_consistency(summary)
        assert is_consistent is False
        assert "effect size" in reason.lower()

    def test_effect_size_consistency_handles_none(self):
        """Test when effect sizes are None."""
        summary = ABTestSummary(
            url="https://example.com/test",
            reported_sample_size_a=1000,
            reported_sample_size_b=1000,
            reconstructed_sample_size_a=1000,
            reconstructed_sample_size_b=1000,
            reported_p_value=0.05,
            reconstructed_p_value=0.08,
            reported_effect_size=None,
            reconstructed_effect_size=0.12,
            test_type="binary",
            timestamp=datetime.now(),
        )
        is_consistent, reason = check_effect_size_consistency(summary)
        assert is_consistent is False


class TestAuditRecordCreation:
    """Tests for audit record creation."""

    def test_audit_record_creation_consistent(self):
        """Test creation of audit record for consistent summary."""
        summary = ABTestSummary(
            url="https://example.com/test",
            reported_sample_size_a=1000,
            reported_sample_size_b=1000,
            reconstructed_sample_size_a=1000,
            reconstructed_sample_size_b=1000,
            reported_p_value=0.05,
            reconstructed_p_value=0.06,
            reported_effect_size=0.10,
            reconstructed_effect_size=0.105,
            test_type="binary",
            timestamp=datetime.now(),
        )
        record = create_audit_record(summary, is_inconsistent=False, warnings=[])
        assert record.url == "https://example.com/test"
        assert record.is_inconsistent is False
        assert record.data_quality_warning is False

    def test_audit_record_creation_inconsistent(self):
        """Test creation of audit record for inconsistent summary."""
        summary = ABTestSummary(
            url="https://example.com/test",
            reported_sample_size_a=1000,
            reported_sample_size_b=1000,
            reconstructed_sample_size_a=1000,
            reconstructed_sample_size_b=1000,
            reported_p_value=0.03,
            reconstructed_p_value=0.10,
            reported_effect_size=0.10,
            reconstructed_effect_size=0.16,
            test_type="binary",
            timestamp=datetime.now(),
        )
        record = create_audit_record(summary, is_inconsistent=True, warnings=["p-value discrepancy"])
        assert record.url == "https://example.com/test"
        assert record.is_inconsistent is True
        assert "p-value discrepancy" in record.audit_notes

    def test_audit_record_creation_with_sample_size_warning(self):
        """Test creation of audit record with data_quality_warning for sample-size mismatch."""
        summary = ABTestSummary(
            url="https://example.com/test",
            reported_sample_size_a=1000,
            reported_sample_size_b=1000,
            reconstructed_sample_size_a=950,
            reconstructed_sample_size_b=950,
            reported_p_value=0.05,
            reconstructed_p_value=0.06,
            reported_effect_size=0.10,
            reconstructed_effect_size=0.105,
            test_type="binary",
            timestamp=datetime.now(),
        )
        record = create_audit_record(summary, is_inconsistent=False, warnings=["sample size mismatch"])
        assert record.data_quality_warning is True
        assert "sample size" in record.audit_notes.lower()


class TestValidateSummary:
    """Tests for individual summary validation."""

    def test_validate_summary_complete(self):
        """Test validation of a complete summary."""
        summary = ABTestSummary(
            url="https://example.com/test",
            reported_sample_size_a=1000,
            reported_sample_size_b=1000,
            reconstructed_sample_size_a=1000,
            reconstructed_sample_size_b=1000,
            reported_p_value=0.05,
            reconstructed_p_value=0.06,
            reported_effect_size=0.10,
            reconstructed_effect_size=0.105,
            test_type="binary",
            timestamp=datetime.now(),
        )
        is_valid, record = validate_summary(summary)
        assert is_valid is True
        assert record.is_inconsistent is False

    def test_validate_summary_inconsistent_p_value(self):
        """Test validation with inconsistent p-value."""
        summary = ABTestSummary(
            url="https://example.com/test",
            reported_sample_size_a=1000,
            reported_sample_size_b=1000,
            reconstructed_sample_size_a=1000,
            reconstructed_sample_size_b=1000,
            reported_p_value=0.03,
            reconstructed_p_value=0.10,
            reported_effect_size=0.10,
            reconstructed_effect_size=0.15,
            test_type="binary",
            timestamp=datetime.now(),
        )
        is_valid, record = validate_summary(summary)
        assert is_valid is False
        assert record.is_inconsistent is True


class TestValidateAllSummaries:
    """Tests for batch validation of multiple summaries."""

    def test_validate_all_summaries(self):
        """Test validation of multiple summaries."""
        summaries = [
            ABTestSummary(
                url=f"https://example.com/test{i}",
                reported_sample_size_a=1000,
                reported_sample_size_b=1000,
                reconstructed_sample_size_a=1000,
                reconstructed_sample_size_b=1000,
                reported_p_value=0.05,
                reconstructed_p_value=0.06,
                reported_effect_size=0.10,
                reconstructed_effect_size=0.105,
                test_type="binary",
                timestamp=datetime.now(),
            )
            for i in range(3)
        ]
        records = validate_all_summaries(summaries)
        assert len(records) == 3
        for record in records:
            assert isinstance(record, AuditRecord)

    def test_validate_all_summaries_with_warnings(self):
        """Test validation with sample-size mismatches generating warnings."""
        summaries = [
            ABTestSummary(
                url="https://example.com/test1",
                reported_sample_size_a=1000,
                reported_sample_size_b=1000,
                reconstructed_sample_size_a=950,
                reconstructed_sample_size_b=950,
                reported_p_value=0.05,
                reconstructed_p_value=0.06,
                reported_effect_size=0.10,
                reconstructed_effect_size=0.105,
                test_type="binary",
                timestamp=datetime.now(),
            ),
            ABTestSummary(
                url="https://example.com/test2",
                reported_sample_size_a=1000,
                reported_sample_size_b=1000,
                reconstructed_sample_size_a=1000,
                reconstructed_sample_size_b=1000,
                reported_p_value=0.03,
                reconstructed_p_value=0.10,
                reported_effect_size=0.10,
                reconstructed_effect_size=0.16,
                test_type="binary",
                timestamp=datetime.now(),
            ),
        ]
        records = validate_all_summaries(summaries)
        assert len(records) == 2
        # First should have data_quality_warning
        assert records[0].data_quality_warning is True
        # Second should be inconsistent
        assert records[1].is_inconsistent is True


class TestWriteAuditReport:
    """Tests for audit report writing."""

    def test_write_audit_report(self):
        """Test writing audit report to file."""
        records = [
            AuditRecord(
                url="https://example.com/test1",
                is_inconsistent=False,
                data_quality_warning=False,
                audit_notes="",
                timestamp=datetime.now(),
            ),
            AuditRecord(
                url="https://example.com/test2",
                is_inconsistent=True,
                data_quality_warning=False,
                audit_notes="p-value discrepancy",
                timestamp=datetime.now(),
            ),
        ]
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "audit_report.json"
            write_audit_report(records, output_path)
            assert output_path.exists()
            with open(output_path, "r") as f:
                data = json.load(f)
            assert len(data) == 2

    def test_write_audit_report_empty(self):
        """Test writing empty audit report."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "audit_report.json"
            write_audit_report([], output_path)
            assert output_path.exists()
            with open(output_path, "r") as f:
                data = json.load(f)
            assert len(data) == 0


class TestFilterForPrevalence:
    """Tests for filtering records for prevalence calculation."""

    def test_filter_for_prevalence_excludes_warnings(self):
        """Test that records with data_quality_warning are excluded."""
        records = [
            AuditRecord(
                url="https://example.com/test1",
                is_inconsistent=False,
                data_quality_warning=False,
                audit_notes="",
                timestamp=datetime.now(),
            ),
            AuditRecord(
                url="https://example.com/test2",
                is_inconsistent=True,
                data_quality_warning=True,
                audit_notes="sample size mismatch",
                timestamp=datetime.now(),
            ),
            AuditRecord(
                url="https://example.com/test3",
                is_inconsistent=True,
                data_quality_warning=False,
                audit_notes="p-value discrepancy",
                timestamp=datetime.now(),
            ),
        ]
        filtered = filter_for_prevalence(records)
        # Should exclude only the one with data_quality_warning
        assert len(filtered) == 2
        assert not any(r.data_quality_warning for r in filtered)

    def test_filter_for_prevalence_empty(self):
        """Test filtering empty list."""
        filtered = filter_for_prevalence([])
        assert len(filtered) == 0