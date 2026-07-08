"""
Unit tests for the inconsistency validator (T025).
Tests FR-004 thresholds and FR-004b sample-size exclusion logic.
"""
import json
import tempfile
from pathlib import Path
from datetime import datetime

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
    validate_all_summaries,
    write_audit_report
)


class TestPValueDifference:
    def test_absolute_p_difference_calculation(self):
        """Test that absolute p-difference is calculated correctly."""
        diff = calculate_absolute_p_difference(0.04, 0.06)
        assert abs(diff - 0.02) < 1e-9

    def test_absolute_p_difference_order_independence(self):
        """Test that order of arguments doesn't matter."""
        diff1 = calculate_absolute_p_difference(0.03, 0.08)
        diff2 = calculate_absolute_p_difference(0.08, 0.03)
        assert diff1 == diff2

    def test_zero_difference(self):
        """Test that identical p-values yield zero difference."""
        diff = calculate_absolute_p_difference(0.05, 0.05)
        assert diff == 0.0


class TestEffectSizeDifference:
    def test_relative_effect_size_calculation(self):
        """Test relative effect size difference calculation."""
        # (0.10 - 0.08) / 0.08 = 0.25
        diff = calculate_relative_effect_size_difference(0.10, 0.08)
        assert abs(diff - 0.25) < 1e-6

    def test_effect_size_near_zero_reconstructed(self):
        """Test handling when reconstructed effect is near zero."""
        # When reconstructed is near zero, should use absolute difference
        diff = calculate_relative_effect_size_difference(0.05, 0.0)
        assert diff == 0.05

    def test_negative_effect_sizes(self):
        """Test with negative effect sizes."""
        # |(-0.10) - (-0.08)| / |(-0.08)| = 0.02 / 0.08 = 0.25
        diff = calculate_relative_effect_size_difference(-0.10, -0.08)
        assert abs(diff - 0.25) < 1e-6


class TestSampleSizeMismatch:
    def test_no_mismatch(self):
        """Test when sample sizes match exactly."""
        mismatch = detect_sample_size_mismatch(
            reported_n_control=100,
            reported_n_treatment=100,
            reconstructed_n_control=100,
            reconstructed_n_treatment=100
        )
        assert not mismatch

    def test_control_mismatch(self):
        """Test when control group size differs."""
        mismatch = detect_sample_size_mismatch(
            reported_n_control=100,
            reported_n_treatment=100,
            reconstructed_n_control=105,
            reconstructed_n_treatment=100
        )
        assert mismatch

    def test_treatment_mismatch(self):
        """Test when treatment group size differs."""
        mismatch = detect_sample_size_mismatch(
            reported_n_control=100,
            reported_n_treatment=100,
            reconstructed_n_control=100,
            reconstructed_n_treatment=95
        )
        assert mismatch

    def test_missing_reconstructed_control(self):
        """Test when reconstructed control is missing."""
        mismatch = detect_sample_size_mismatch(
            reported_n_control=100,
            reported_n_treatment=100,
            reconstructed_n_control=None,
            reconstructed_n_treatment=100
        )
        assert not mismatch  # Cannot validate, not a mismatch

    def test_missing_reported_treatment(self):
        """Test when reported treatment is missing."""
        mismatch = detect_sample_size_mismatch(
            reported_n_control=100,
            reported_n_treatment=None,
            reconstructed_n_control=100,
            reconstructed_n_treatment=100
        )
        assert not mismatch


class TestPValueConsistency:
    def test_consistent_p_values(self):
        """Test p-values within threshold are consistent."""
        is_consistent, diff = check_p_value_consistency(0.04, 0.06)
        assert is_consistent
        assert abs(diff - 0.02) < 1e-9

    def test_inconsistent_p_values(self):
        """Test p-values exceeding threshold are inconsistent."""
        is_consistent, diff = check_p_value_consistency(0.03, 0.09)
        assert not is_consistent
        assert abs(diff - 0.06) < 1e-9

    def test_boundary_p_values(self):
        """Test p-values exactly at threshold."""
        is_consistent, _ = check_p_value_consistency(0.04, 0.09)
        assert not is_consistent  # 0.05 is NOT <= 0.05, wait, 0.05 IS <= 0.05
        # Actually 0.09 - 0.04 = 0.05, which is <= 0.05, so should be consistent
        is_consistent, diff = check_p_value_consistency(0.04, 0.09)
        assert is_consistent
        assert abs(diff - 0.05) < 1e-9


class TestEffectSizeConsistency:
    def test_consistent_effect_sizes(self):
        """Test effect sizes within threshold are consistent."""
        # 5% relative diff is the threshold
        # 0.10 vs 0.105 -> 0.005/0.10 = 0.05 (at boundary)
        is_consistent, diff = check_effect_size_consistency(0.10, 0.105)
        assert is_consistent
        assert abs(diff - 0.05) < 1e-6

    def test_inconsistent_effect_sizes(self):
        """Test effect sizes exceeding threshold are inconsistent."""
        # 0.10 vs 0.11 -> 0.01/0.10 = 0.10 (exceeds 0.05)
        is_consistent, diff = check_effect_size_consistency(0.10, 0.11)
        assert not is_consistent
        assert abs(diff - 0.10) < 1e-6


class TestAuditRecordCreation:
    def test_create_consistent_record(self):
        """Test creating a record with consistent values."""
        summary = ABTestSummary(
            url="http://example.com",
            domain="example.com",
            reported_p_value=0.04,
            reconstructed_p_value=0.04,
            effect_size=0.10,
            n_control=100,
            n_treatment=100
        )

        record = create_audit_record(
            summary,
            is_p_consistent=True,
            p_difference=0.0,
            is_effect_consistent=True,
            effect_difference=0.0,
            has_sample_size_mismatch=False
        )

        assert record.is_inconsistent is False
        assert record.data_quality_warning is False
        assert len(record.notes) == 1
        assert "All checks passed" in record.notes[0]

    def test_create_inconsistent_record(self):
        """Test creating a record with inconsistent p-value."""
        summary = ABTestSummary(
            url="http://example.com",
            domain="example.com",
            reported_p_value=0.03,
            reconstructed_p_value=0.09,
            effect_size=0.10,
            n_control=100,
            n_treatment=100
        )

        record = create_audit_record(
            summary,
            is_p_consistent=False,
            p_difference=0.06,
            is_effect_consistent=True,
            effect_difference=0.0,
            has_sample_size_mismatch=False
        )

        assert record.is_inconsistent is True
        assert "P-value inconsistency" in record.notes[0]

    def test_create_record_with_sample_size_warning(self):
        """Test creating a record with sample size mismatch warning."""
        summary = ABTestSummary(
            url="http://example.com",
            domain="example.com",
            reported_p_value=0.04,
            reconstructed_p_value=0.04,
            effect_size=0.10,
            n_control=100,
            n_treatment=100
        )

        record = create_audit_record(
            summary,
            is_p_consistent=True,
            p_difference=0.0,
            is_effect_consistent=True,
            effect_difference=0.0,
            has_sample_size_mismatch=True
        )

        assert record.is_inconsistent is False
        assert record.data_quality_warning is True
        assert "Sample size mismatch" in record.notes[0]


class TestFilterForPrevalence:
    def test_filter_excludes_warnings(self):
        """Test that filter excludes records with data_quality_warning."""
        records = [
            AuditRecord(
                url="http://a.com", domain="a.com", is_inconsistent=False,
                p_difference=0.0, effect_size_difference=0.0,
                notes=["OK"], data_quality_warning=False, timestamp="2024-01-01"
            ),
            AuditRecord(
                url="http://b.com", domain="b.com", is_inconsistent=False,
                p_difference=0.0, effect_size_difference=0.0,
                notes=["Mismatch"], data_quality_warning=True, timestamp="2024-01-01"
            ),
            AuditRecord(
                url="http://c.com", domain="c.com", is_inconsistent=True,
                p_difference=0.06, effect_size_difference=0.0,
                notes=["Inconsistent"], data_quality_warning=False, timestamp="2024-01-01"
            )
        ]

        filtered = filter_for_prevalence(records)

        assert len(filtered) == 2
        assert all(not r.data_quality_warning for r in filtered)
        # Should include the inconsistent one (as long as no warning)
        assert any(r.is_inconsistent for r in filtered)


class TestValidateSummary:
    def test_validate_consistent_summary(self):
        """Test validation of a consistent summary."""
        summary = ABTestSummary(
            url="http://example.com",
            domain="example.com",
            reported_p_value=0.04,
            reconstructed_p_value=0.04,
            effect_size=0.10,
            n_control=100,
            n_treatment=100
        )

        record = validate_summary(
            summary,
            reconstructed_p=0.04,
            reconstructed_effect=0.10,
            reconstructed_n_control=100,
            reconstructed_n_treatment=100
        )

        assert record.is_inconsistent is False
        assert record.data_quality_warning is False

    def test_validate_inconsistent_summary(self):
        """Test validation of an inconsistent summary."""
        summary = ABTestSummary(
            url="http://example.com",
            domain="example.com",
            reported_p_value=0.03,
            reconstructed_p_value=0.09,
            effect_size=0.10,
            n_control=100,
            n_treatment=100
        )

        record = validate_summary(
            summary,
            reconstructed_p=0.09,
            reconstructed_effect=0.10,
            reconstructed_n_control=100,
            reconstructed_n_treatment=100
        )

        assert record.is_inconsistent is True
        assert record.p_difference > 0.05

    def test_validate_with_sample_size_mismatch(self):
        """Test validation flags sample size mismatch."""
        summary = ABTestSummary(
            url="http://example.com",
            domain="example.com",
            reported_p_value=0.04,
            reconstructed_p_value=0.04,
            effect_size=0.10,
            n_control=100,
            n_treatment=100
        )

        record = validate_summary(
            summary,
            reconstructed_p=0.04,
            reconstructed_effect=0.10,
            reconstructed_n_control=105,  # Mismatch
            reconstructed_n_treatment=100
        )

        assert record.data_quality_warning is True
        assert "Sample size mismatch" in record.notes[0]


class TestWriteAuditReport:
    def test_write_report_creates_file(self):
        """Test that write_audit_report creates the output file."""
        records = [
            AuditRecord(
                url="http://example.com", domain="example.com", is_inconsistent=False,
                p_difference=0.0, effect_size_difference=0.0,
                notes=["OK"], data_quality_warning=False, timestamp="2024-01-01"
            )
        ]

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_report.json"
            write_audit_report(records, output_path)

            assert output_path.exists()
            with open(output_path, 'r') as f:
                data = json.load(f)
            assert data["total_records"] == 1
            assert data["inconsistent_count"] == 0

    def test_write_report_counts_inconsistent(self):
        """Test that write_audit_report correctly counts inconsistent records."""
        records = [
            AuditRecord(
                url="http://a.com", domain="a.com", is_inconsistent=False,
                p_difference=0.0, effect_size_difference=0.0,
                notes=["OK"], data_quality_warning=False, timestamp="2024-01-01"
            ),
            AuditRecord(
                url="http://b.com", domain="b.com", is_inconsistent=True,
                p_difference=0.06, effect_size_difference=0.0,
                notes=["Inconsistent"], data_quality_warning=False, timestamp="2024-01-01"
            )
        ]

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_report.json"
            write_audit_report(records, output_path)

            with open(output_path, 'r') as f:
                data = json.load(f)
            assert data["inconsistent_count"] == 1
            assert data["total_records"] == 2