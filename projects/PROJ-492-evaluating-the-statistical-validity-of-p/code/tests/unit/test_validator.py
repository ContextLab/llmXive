"""
Unit tests for the Inconsistency Validator (T025)

Tests:
- Absolute p-difference > 0.05 threshold
- Relative effect-size > 5% threshold
- Sample-size mismatch detection and exclusion
- Data quality warning generation
"""

import json
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

import numpy as np

from code.src.models.data_models import ABTestSummary, AuditRecord
from code.src.audit.validator import (
    calculate_absolute_p_difference,
    calculate_relative_effect_size_difference,
    detect_sample_size_mismatch,
    check_p_value_consistency,
    check_effect_size_consistency,
    validate_summary,
    validate_all_summaries,
    filter_for_prevalence,
    write_audit_report,
    P_VALUE_THRESHOLD,
    EFFECT_SIZE_RELATIVE_THRESHOLD
)


class TestPValueDifference:
    """Tests for p-value difference calculation"""

    def test_absolute_p_difference_normal(self):
        """Test normal p-value difference calculation"""
        diff = calculate_absolute_p_difference(0.04, 0.10)
        assert diff == 0.06

    def test_absolute_p_difference_identical(self):
        """Test when p-values are identical"""
        diff = calculate_absolute_p_difference(0.05, 0.05)
        assert diff == 0.0

    def test_absolute_p_difference_none_values(self):
        """Test when one or both values are None"""
        assert np.isnan(calculate_absolute_p_difference(None, 0.05))
        assert np.isnan(calculate_absolute_p_difference(0.05, None))
        assert np.isnan(calculate_absolute_p_difference(None, None))


class TestEffectSizeDifference:
    """Tests for effect size relative difference calculation"""

    def test_relative_effect_size_normal(self):
        """Test normal relative effect size difference"""
        # Reported 0.10, Reconstructed 0.095 -> diff = 0.005 / 0.095 ≈ 0.0526 (5.26%)
        diff = calculate_relative_effect_size_difference(0.10, 0.095)
        assert abs(diff - 0.0526) < 0.0001

    def test_relative_effect_size_consistent(self):
        """Test when effect sizes are within 5% threshold"""
        # 4.9% difference
        diff = calculate_relative_effect_size_difference(0.10, 0.0951)
        assert diff < 0.05

    def test_relative_effect_size_zero_reconstructed(self):
        """Test when reconstructed effect is zero"""
        assert np.isinf(calculate_relative_effect_size_difference(0.01, 0.0))
        assert calculate_relative_effect_size_difference(0.0, 0.0) == 0.0

    def test_relative_effect_size_none_values(self):
        """Test when one or both values are None"""
        assert np.isnan(calculate_relative_effect_size_difference(None, 0.05))
        assert np.isnan(calculate_relative_effect_size_difference(0.05, None))


class TestSampleSizeMismatch:
    """Tests for sample size mismatch detection (FR-004b)"""

    def test_no_mismatch(self):
        """Test when sample sizes match conversions and rates"""
        summary = ABTestSummary(
            url="http://example.com",
            domain="example.com",
            n_control=1000,
            n_treatment=1000,
            conversions_control=100,
            conversion_rate_control=0.10,
            conversions_treatment=120,
            conversion_rate_treatment=0.12
        )
        is_mismatch, msg = detect_sample_size_mismatch(summary)
        assert not is_mismatch
        assert msg is None

    def test_mismatch_control(self):
        """Test when control sample size mismatches"""
        summary = ABTestSummary(
            url="http://example.com",
            domain="example.com",
            n_control=1000,  # Reported 1000
            n_treatment=1000,
            conversions_control=100,
            conversion_rate_control=0.10,  # Implies 1000, but let's force mismatch
            conversions_treatment=120,
            conversion_rate_treatment=0.12
        )
        # Manually create a mismatch scenario: reported 1000, implied 900
        summary.n_control = 1000
        summary.conversions_control = 90
        summary.conversion_rate_control = 0.10  # Implies 900
        is_mismatch, msg = detect_sample_size_mismatch(summary)
        assert is_mismatch
        assert "Sample size mismatch" in msg
        assert "n_control" in msg

    def test_mismatch_treatment(self):
        """Test when treatment sample size mismatches"""
        summary = ABTestSummary(
            url="http://example.com",
            domain="example.com",
            n_control=1000,
            n_treatment=1000,
            conversions_control=100,
            conversion_rate_control=0.10,
            conversions_treatment=120,
            conversion_rate_treatment=0.12
        )
        summary.n_treatment = 1000
        summary.conversions_treatment = 110
        summary.conversion_rate_treatment = 0.10  # Implies 1100
        is_mismatch, msg = detect_sample_size_mismatch(summary)
        assert is_mismatch
        assert "n_treatment" in msg

    def test_missing_sample_sizes(self):
        """Test when sample sizes are missing"""
        summary = ABTestSummary(
            url="http://example.com",
            domain="example.com",
            n_control=None,
            n_treatment=None,
            conversions_control=100,
            conversion_rate_control=0.10
        )
        is_mismatch, msg = detect_sample_size_mismatch(summary)
        assert not is_mismatch
        assert msg is None


class TestValidationThresholds:
    """Tests for FR-004 threshold application"""

    def test_p_value_consistent(self):
        """Test p-value within threshold (0.05)"""
        summary = ABTestSummary(
            url="http://example.com",
            domain="example.com",
            reported_p_value=0.04,
            reconstructed_p_value=0.06,  # Diff = 0.02
            reported_effect_size=0.10,
            reconstructed_effect_size=0.10,
            n_control=1000,
            n_treatment=1000
        )
        is_consistent, diff, msg = check_p_value_consistency(summary)
        assert is_consistent
        assert diff == 0.02
        assert msg is None

    def test_p_value_inconsistent(self):
        """Test p-value outside threshold (> 0.05)"""
        summary = ABTestSummary(
            url="http://example.com",
            domain="example.com",
            reported_p_value=0.01,
            reconstructed_p_value=0.10,  # Diff = 0.09
            reported_effect_size=0.10,
            reconstructed_effect_size=0.10,
            n_control=1000,
            n_treatment=1000
        )
        is_consistent, diff, msg = check_p_value_consistency(summary)
        assert not is_consistent
        assert diff == 0.09
        assert "P-value inconsistency" in msg

    def test_effect_size_consistent(self):
        """Test effect size within 5% threshold"""
        summary = ABTestSummary(
            url="http://example.com",
            domain="example.com",
            reported_p_value=0.04,
            reconstructed_p_value=0.04,
            reported_effect_size=0.10,
            reconstructed_effect_size=0.096,  # ~4% diff
            n_control=1000,
            n_treatment=1000
        )
        is_consistent, diff, msg = check_effect_size_consistency(summary)
        assert is_consistent
        assert diff < 0.05
        assert msg is None

    def test_effect_size_inconsistent(self):
        """Test effect size outside 5% threshold"""
        summary = ABTestSummary(
            url="http://example.com",
            domain="example.com",
            reported_p_value=0.04,
            reconstructed_p_value=0.04,
            reported_effect_size=0.10,
            reconstructed_effect_size=0.08,  # 25% diff
            n_control=1000,
            n_treatment=1000
        )
        is_consistent, diff, msg = check_effect_size_consistency(summary)
        assert not is_consistent
        assert diff > 0.05
        assert "Effect size inconsistency" in msg


class TestAuditRecordGeneration:
    """Tests for AuditRecord creation and data_quality_warning"""

    def test_audit_record_consistent(self):
        """Test AuditRecord for consistent summary"""
        summary = ABTestSummary(
            url="http://example.com",
            domain="example.com",
            reported_p_value=0.04,
            reconstructed_p_value=0.05,
            reported_effect_size=0.10,
            reconstructed_effect_size=0.10,
            n_control=1000,
            n_treatment=1000
        )
        record = validate_summary(summary)
        assert not record.is_inconsistent
        assert record.data_quality_warning is None

    def test_audit_record_inconsistent(self):
        """Test AuditRecord for inconsistent summary"""
        summary = ABTestSummary(
            url="http://example.com",
            domain="example.com",
            reported_p_value=0.01,
            reconstructed_p_value=0.10,
            reported_effect_size=0.10,
            reconstructed_effect_size=0.10,
            n_control=1000,
            n_treatment=1000
        )
        record = validate_summary(summary)
        assert record.is_inconsistent
        assert "P-value discrepancy" in record.data_quality_warning

    def test_audit_record_sample_mismatch_warning(self):
        """Test AuditRecord with sample-size mismatch (FR-004b)"""
        summary = ABTestSummary(
            url="http://example.com",
            domain="example.com",
            reported_p_value=0.04,
            reconstructed_p_value=0.05,
            reported_effect_size=0.10,
            reconstructed_effect_size=0.10,
            n_control=1000,
            n_treatment=1000,
            conversions_control=90,
            conversion_rate_control=0.10  # Implies 900, not 1000
        )
        record = validate_summary(summary)
        assert "Data quality warning" in str(record.data_quality_warning)
        assert record.validation_details["sample_size_mismatch"] is True


class TestPrevalenceExclusion:
    """Tests for FR-004b: Exclude sample-size mismatches from prevalence"""

    def test_filter_for_prevalence(self):
        """Test that sample-mismatch records are excluded"""
        records = [
            AuditRecord(
                url="http://example.com/1",
                domain="example.com",
                reported_p_value=0.04,
                reconstructed_p_value=0.05,
                reported_effect_size=0.10,
                reconstructed_effect_size=0.10,
                n_control=1000,
                n_treatment=1000,
                is_inconsistent=False,
                data_quality_warning=None,
                validation_details={"sample_size_mismatch": False}
            ),
            AuditRecord(
                url="http://example.com/2",
                domain="example.com",
                reported_p_value=0.04,
                reconstructed_p_value=0.05,
                reported_effect_size=0.10,
                reconstructed_effect_size=0.10,
                n_control=1000,
                n_treatment=1000,
                is_inconsistent=False,
                data_quality_warning=["Data quality warning: Mismatch"],
                validation_details={"sample_size_mismatch": True}
            ),
            AuditRecord(
                url="http://example.com/3",
                domain="example.com",
                reported_p_value=0.01,
                reconstructed_p_value=0.10,
                reported_effect_size=0.10,
                reconstructed_effect_size=0.10,
                n_control=1000,
                n_treatment=1000,
                is_inconsistent=True,
                data_quality_warning=["P-value discrepancy"],
                validation_details={"sample_size_mismatch": False}
            )
        ]

        filtered = filter_for_prevalence(records)
        assert len(filtered) == 2
        assert filtered[0].url == "http://example.com/1"
        assert filtered[1].url == "http://example.com/3"
        # The record with sample_size_mismatch should be excluded

    def test_filter_all_excluded(self):
        """Test when all records have sample mismatches"""
        records = [
            AuditRecord(
                url="http://example.com/1",
                domain="example.com",
                reported_p_value=0.04,
                reconstructed_p_value=0.05,
                reported_effect_size=0.10,
                reconstructed_effect_size=0.10,
                n_control=1000,
                n_treatment=1000,
                is_inconsistent=False,
                data_quality_warning=["Warning"],
                validation_details={"sample_size_mismatch": True}
            )
        ]
        filtered = filter_for_prevalence(records)
        assert len(filtered) == 0


class TestWriteAuditReport:
    """Tests for writing audit report to JSON"""

    def test_write_audit_report(self, tmp_path):
        """Test that audit report is written correctly"""
        records = [
            AuditRecord(
                url="http://example.com/1",
                domain="example.com",
                reported_p_value=0.04,
                reconstructed_p_value=0.05,
                reported_effect_size=0.10,
                reconstructed_effect_size=0.10,
                n_control=1000,
                n_treatment=1000,
                is_inconsistent=False,
                data_quality_warning=None,
                validation_details={"sample_size_mismatch": False}
            ),
            AuditRecord(
                url="http://example.com/2",
                domain="example.com",
                reported_p_value=0.01,
                reconstructed_p_value=0.10,
                reported_effect_size=0.10,
                reconstructed_effect_size=0.10,
                n_control=1000,
                n_treatment=1000,
                is_inconsistent=True,
                data_quality_warning=["P-value discrepancy"],
                validation_details={"sample_size_mismatch": False}
            )
        ]

        output_path = tmp_path / "audit_report.json"
        write_audit_report(records, output_path)

        assert output_path.exists()
        with open(output_path, 'r') as f:
            data = json.load(f)

        assert data["summary"]["total_records"] == 2
        assert data["summary"]["inconsistent_count"] == 1
        assert len(data["records"]) == 2
        assert data["records"][0]["is_inconsistent"] is False
        assert data["records"][1]["is_inconsistent"] is True

    def test_write_audit_report_with_sample_mismatch(self, tmp_path):
        """Test that sample mismatch counts are tracked"""
        records = [
            AuditRecord(
                url="http://example.com/1",
                domain="example.com",
                reported_p_value=0.04,
                reconstructed_p_value=0.05,
                reported_effect_size=0.10,
                reconstructed_effect_size=0.10,
                n_control=1000,
                n_treatment=1000,
                is_inconsistent=False,
                data_quality_warning=["Data quality warning"],
                validation_details={"sample_size_mismatch": True}
            )
        ]

        output_path = tmp_path / "audit_report.json"
        write_audit_report(records, output_path)

        with open(output_path, 'r') as f:
            data = json.load(f)

        assert data["summary"]["sample_mismatch_count"] == 1