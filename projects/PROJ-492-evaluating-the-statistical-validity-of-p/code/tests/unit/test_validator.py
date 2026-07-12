"""
Unit tests for the inconsistency validator (T025).

Tests cover:
- Absolute p-difference > 0.05 threshold
- Relative effect-size > 5% threshold
- Sample-size mismatch handling and exclusion from prevalence
- Data quality warning generation
"""

import pytest
from unittest.mock import patch
from pathlib import Path
import json
import tempfile

from code.src.models.data_models import ABTestSummary, AuditRecord
from code.src.audit.validator import (
    run_validator,
    validate_p_value_consistency,
    validate_effect_size_consistency,
    validate_sample_sizes,
    create_audit_record,
    get_prevalence_records,
    write_audit_report,
    P_DIFF_THRESHOLD,
    EFFECT_SIZE_REL_THRESHOLD
)


class TestPValueValidation:
    """Tests for p-value consistency validation."""

    def test_p_value_within_threshold(self):
        """Test when p-value difference is within threshold."""
        reported = 0.03
        reconstructed = 0.05
        is_consistent, diff = validate_p_value_consistency(reported, reconstructed)
        assert is_consistent is True
        assert abs(diff - 0.02) < 1e-6

    def test_p_value_exceeds_threshold(self):
        """Test when p-value difference exceeds threshold."""
        reported = 0.01
        reconstructed = 0.07
        is_consistent, diff = validate_p_value_consistency(reported, reconstructed)
        assert is_consistent is False
        assert diff > P_DIFF_THRESHOLD

    def test_p_value_exact_threshold(self):
        """Test when p-value difference is exactly at threshold."""
        reported = 0.01
        reconstructed = 0.06  # difference = 0.05
        is_consistent, diff = validate_p_value_consistency(reported, reconstructed)
        assert is_consistent is True
        assert abs(diff - 0.05) < 1e-6


class TestEffectSizeValidation:
    """Tests for effect-size consistency validation."""

    def test_effect_size_within_threshold(self):
        """Test when effect size difference is within threshold."""
        reported = 0.10
        reconstructed = 0.104  # 4% relative difference
        is_consistent, diff = validate_effect_size_consistency(reported, reconstructed)
        assert is_consistent is True
        assert diff <= EFFECT_SIZE_REL_THRESHOLD

    def test_effect_size_exceeds_threshold(self):
        """Test when effect size difference exceeds threshold."""
        reported = 0.10
        reconstructed = 0.11  # 10% relative difference
        is_consistent, diff = validate_effect_size_consistency(reported, reconstructed)
        assert is_consistent is False
        assert diff > EFFECT_SIZE_REL_THRESHOLD

    def test_effect_size_exact_threshold(self):
        """Test when effect size difference is exactly at threshold."""
        reported = 0.10
        reconstructed = 0.105  # 5% relative difference
        is_consistent, diff = validate_effect_size_consistency(reported, reconstructed)
        assert is_consistent is True
        assert abs(diff - 0.05) < 1e-6

    def test_effect_size_zero_reported(self):
        """Test handling of zero reported effect size."""
        reported = 0.0
        reconstructed = 0.01
        is_consistent, diff = validate_effect_size_consistency(reported, reconstructed)
        # When reported is 0, any non-zero reconstructed is infinite relative diff
        assert is_consistent is False


class TestSampleSizeValidation:
    """Tests for sample-size mismatch validation."""

    def test_valid_sample_sizes(self):
        """Test with valid sample sizes."""
        summary = ABTestSummary(
            url="http://example.com",
            domain="example.com",
            n_control=1000,
            n_treatment=1000,
            p_value_reported=0.03,
            effect_size_reported=0.05,
            outcome_type="binary"
        )
        is_valid, warning = validate_sample_sizes(summary)
        assert is_valid is True
        assert warning is None

    def test_missing_sample_sizes(self):
        """Test with missing sample sizes."""
        summary = ABTestSummary(
            url="http://example.com",
            domain="example.com",
            n_control=None,
            n_treatment=1000,
            p_value_reported=0.03,
            effect_size_reported=0.05,
            outcome_type="binary"
        )
        is_valid, warning = validate_sample_sizes(summary)
        assert is_valid is False
        assert "Missing sample size" in warning

    def test_invalid_sample_sizes(self):
        """Test with invalid (zero/negative) sample sizes."""
        summary = ABTestSummary(
            url="http://example.com",
            domain="example.com",
            n_control=0,
            n_treatment=1000,
            p_value_reported=0.03,
            effect_size_reported=0.05,
            outcome_type="binary"
        )
        is_valid, warning = validate_sample_sizes(summary)
        assert is_valid is False
        assert "Invalid sample sizes" in warning

    def test_extreme_imbalance(self):
        """Test with extreme sample size imbalance."""
        summary = ABTestSummary(
            url="http://example.com",
            domain="example.com",
            n_control=10,
            n_treatment=10000,
            p_value_reported=0.03,
            effect_size_reported=0.05,
            outcome_type="binary"
        )
        is_valid, warning = validate_sample_sizes(summary)
        assert is_valid is False
        assert "Extreme sample size imbalance" in warning


class TestAuditRecordCreation:
    """Tests for AuditRecord creation."""

    def test_consistent_record(self):
        """Test creation of a consistent record."""
        summary = ABTestSummary(
            url="http://example.com",
            domain="example.com",
            n_control=1000,
            n_treatment=1000,
            p_value_reported=0.03,
            effect_size_reported=0.05,
            outcome_type="binary"
        )
        record = create_audit_record(
            summary=summary,
            is_consistent=True,
            p_diff=0.01,
            effect_diff=0.02,
            sample_size_warning=None,
            reconstructed_p=0.04,
            reconstructed_effect=0.051
        )
        assert record.status == "consistent"
        assert record.error_code is None
        assert "passed" in record.notes

    def test_inconsistent_p_value_record(self):
        """Test creation of an inconsistent record due to p-value."""
        summary = ABTestSummary(
            url="http://example.com",
            domain="example.com",
            n_control=1000,
            n_treatment=1000,
            p_value_reported=0.01,
            effect_size_reported=0.05,
            outcome_type="binary"
        )
        record = create_audit_record(
            summary=summary,
            is_consistent=False,
            p_diff=0.07,  # Exceeds threshold
            effect_diff=0.02,
            sample_size_warning=None,
            reconstructed_p=0.08,
            reconstructed_effect=0.051
        )
        assert record.status == "inconsistent"
        assert record.error_code is not None
        assert "P-value discrepancy" in record.notes

    def test_data_quality_warning_record(self):
        """Test creation of a data quality warning record."""
        summary = ABTestSummary(
            url="http://example.com",
            domain="example.com",
            n_control=None,
            n_treatment=1000,
            p_value_reported=0.03,
            effect_size_reported=0.05,
            outcome_type="binary"
        )
        record = create_audit_record(
            summary=summary,
            is_consistent=False,
            sample_size_warning="Missing sample size data"
        )
        assert record.status == "data_quality_warning"
        assert record.error_code is not None
        assert "Sample size issue" in record.notes


class TestPrevalenceExclusion:
    """Tests for FR-004b: exclusion of sample-size mismatch entries."""

    def test_exclude_data_quality_warnings(self):
        """Test that data_quality_warning records are excluded from prevalence."""
        records = [
            AuditRecord(
                url="http://example1.com",
                domain="example.com",
                reported_p_value=0.03,
                reconstructed_p_value=0.04,
                reported_effect_size=0.05,
                reconstructed_effect_size=0.051,
                status="consistent",
                notes="All checks passed",
                error_code=None,
                timestamp="2024-01-01T00:00:00"
            ),
            AuditRecord(
                url="http://example2.com",
                domain="example.com",
                reported_p_value=0.01,
                reconstructed_p_value=0.08,
                reported_effect_size=0.05,
                reconstructed_effect_size=0.051,
                status="inconsistent",
                notes="P-value discrepancy",
                error_code="ERR-004",
                timestamp="2024-01-01T00:00:00"
            ),
            AuditRecord(
                url="http://example3.com",
                domain="example.com",
                reported_p_value=0.03,
                reconstructed_p_value=None,
                reported_effect_size=0.05,
                reconstructed_effect_size=None,
                status="data_quality_warning",
                notes="Sample size issue",
                error_code="ERR-006",
                timestamp="2024-01-01T00:00:00"
            )
        ]

        prevalence_records = get_prevalence_records(records)

        assert len(prevalence_records) == 2
        assert all(r.status != "data_quality_warning" for r in prevalence_records)

    def test_all_consistent(self):
        """Test when all records are consistent."""
        records = [
            AuditRecord(
                url="http://example1.com",
                domain="example.com",
                reported_p_value=0.03,
                reconstructed_p_value=0.04,
                reported_effect_size=0.05,
                reconstructed_effect_size=0.051,
                status="consistent",
                notes="All checks passed",
                error_code=None,
                timestamp="2024-01-01T00:00:00"
            ),
            AuditRecord(
                url="http://example2.com",
                domain="example.com",
                reported_p_value=0.03,
                reconstructed_p_value=0.04,
                reported_effect_size=0.05,
                reconstructed_effect_size=0.051,
                status="consistent",
                notes="All checks passed",
                error_code=None,
                timestamp="2024-01-01T00:00:00"
            )
        ]

        prevalence_records = get_prevalence_records(records)
        assert len(prevalence_records) == 2

    def test_all_warnings(self):
        """Test when all records have data quality warnings."""
        records = [
            AuditRecord(
                url="http://example1.com",
                domain="example.com",
                reported_p_value=0.03,
                reconstructed_p_value=None,
                reported_effect_size=0.05,
                reconstructed_effect_size=None,
                status="data_quality_warning",
                notes="Sample size issue",
                error_code="ERR-006",
                timestamp="2024-01-01T00:00:00"
            ),
            AuditRecord(
                url="http://example2.com",
                domain="example.com",
                reported_p_value=0.03,
                reconstructed_p_value=None,
                reported_effect_size=0.05,
                reconstructed_effect_size=None,
                status="data_quality_warning",
                notes="Sample size issue",
                error_code="ERR-006",
                timestamp="2024-01-01T00:00:00"
            )
        ]

        prevalence_records = get_prevalence_records(records)
        assert len(prevalence_records) == 0


class TestEndToEndValidation:
    """End-to-end tests for the validator."""

    def test_run_validator_mixed_results(self):
        """Test run_validator with a mix of consistent, inconsistent, and warning records."""
        summaries = [
            ABTestSummary(
                url="http://example1.com",
                domain="example.com",
                n_control=1000,
                n_treatment=1000,
                p_value_reported=0.03,
                effect_size_reported=0.05,
                outcome_type="binary"
            ),
            ABTestSummary(
                url="http://example2.com",
                domain="example.com",
                n_control=1000,
                n_treatment=1000,
                p_value_reported=0.01,
                effect_size_reported=0.05,
                outcome_type="binary"
            ),
            ABTestSummary(
                url="http://example3.com",
                domain="example.com",
                n_control=None,
                n_treatment=1000,
                p_value_reported=0.03,
                effect_size_reported=0.05,
                outcome_type="binary"
            )
        ]

        reconstructed_results = [
            {
                'index': 0,
                'reconstructed_p': 0.04,
                'reconstructed_effect': 0.051,
                'is_valid': True
            },
            {
                'index': 1,
                'reconstructed_p': 0.08,  # High discrepancy
                'reconstructed_effect': 0.051,
                'is_valid': True
            },
            {
                'index': 2,
                'is_valid': False,
                'error_message': 'Missing sample size'
            }
        ]

        records = run_validator(summaries, reconstructed_results)

        assert len(records) == 3

        # First should be consistent
        assert records[0].status == "consistent"

        # Second should be inconsistent (p-value discrepancy)
        assert records[1].status == "inconsistent"
        assert "P-value discrepancy" in records[1].notes

        # Third should be data_quality_warning
        assert records[2].status == "data_quality_warning"
        assert "Sample size issue" in records[2].notes

    def test_write_audit_report(self):
        """Test writing audit report to JSON file."""
        records = [
            AuditRecord(
                url="http://example1.com",
                domain="example.com",
                reported_p_value=0.03,
                reconstructed_p_value=0.04,
                reported_effect_size=0.05,
                reconstructed_effect_size=0.051,
                status="consistent",
                notes="All checks passed",
                error_code=None,
                timestamp="2024-01-01T00:00:00"
            ),
            AuditRecord(
                url="http://example2.com",
                domain="example.com",
                reported_p_value=0.01,
                reconstructed_p_value=0.08,
                reported_effect_size=0.05,
                reconstructed_effect_size=0.051,
                status="inconsistent",
                notes="P-value discrepancy",
                error_code="ERR-004",
                timestamp="2024-01-01T00:00:00"
            )
        ]

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "audit_report.json"
            write_audit_report(records, output_path)

            assert output_path.exists()

            with open(output_path, 'r') as f:
                data = json.load(f)

            assert data['total_records'] == 2
            assert data['consistent_count'] == 1
            assert data['inconsistent_count'] == 1
            assert len(data['records']) == 2