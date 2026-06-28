"""
Unit tests for data models (ABTestSummary, AuditRecord).

Verifies:
- Pydantic model instantiation
- Field validation
- Model validators
- Importability
"""

import pytest
from datetime import datetime
from code.src.models.data_models import ABTestSummary, AuditRecord


class TestABTestSummary:
    """Tests for ABTestSummary model."""

    def test_create_binary_summary(self):
        """Test creating a binary outcome summary."""
        summary = ABTestSummary(
            url="https://example.com/ab-test",
            n_control=1000,
            n_treatment=1000,
            baseline_rate=0.10,
            treatment_rate=0.12,
            reported_p_value=0.03
        )
        assert summary.outcome_type == "binary"
        assert summary.baseline_rate == 0.10
        assert summary.treatment_rate == 0.12

    def test_create_continuous_summary(self):
        """Test creating a continuous outcome summary."""
        summary = ABTestSummary(
            url="https://example.com/ab-test",
            n_control=500,
            n_treatment=500,
            control_mean=10.5,
            treatment_mean=11.2,
            control_std=2.0,
            treatment_std=2.1
        )
        assert summary.outcome_type == "continuous"

    def test_invalid_url_raises(self):
        """Test that invalid URL format raises validation error."""
        with pytest.raises(ValueError):
            ABTestSummary(
                url="not-a-valid-url",
                n_control=100,
                n_treatment=100
            )

    def test_negative_sample_size_raises(self):
        """Test that negative sample size raises validation error."""
        with pytest.raises(ValueError):
            ABTestSummary(
                url="https://example.com/ab-test",
                n_control=-100,
                n_treatment=100
            )

    def test_rate_out_of_range_raises(self):
        """Test that rate outside [0, 1] raises validation error."""
        with pytest.raises(ValueError):
            ABTestSummary(
                url="https://example.com/ab-test",
                n_control=100,
                n_treatment=100,
                baseline_rate=1.5
            )

    def test_missing_baseline_flag(self):
        """Test that missing baseline rate is flagged."""
        summary = ABTestSummary(
            url="https://example.com/ab-test",
            n_control=100,
            n_treatment=100,
            treatment_rate=0.12
        )
        assert summary.missing_baseline is True

    def test_publication_year_validation(self):
        """Test publication year range validation."""
        # Valid year
        summary = ABTestSummary(
            url="https://example.com/ab-test",
            n_control=100,
            n_treatment=100,
            publication_year=2023
        )
        assert summary.publication_year == 2023

        # Invalid year
        with pytest.raises(ValueError):
            ABTestSummary(
                url="https://example.com/ab-test",
                n_control=100,
                n_treatment=100,
                publication_year=1800
            )

    def test_serialization(self):
        """Test model serialization to dict and JSON."""
        summary = ABTestSummary(
            url="https://example.com/ab-test",
            n_control=100,
            n_treatment=100,
            baseline_rate=0.10,
            treatment_rate=0.12
        )
        summary_dict = summary.model_dump()
        assert "url" in summary_dict
        assert "n_control" in summary_dict

        summary_json = summary.model_dump_json()
        assert "example.com" in summary_json


class TestAuditRecord:
    """Tests for AuditRecord model."""

    def test_create_audit_record(self):
        """Test creating an audit record."""
        summary = ABTestSummary(
            url="https://example.com/ab-test",
            n_control=1000,
            n_treatment=1000,
            baseline_rate=0.10,
            treatment_rate=0.12,
            reported_p_value=0.03
        )
        record = AuditRecord(
            summary_url="https://example.com/ab-test",
            original_summary=summary,
            reconstructed_p_value=0.04,
            p_value_difference=0.01
        )
        assert record.summary_url == "https://example.com/ab-test"
        assert record.reconstructed_p_value == 0.04

    def test_inconsistency_detection(self):
        """Test inconsistency flag when p-value difference exceeds threshold."""
        summary = ABTestSummary(
            url="https://example.com/ab-test",
            n_control=1000,
            n_treatment=1000,
            baseline_rate=0.10,
            treatment_rate=0.12,
            reported_p_value=0.03
        )
        record = AuditRecord(
            summary_url="https://example.com/ab-test",
            original_summary=summary,
            reconstructed_p_value=0.10,
            p_value_difference=0.07
        )
        assert record.p_value_flag is True
        assert record.is_inconsistent is True

    def test_consistency_when_below_threshold(self):
        """Test that record is consistent when differences are below threshold."""
        summary = ABTestSummary(
            url="https://example.com/ab-test",
            n_control=1000,
            n_treatment=1000,
            baseline_rate=0.10,
            treatment_rate=0.12,
            reported_p_value=0.03
        )
        record = AuditRecord(
            summary_url="https://example.com/ab-test",
            original_summary=summary,
            reconstructed_p_value=0.05,
            p_value_difference=0.02
        )
        assert record.p_value_flag is False
        assert record.is_inconsistent is False

    def test_missing_baseline_warning(self):
        """Test that missing baseline triggers warning."""
        summary = ABTestSummary(
            url="https://example.com/ab-test",
            n_control=100,
            n_treatment=100,
            treatment_rate=0.12
        )
        record = AuditRecord(
            summary_url="https://example.com/ab-test",
            original_summary=summary
        )
        assert record.missing_baseline_warning is True
        assert any("ERR-012" in w for w in record.data_quality_warnings)

    def test_serialization(self):
        """Test audit record serialization."""
        summary = ABTestSummary(
            url="https://example.com/ab-test",
            n_control=100,
            n_treatment=100,
            baseline_rate=0.10,
            treatment_rate=0.12
        )
        record = AuditRecord(
            summary_url="https://example.com/ab-test",
            original_summary=summary
        )
        record_dict = record.model_dump()
        assert "summary_url" in record_dict
        assert "original_summary" in record_dict


class TestModelImportability:
    """Tests ensuring models are importable."""

    def test_import_from_package(self):
        """Test importing from package __init__."""
        from code.src.models import ABTestSummary, AuditRecord
        assert ABTestSummary is not None
        assert AuditRecord is not None

    def test_is_valid_functions(self):
        """Test helper validation functions."""
        from code.src.models.data_models import is_valid_ab_summary, is_valid_audit_record

        summary = ABTestSummary(
            url="https://example.com/ab-test",
            n_control=100,
            n_treatment=100
        )
        assert is_valid_ab_summary(summary) is True
        assert is_valid_ab_summary("not a summary") is False

        record = AuditRecord(
            summary_url="https://example.com/ab-test",
            original_summary=summary
        )
        assert is_valid_audit_record(record) is True
        assert is_valid_audit_record("not a record") is False
