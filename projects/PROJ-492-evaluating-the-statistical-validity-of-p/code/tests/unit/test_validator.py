"""
Unit tests for the inconsistency validator module (T025).

Tests cover:
- Absolute p-value difference threshold (> 0.05)
- Relative effect-size difference threshold (> 5%)
- Sample-size mismatch detection and exclusion from prevalence
- AuditRecord generation with data_quality_warning
"""

import json
import tempfile
from pathlib import Path
from unittest.mock import MagicMock

import pytest
import numpy as np

from code.src.audit.validator import (
    calculate_absolute_p_difference,
    calculate_relative_effect_size_difference,
    detect_sample_size_mismatch,
    check_p_value_consistency,
    check_effect_size_consistency,
    create_audit_record,
    validate_summary,
    filter_for_prevalence,
    validate_all_summaries,
    write_audit_report,
    P_VALUE_THRESHOLD,
    EFFECT_SIZE_RELATIVE_THRESHOLD,
)
from code.src.models.data_models import ABTestSummary, AuditRecord


class TestPValueDifference:
    """Tests for p-value difference calculations."""

    def test_absolute_p_difference_within_threshold(self):
        """Test p-value difference within 0.05 threshold."""
        diff = calculate_absolute_p_difference(0.04, 0.03)
        assert diff == 0.01
        assert diff <= P_VALUE_THRESHOLD

    def test_absolute_p_difference_exceeds_threshold(self):
        """Test p-value difference exceeding 0.05 threshold."""
        diff = calculate_absolute_p_difference(0.10, 0.03)
        assert diff == 0.07
        assert diff > P_VALUE_THRESHOLD

    def test_p_value_consistency_pass(self):
        """Test p-value consistency check when within threshold."""
        is_consistent, msg = check_p_value_consistency(0.04, 0.03)
        assert is_consistent
        assert "within threshold" in msg

    def test_p_value_consistency_fail(self):
        """Test p-value consistency check when exceeding threshold."""
        is_consistent, msg = check_p_value_consistency(0.10, 0.03)
        assert not is_consistent
        assert "exceeds threshold" in msg


class TestEffectSizeDifference:
    """Tests for effect-size difference calculations."""

    def test_relative_effect_size_within_threshold(self):
        """Test relative effect-size difference within 5% threshold."""
        # 10% vs 10.5% is 5% relative difference
        diff = calculate_relative_effect_size_difference(0.105, 0.10)
        assert abs(diff - 0.05) < 1e-6
        assert diff <= EFFECT_SIZE_RELATIVE_THRESHOLD

    def test_relative_effect_size_exceeds_threshold(self):
        """Test relative effect-size difference exceeding 5% threshold."""
        # 10% vs 11% is 10% relative difference
        diff = calculate_relative_effect_size_difference(0.11, 0.10)
        assert abs(diff - 0.10) < 1e-6
        assert diff > EFFECT_SIZE_RELATIVE_THRESHOLD

    def test_relative_effect_size_zero_baseline(self):
        """Test relative effect-size with zero baseline."""
        # Both zero -> 0 difference
        diff = calculate_relative_effect_size_difference(0.0, 0.0)
        assert diff == 0.0

        # Non-zero vs zero -> 100% difference
        diff = calculate_relative_effect_size_difference(0.1, 0.0)
        assert diff == 1.0

    def test_effect_size_consistency_pass(self):
        """Test effect-size consistency check when within threshold."""
        is_consistent, msg = check_effect_size_consistency(0.105, 0.10)
        assert is_consistent
        assert "within threshold" in msg

    def test_effect_size_consistency_fail(self):
        """Test effect-size consistency check when exceeding threshold."""
        is_consistent, msg = check_effect_size_consistency(0.11, 0.10)
        assert not is_consistent
        assert "exceeds threshold" in msg


class TestSampleSizeMismatch:
    """Tests for sample-size mismatch detection."""

    def test_valid_sample_sizes(self):
        """Test that valid sample sizes are not flagged."""
        summary = ABTestSummary(
            url="https://example.com/test",
            domain="example.com",
            reported_p_value=0.03,
            reported_effect_size=0.05,
            sample_size_control=1000,
            sample_size_treatment=1000,
            conversion_rate_control=0.10,
            conversion_rate_treatment=0.11,
            outcome_type="binary"
        )
        assert not detect_sample_size_mismatch(summary)

    def test_missing_sample_size_control(self):
        """Test that missing control sample size is flagged."""
        summary = ABTestSummary(
            url="https://example.com/test",
            domain="example.com",
            reported_p_value=0.03,
            reported_effect_size=0.05,
            sample_size_control=None,
            sample_size_treatment=1000,
            conversion_rate_control=0.10,
            conversion_rate_treatment=0.11,
            outcome_type="binary"
        )
        assert detect_sample_size_mismatch(summary)

    def test_missing_sample_size_treatment(self):
        """Test that missing treatment sample size is flagged."""
        summary = ABTestSummary(
            url="https://example.com/test",
            domain="example.com",
            reported_p_value=0.03,
            reported_effect_size=0.05,
            sample_size_control=1000,
            sample_size_treatment=None,
            conversion_rate_control=0.10,
            conversion_rate_treatment=0.11,
            outcome_type="binary"
        )
        assert detect_sample_size_mismatch(summary)

    def test_zero_sample_size(self):
        """Test that zero sample size is flagged."""
        summary = ABTestSummary(
            url="https://example.com/test",
            domain="example.com",
            reported_p_value=0.03,
            reported_effect_size=0.05,
            sample_size_control=0,
            sample_size_treatment=1000,
            conversion_rate_control=0.10,
            conversion_rate_treatment=0.11,
            outcome_type="binary"
        )
        assert detect_sample_size_mismatch(summary)


class TestAuditRecordCreation:
    """Tests for AuditRecord creation and data_quality_warning."""

    def test_record_with_sample_size_mismatch_has_warning(self):
        """Test that sample-size mismatch generates data_quality_warning."""
        summary = ABTestSummary(
            url="https://example.com/test",
            domain="example.com",
            reported_p_value=0.03,
            reported_effect_size=0.05,
            sample_size_control=None,
            sample_size_treatment=1000,
            conversion_rate_control=0.10,
            conversion_rate_treatment=0.11,
            outcome_type="binary"
        )
        
        record = create_audit_record(
            summary=summary,
            reconstructed_p=0.03,
            reported_p=0.03,
            reconstructed_effect=0.05,
            reported_effect=0.05,
            p_consistent=True,
            effect_consistent=True,
            sample_size_mismatch=True,
            reconstruction_success=True
        )
        
        assert record.data_quality_warning is True
        assert record.is_inconsistent is True
        assert any("SAMPLE_SIZE_MISMATCH" in note for note in record.inconsistency_reasons)

    def test_record_without_issues_has_no_warning(self):
        """Test that valid records have no data_quality_warning."""
        summary = ABTestSummary(
            url="https://example.com/test",
            domain="example.com",
            reported_p_value=0.03,
            reported_effect_size=0.05,
            sample_size_control=1000,
            sample_size_treatment=1000,
            conversion_rate_control=0.10,
            conversion_rate_treatment=0.11,
            outcome_type="binary"
        )
        
        record = create_audit_record(
            summary=summary,
            reconstructed_p=0.03,
            reported_p=0.03,
            reconstructed_effect=0.05,
            reported_effect=0.05,
            p_consistent=True,
            effect_consistent=True,
            sample_size_mismatch=False,
            reconstruction_success=True
        )
        
        assert record.data_quality_warning is False
        assert record.is_inconsistent is False

    def test_record_with_p_value_inconsistency(self):
        """Test that p-value inconsistency flags record."""
        summary = ABTestSummary(
            url="https://example.com/test",
            domain="example.com",
            reported_p_value=0.03,
            reported_effect_size=0.05,
            sample_size_control=1000,
            sample_size_treatment=1000,
            conversion_rate_control=0.10,
            conversion_rate_treatment=0.11,
            outcome_type="binary"
        )
        
        record = create_audit_record(
            summary=summary,
            reconstructed_p=0.10,  # Exceeds threshold
            reported_p=0.03,
            reconstructed_effect=0.05,
            reported_effect=0.05,
            p_consistent=False,
            effect_consistent=True,
            sample_size_mismatch=False,
            reconstruction_success=True
        )
        
        assert record.is_inconsistent is True
        assert record.data_quality_warning is False  # Not a data quality issue, just inconsistency

    def test_record_with_reconstruction_failure(self):
        """Test that reconstruction failure generates warning."""
        summary = ABTestSummary(
            url="https://example.com/test",
            domain="example.com",
            reported_p_value=0.03,
            reported_effect_size=0.05,
            sample_size_control=1000,
            sample_size_treatment=1000,
            conversion_rate_control=0.10,
            conversion_rate_treatment=0.11,
            outcome_type="binary"
        )
        
        record = create_audit_record(
            summary=summary,
            reconstructed_p=0.0,
            reported_p=0.03,
            reconstructed_effect=0.0,
            reported_effect=0.05,
            p_consistent=False,
            effect_consistent=False,
            sample_size_mismatch=False,
            reconstruction_success=False
        )
        
        assert record.data_quality_warning is True
        assert record.is_inconsistent is True


class TestPrevalenceExclusion:
    """Tests for FR-004b: exclusion of sample-size mismatches from prevalence."""

    def test_filter_excludes_sample_size_mismatches(self):
        """Test that filter_for_prevalence excludes records with data_quality_warning."""
        # Create records with and without warnings
        record_good = AuditRecord(
            url="https://good.com",
            domain="good.com",
            reported_p_value=0.03,
            reconstructed_p_value=0.03,
            reported_effect_size=0.05,
            reconstructed_effect_size=0.05,
            sample_size_control=1000,
            sample_size_treatment=1000,
            is_inconsistent=False,
            inconsistency_reasons=["All checks passed"],
            data_quality_warning=False
        )
        
        record_mismatch = AuditRecord(
            url="https://bad.com",
            domain="bad.com",
            reported_p_value=0.03,
            reconstructed_p_value=0.03,
            reported_effect_size=0.05,
            reconstructed_effect_size=0.05,
            sample_size_control=None,
            sample_size_treatment=1000,
            is_inconsistent=True,
            inconsistency_reasons=["SAMPLE_SIZE_MISMATCH"],
            data_quality_warning=True
        )
        
        records = [record_good, record_mismatch]
        filtered = filter_for_prevalence(records)
        
        assert len(filtered) == 1
        assert filtered[0].url == "https://good.com"
        assert record_mismatch not in filtered

    def test_filter_includes_valid_records(self):
        """Test that filter_for_prevalence includes all valid records."""
        records = [
            AuditRecord(
                url=f"https://test{i}.com",
                domain=f"test{i}.com",
                reported_p_value=0.03,
                reconstructed_p_value=0.03,
                reported_effect_size=0.05,
                reconstructed_effect_size=0.05,
                sample_size_control=1000,
                sample_size_treatment=1000,
                is_inconsistent=False,
                inconsistency_reasons=["All checks passed"],
                data_quality_warning=False
            )
            for i in range(5)
        ]
        
        filtered = filter_for_prevalence(records)
        assert len(filtered) == 5


class TestWriteAuditReport:
    """Tests for audit report file generation."""

    def test_write_audit_report_creates_json(self):
        """Test that write_audit_report creates a valid JSON file."""
        records = [
            AuditRecord(
                url="https://example.com",
                domain="example.com",
                reported_p_value=0.03,
                reconstructed_p_value=0.03,
                reported_effect_size=0.05,
                reconstructed_effect_size=0.05,
                sample_size_control=1000,
                sample_size_treatment=1000,
                is_inconsistent=False,
                inconsistency_reasons=["All checks passed"],
                data_quality_warning=False
            )
        ]
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "audit_report.json"
            write_audit_report(records, output_path)
            
            assert output_path.exists()
            
            with open(output_path, 'r') as f:
                data = json.load(f)
            
            assert data["total_records"] == 1
            assert data["inconsistent_count"] == 0
            assert data["data_quality_warnings"] == 0
            assert len(data["records"]) == 1
            assert data["records"][0]["url"] == "https://example.com"

    def test_write_audit_report_with_mismatches(self):
        """Test report generation includes mismatch counts."""
        records = [
            AuditRecord(
                url="https://good.com",
                domain="good.com",
                reported_p_value=0.03,
                reconstructed_p_value=0.03,
                reported_effect_size=0.05,
                reconstructed_effect_size=0.05,
                sample_size_control=1000,
                sample_size_treatment=1000,
                is_inconsistent=False,
                inconsistency_reasons=["All checks passed"],
                data_quality_warning=False
            ),
            AuditRecord(
                url="https://bad.com",
                domain="bad.com",
                reported_p_value=0.03,
                reconstructed_p_value=0.03,
                reported_effect_size=0.05,
                reconstructed_effect_size=0.05,
                sample_size_control=None,
                sample_size_treatment=1000,
                is_inconsistent=True,
                inconsistency_reasons=["SAMPLE_SIZE_MISMATCH"],
                data_quality_warning=True
            )
        ]
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "audit_report.json"
            write_audit_report(records, output_path)
            
            with open(output_path, 'r') as f:
                data = json.load(f)
            
            assert data["total_records"] == 2
            assert data["inconsistent_count"] == 1
            assert data["data_quality_warnings"] == 1
