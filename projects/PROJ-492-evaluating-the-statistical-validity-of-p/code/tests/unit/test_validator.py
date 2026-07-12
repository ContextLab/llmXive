"""
Unit tests for the inconsistency validator (T025).

Tests cover:
- Absolute p-value difference > 0.05 threshold
- Relative effect-size difference > 5% threshold
- Sample-size mismatch detection and exclusion from prevalence estimates
- Data quality warning generation
"""

import json
import pytest
from pathlib import Path
from datetime import datetime

from code.src.audit.validator import (
    validate_p_value_consistency,
    validate_effect_size_consistency,
    check_sample_size_mismatch,
    create_audit_record,
    validate_single_summary,
    validate_all_summaries,
    filter_for_prevalence_estimation,
    run_validator,
    P_VALUE_THRESHOLD,
    EFFECT_SIZE_RELATIVE_THRESHOLD
)
from code.src.models.data_models import ABTestSummary


class TestPValueConsistency:
    """Test absolute p-value difference threshold (FR-004)."""

    def test_p_value_within_threshold(self):
        """p-value difference <= 0.05 should be consistent."""
        is_consistent, diff = validate_p_value_consistency(0.03, 0.05)
        assert is_consistent is True
        assert abs(diff - 0.02) < 1e-10

    def test_p_value_exactly_at_threshold(self):
        """p-value difference == 0.05 should be consistent."""
        is_consistent, diff = validate_p_value_consistency(0.03, 0.08)
        assert is_consistent is True
        assert abs(diff - 0.05) < 1e-10

    def test_p_value_exceeds_threshold(self):
        """p-value difference > 0.05 should be inconsistent."""
        is_consistent, diff = validate_p_value_consistency(0.03, 0.10)
        assert is_consistent is False
        assert abs(diff - 0.07) < 1e-10

    def test_p_value_large_difference(self):
        """Large p-value difference should be inconsistent."""
        is_consistent, diff = validate_p_value_consistency(0.01, 0.50)
        assert is_consistent is False
        assert abs(diff - 0.49) < 1e-10


class TestEffectSizeConsistency:
    """Test relative effect-size difference threshold (FR-004)."""

    def test_effect_size_within_threshold(self):
        """Relative effect-size difference <= 5% should be consistent."""
        is_consistent, diff = validate_effect_size_consistency(0.10, 0.105)
        assert is_consistent is True
        assert diff <= EFFECT_SIZE_RELATIVE_THRESHOLD

    def test_effect_size_exactly_at_threshold(self):
        """Relative effect-size difference == 5% should be consistent."""
        is_consistent, diff = validate_effect_size_consistency(0.10, 0.10526)
        assert is_consistent is True
        assert abs(diff - 0.05) < 0.001

    def test_effect_size_exceeds_threshold(self):
        """Relative effect-size difference > 5% should be inconsistent."""
        is_consistent, diff = validate_effect_size_consistency(0.10, 0.11)
        assert is_consistent is False
        assert diff > EFFECT_SIZE_RELATIVE_THRESHOLD

    def test_effect_size_zero_values(self):
        """Zero effect sizes should not cause division errors."""
        is_consistent, diff = validate_effect_size_consistency(0.0, 0.0)
        assert is_consistent is True
        assert diff == 0.0


class TestSampleSizeMismatch:
    """Test sample-size mismatch detection (FR-004b)."""

    def test_no_mismatch(self):
        """Matching sample sizes should not trigger mismatch."""
        summary = ABTestSummary(
            url="https://example.com/test1",
            domain="example.com",
            n_control=1000,
            n_treatment=1000,
            reconstructed_n_control=1000,
            reconstructed_n_treatment=1000,
            p_value=0.03,
            reconstructed_p_value=0.03,
            effect_size=0.1,
            reconstructed_effect_size=0.1
        )
        assert check_sample_size_mismatch(summary) is False

    def test_control_mismatch(self):
        """Control sample size mismatch should be detected."""
        summary = ABTestSummary(
            url="https://example.com/test2",
            domain="example.com",
            n_control=1000,
            n_treatment=1000,
            reconstructed_n_control=1100,
            reconstructed_n_treatment=1000,
            p_value=0.03,
            reconstructed_p_value=0.03,
            effect_size=0.1,
            reconstructed_effect_size=0.1
        )
        assert check_sample_size_mismatch(summary) is True

    def test_treatment_mismatch(self):
        """Treatment sample size mismatch should be detected."""
        summary = ABTestSummary(
            url="https://example.com/test3",
            domain="example.com",
            n_control=1000,
            n_treatment=1000,
            reconstructed_n_control=1000,
            reconstructed_n_treatment=900,
            p_value=0.03,
            reconstructed_p_value=0.03,
            effect_size=0.1,
            reconstructed_effect_size=0.1
        )
        assert check_sample_size_mismatch(summary) is True

    def test_missing_sample_sizes(self):
        """Missing sample sizes should trigger mismatch."""
        summary = ABTestSummary(
            url="https://example.com/test4",
            domain="example.com",
            n_control=None,
            n_treatment=1000,
            reconstructed_n_control=1000,
            reconstructed_n_treatment=1000,
            p_value=0.03,
            reconstructed_p_value=0.03,
            effect_size=0.1,
            reconstructed_effect_size=0.1
        )
        assert check_sample_size_mismatch(summary) is True


class TestAuditRecordCreation:
    """Test AuditRecord generation with warnings."""

    def test_consistent_record(self):
        """Consistent record should have no warnings."""
        summary = ABTestSummary(
            url="https://example.com/test5",
            domain="example.com",
            n_control=1000,
            n_treatment=1000,
            reconstructed_n_control=1000,
            reconstructed_n_treatment=1000,
            p_value=0.03,
            reconstructed_p_value=0.03,
            effect_size=0.1,
            reconstructed_effect_size=0.1
        )
        record = create_audit_record(summary, True, 0.0, 0.0, False)
        assert record.is_consistent is True
        assert record.data_quality_warning is None
        assert "SAMPLE_SIZE_MISMATCH" not in (record.audit_notes or "")

    def test_sample_size_mismatch_record(self):
        """Sample size mismatch should generate data_quality_warning."""
        summary = ABTestSummary(
            url="https://example.com/test6",
            domain="example.com",
            n_control=1000,
            n_treatment=1000,
            reconstructed_n_control=1100,
            reconstructed_n_treatment=1000,
            p_value=0.03,
            reconstructed_p_value=0.03,
            effect_size=0.1,
            reconstructed_effect_size=0.1
        )
        record = create_audit_record(summary, True, 0.0, 0.0, True)
        assert record.data_quality_warning is not None
        assert "SAMPLE_SIZE_MISMATCH" in record.audit_notes
        assert "excluded from aggregate prevalence estimates" in record.data_quality_warning

    def test_p_value_inconsistent_record(self):
        """P-value inconsistency should be noted in audit_notes."""
        summary = ABTestSummary(
            url="https://example.com/test7",
            domain="example.com",
            n_control=1000,
            n_treatment=1000,
            reconstructed_n_control=1000,
            reconstructed_n_treatment=1000,
            p_value=0.03,
            reconstructed_p_value=0.10,
            effect_size=0.1,
            reconstructed_effect_size=0.1
        )
        record = create_audit_record(summary, False, 0.07, 0.0, False)
        assert record.is_consistent is False
        assert "P_VALUE_INCONSISTENT" in record.audit_notes


class TestFilteringForPrevalence:
    """Test exclusion of sample-size mismatch entries from prevalence estimates."""

    def test_filter_excludes_mismatches(self):
        """Records with sample-size mismatch should be filtered out."""
        records = [
            create_audit_record(
                ABTestSummary(
                    url=f"https://example.com/test{i}",
                    domain="example.com",
                    n_control=1000,
                    n_treatment=1000,
                    reconstructed_n_control=1000,
                    reconstructed_n_treatment=1000,
                    p_value=0.03,
                    reconstructed_p_value=0.03,
                    effect_size=0.1,
                    reconstructed_effect_size=0.1
                ),
                True, 0.0, 0.0, False
            )
            for i in range(5)
        ] + [
            create_audit_record(
                ABTestSummary(
                    url="https://example.com/mismatch",
                    domain="example.com",
                    n_control=1000,
                    n_treatment=1000,
                    reconstructed_n_control=1100,
                    reconstructed_n_treatment=1000,
                    p_value=0.03,
                    reconstructed_p_value=0.03,
                    effect_size=0.1,
                    reconstructed_effect_size=0.1
                ),
                True, 0.0, 0.0, True
            )
        ]

        filtered = filter_for_prevalence_estimation(records)
        assert len(filtered) == 5
        assert len(records) == 6
        assert all("SAMPLE_SIZE_MISMATCH" not in r.audit_notes for r in filtered)

    def test_filter_keeps_valid_records(self):
        """Valid records should be kept in filtered list."""
        records = [
            create_audit_record(
                ABTestSummary(
                    url=f"https://example.com/test{i}",
                    domain="example.com",
                    n_control=1000,
                    n_treatment=1000,
                    reconstructed_n_control=1000,
                    reconstructed_n_treatment=1000,
                    p_value=0.03,
                    reconstructed_p_value=0.03,
                    effect_size=0.1,
                    reconstructed_effect_size=0.1
                ),
                True, 0.0, 0.0, False
            )
            for i in range(10)
        ]

        filtered = filter_for_prevalence_estimation(records)
        assert len(filtered) == 10


class TestEndToEndValidation:
    """End-to-end validation tests."""

    def test_validate_single_summary(self):
        """Single summary validation should produce correct record."""
        summary = ABTestSummary(
            url="https://example.com/single",
            domain="example.com",
            n_control=1000,
            n_treatment=1000,
            reconstructed_n_control=1000,
            reconstructed_n_treatment=1000,
            p_value=0.03,
            reconstructed_p_value=0.03,
            effect_size=0.1,
            reconstructed_effect_size=0.1
        )
        record = validate_single_summary(summary)
        assert record.is_consistent is True
        assert record.data_quality_warning is None

    def test_validate_single_summary_with_mismatch(self):
        """Single summary with mismatch should produce warning record."""
        summary = ABTestSummary(
            url="https://example.com/mismatch_single",
            domain="example.com",
            n_control=1000,
            n_treatment=1000,
            reconstructed_n_control=1100,
            reconstructed_n_treatment=1000,
            p_value=0.03,
            reconstructed_p_value=0.03,
            effect_size=0.1,
            reconstructed_effect_size=0.1
        )
        record = validate_single_summary(summary)
        assert record.data_quality_warning is not None
        assert "SAMPLE_SIZE_MISMATCH" in record.audit_notes

    def test_validate_all_summaries(self):
        """Batch validation should process all summaries."""
        summaries = [
            ABTestSummary(
                url=f"https://example.com/test{i}",
                domain="example.com",
                n_control=1000,
                n_treatment=1000,
                reconstructed_n_control=1000,
                reconstructed_n_treatment=1000,
                p_value=0.03,
                reconstructed_p_value=0.03,
                effect_size=0.1,
                reconstructed_effect_size=0.1
            )
            for i in range(5)
        ]
        records = validate_all_summaries(summaries)
        assert len(records) == 5
        assert all(r.is_consistent for r in records)

    def test_run_validator_creates_output(self, tmp_path):
        """Validator should create output JSON file."""
        # Create test input
        input_path = tmp_path / "input_summaries.json"
        summaries = [
            {
                "url": f"https://example.com/test{i}",
                "domain": "example.com",
                "n_control": 1000,
                "n_treatment": 1000,
                "reconstructed_n_control": 1000,
                "reconstructed_n_treatment": 1000,
                "p_value": 0.03,
                "reconstructed_p_value": 0.03,
                "effect_size": 0.1,
                "reconstructed_effect_size": 0.1
            }
            for i in range(3)
        ]
        with open(input_path, 'w') as f:
            json.dump(summaries, f)

        output_path = tmp_path / "audit_report.json"

        all_records, filtered_records = run_validator(input_path, output_path)

        assert output_path.exists()
        assert len(all_records) == 3
        assert len(filtered_records) == 3

        # Verify output file content
        with open(output_path, 'r') as f:
            report = json.load(f)
        assert "audit_records" in report
        assert report["total_records"] == 3
        assert report["consistent_count"] == 3