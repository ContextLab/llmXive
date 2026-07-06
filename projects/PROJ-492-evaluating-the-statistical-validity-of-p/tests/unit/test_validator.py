"""
Unit tests for the validator module covering:
1. Absolute p-difference > 0.05 threshold
2. Relative effect-size difference > 5% threshold
3. Inequality p-value handling
4. Sample-size mismatch detection and data_quality_warning generation
"""

import pytest
import numpy as np
from unittest.mock import patch
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
    write_audit_report
)
from code.src.config import SEED
import json
from pathlib import Path


class TestAbsolutePDifference:
    """Tests for absolute p-value difference calculation and threshold."""

    def test_absolute_p_difference_below_threshold(self):
        """Test when p-value difference is 0.03 (below 0.05 threshold)."""
        p_reported = 0.042
        p_reconstructed = 0.072
        
        diff = calculate_absolute_p_difference(p_reported, p_reconstructed)
        
        assert abs(diff) == pytest.approx(0.03, rel=1e-6)
        assert diff < 0.05

    def test_absolute_p_difference_above_threshold(self):
        """Test when p-value difference is 0.06 (above 0.05 threshold)."""
        p_reported = 0.01
        p_reconstructed = 0.07
        
        diff = calculate_absolute_p_difference(p_reported, p_reconstructed)
        
        assert abs(diff) == pytest.approx(0.06, rel=1e-6)
        assert diff > 0.05

    def test_absolute_p_difference_exactly_threshold(self):
        """Test when p-value difference is exactly 0.05."""
        p_reported = 0.05
        p_reconstructed = 0.10
        
        diff = calculate_absolute_p_difference(p_reported, p_reconstructed)
        
        assert abs(diff) == pytest.approx(0.05, rel=1e-6)

    def test_absolute_p_difference_with_inequality(self):
        """Test handling of inequality p-values (e.g., p < 0.001)."""
        # When p is reported as inequality, we use the bound value
        p_reported = 0.001  # From "p < 0.001"
        p_reconstructed = 0.005
        
        diff = calculate_absolute_p_difference(p_reported, p_reconstructed)
        
        assert abs(diff) == pytest.approx(0.004, rel=1e-6)


class TestRelativeEffectSizeDifference:
    """Tests for relative effect-size difference calculation and threshold."""

    def test_effect_size_below_threshold(self):
        """Test when effect size difference is 3% (below 5% threshold)."""
        effect_reported = 0.10
        effect_reconstructed = 0.103
        
        rel_diff = calculate_relative_effect_size_difference(effect_reported, effect_reconstructed)
        
        assert rel_diff == pytest.approx(0.03, rel=1e-6)
        assert rel_diff < 0.05

    def test_effect_size_above_threshold(self):
        """Test when effect size difference is 8% (above 5% threshold)."""
        effect_reported = 0.20
        effect_reconstructed = 0.216
        
        rel_diff = calculate_relative_effect_size_difference(effect_reported, effect_reconstructed)
        
        assert rel_diff == pytest.approx(0.08, rel=1e-6)
        assert rel_diff > 0.05

    def test_effect_size_exactly_threshold(self):
        """Test when effect size difference is exactly 5%."""
        effect_reported = 0.10
        effect_reconstructed = 0.105
        
        rel_diff = calculate_relative_effect_size_difference(effect_reported, effect_reconstructed)
        
        assert rel_diff == pytest.approx(0.05, rel=1e-6)

    def test_effect_size_zero_baseline(self):
        """Test handling when reported effect is zero (edge case)."""
        effect_reported = 0.0
        effect_reconstructed = 0.01
        
        # Should return 100% or a defined maximum when baseline is 0
        rel_diff = calculate_relative_effect_size_difference(effect_reported, effect_reconstructed)
        
        # When baseline is 0, relative difference is undefined/infinite
        # The function should handle this gracefully, typically returning a large value or 1.0
        assert rel_diff >= 0.0  # Should not crash


class TestInequalityHandling:
    """Tests for handling inequality p-values in validation."""

    def test_inequality_p_less_than(self):
        """Test parsing of 'p < 0.01' format."""
        # The validator should interpret 'p < 0.01' as p = 0.01 for comparison
        p_reported = 0.01  # Parsed from "p < 0.01"
        p_reconstructed = 0.015
        
        diff = calculate_absolute_p_difference(p_reported, p_reconstructed)
        
        # 0.01 vs 0.015 -> 0.005 difference (below threshold)
        assert diff < 0.05

    def test_inequality_p_greater_than(self):
        """Test parsing of 'p > 0.1' format."""
        p_reported = 0.1  # Parsed from "p > 0.1"
        p_reconstructed = 0.12
        
        diff = calculate_absolute_p_difference(p_reported, p_reconstructed)
        
        # 0.1 vs 0.12 -> 0.02 difference (below threshold)
        assert diff < 0.05

    def test_inequality_consistency_check(self):
        """Test that inequality p-values are handled in consistency check."""
        # When reported is an inequality bound, we check if reconstructed is consistent
        # with being on the same side of the threshold
        p_reported = 0.05  # From "p < 0.05"
        p_reconstructed = 0.04  # Reconstructed value is less than 0.05
        
        is_consistent = check_p_value_consistency(p_reported, p_reconstructed, threshold=0.05)
        
        # Both are < 0.05, so consistent
        assert is_consistent is True


class TestSampleSizeMismatch:
    """Tests for sample size mismatch detection and warning generation."""

    def test_no_sample_size_mismatch(self):
        """Test when sample sizes match exactly."""
        summary = ABTestSummary(
            url="https://example.com/test",
            domain="example.com",
            baseline_n=1000,
            treatment_n=1000,
            baseline_rate=0.10,
            treatment_rate=0.12,
            reported_p_value=0.04,
            effect_size=0.02,
            outcome_type="binary"
        )
        
        mismatch = detect_sample_size_mismatch(summary)
        
        assert mismatch is False

    def test_sample_size_mismatch_detected(self):
        """Test when sample sizes differ significantly."""
        summary = ABTestSummary(
            url="https://example.com/test",
            domain="example.com",
            baseline_n=1000,
            treatment_n=1500,  # 50% difference
            baseline_rate=0.10,
            treatment_rate=0.12,
            reported_p_value=0.04,
            effect_size=0.02,
            outcome_type="binary"
        )
        
        mismatch = detect_sample_size_mismatch(summary)
        
        assert mismatch is True

    def test_sample_size_mismatch_small_difference(self):
        """Test when sample sizes differ slightly (within tolerance)."""
        summary = ABTestSummary(
            url="https://example.com/test",
            domain="example.com",
            baseline_n=1000,
            treatment_n=1010,  # 1% difference
            baseline_rate=0.10,
            treatment_rate=0.12,
            reported_p_value=0.04,
            effect_size=0.02,
            outcome_type="binary"
        )
        
        mismatch = detect_sample_size_mismatch(summary)
        
        # Should be False if within tolerance (e.g., 5%)
        assert mismatch is False


class TestDataQualityWarningGeneration:
    """Tests for data_quality_warning generation on sample-size mismatch."""

    def test_warning_generated_on_mismatch(self):
        """Test that data_quality_warning is generated when sample sizes mismatch."""
        summary = ABTestSummary(
            url="https://example.com/test",
            domain="example.com",
            baseline_n=1000,
            treatment_n=2000,  # Large mismatch
            baseline_rate=0.10,
            treatment_rate=0.12,
            reported_p_value=0.04,
            effect_size=0.02,
            outcome_type="binary"
        )
        
        audit_record = create_audit_record(summary, is_consistent=True)
        
        # Check that data_quality_warning is present
        assert audit_record.data_quality_warning is not None
        assert "sample_size_mismatch" in audit_record.data_quality_warning.lower()

    def test_no_warning_on_match(self):
        """Test that no warning is generated when sample sizes match."""
        summary = ABTestSummary(
            url="https://example.com/test",
            domain="example.com",
            baseline_n=1000,
            treatment_n=1000,
            baseline_rate=0.10,
            treatment_rate=0.12,
            reported_p_value=0.04,
            effect_size=0.02,
            outcome_type="binary"
        )
        
        audit_record = create_audit_record(summary, is_consistent=True)
        
        # Check that data_quality_warning is None or empty
        assert audit_record.data_quality_warning is None or audit_record.data_quality_warning == ""


class TestValidateSummary:
    """Tests for the main validate_summary function."""

    def test_valid_summary_no_issues(self):
        """Test validation of a consistent summary with no issues."""
        summary = ABTestSummary(
            url="https://example.com/test",
            domain="example.com",
            baseline_n=1000,
            treatment_n=1000,
            baseline_rate=0.10,
            treatment_rate=0.11,
            reported_p_value=0.04,
            effect_size=0.01,
            outcome_type="binary"
        )
        
        audit_record = validate_summary(summary)
        
        assert audit_record.is_consistent is True
        assert audit_record.data_quality_warning is None

    def test_inconsistent_summary_p_value(self):
        """Test validation when p-value difference exceeds threshold."""
        summary = ABTestSummary(
            url="https://example.com/test",
            domain="example.com",
            baseline_n=1000,
            treatment_n=1000,
            baseline_rate=0.10,
            treatment_rate=0.15,
            reported_p_value=0.01,  # Very low reported
            effect_size=0.05,
            outcome_type="binary"
        )
        
        # The reconstructor would produce a different p-value for these stats
        # We mock the reconstructed value to simulate inconsistency
        with patch('code.src.audit.validator.reconstruct_single_summary') as mock_reconstruct:
            mock_reconstruct.return_value = {
                'reconstructed_p_value': 0.25,  # Much higher
                'reconstructed_effect_size': 0.05
            }
            
            audit_record = validate_summary(summary)
            
            assert audit_record.is_consistent is False
            assert 'p_value_inconsistency' in audit_record.notes.lower()

    def test_inconsistent_summary_effect_size(self):
        """Test validation when effect size difference exceeds threshold."""
        summary = ABTestSummary(
            url="https://example.com/test",
            domain="example.com",
            baseline_n=1000,
            treatment_n=1000,
            baseline_rate=0.10,
            treatment_rate=0.15,
            reported_p_value=0.04,
            effect_size=0.05,  # Reported effect
            outcome_type="binary"
        )
        
        with patch('code.src.audit.validator.reconstruct_single_summary') as mock_reconstruct:
            mock_reconstruct.return_value = {
                'reconstructed_p_value': 0.04,
                'reconstructed_effect_size': 0.10  # Different effect size
            }
            
            audit_record = validate_summary(summary)
            
            assert audit_record.is_consistent is False
            assert 'effect_size_inconsistency' in audit_record.notes.lower()


class TestValidateAllSummaries:
    """Tests for batch validation of multiple summaries."""

    def test_validate_all_empty_list(self):
        """Test validation with empty summary list."""
        summaries = []
        
        audit_records = validate_all_summaries(summaries)
        
        assert audit_records == []

    def test_validate_all_mixed_results(self):
        """Test validation with mix of consistent and inconsistent summaries."""
        summaries = [
            ABTestSummary(
                url="https://example.com/test1",
                domain="example.com",
                baseline_n=1000,
                treatment_n=1000,
                baseline_rate=0.10,
                treatment_rate=0.11,
                reported_p_value=0.04,
                effect_size=0.01,
                outcome_type="binary"
            ),
            ABTestSummary(
                url="https://example.com/test2",
                domain="example.com",
                baseline_n=1000,
                treatment_n=1000,
                baseline_rate=0.10,
                treatment_rate=0.20,
                reported_p_value=0.01,
                effect_size=0.10,
                outcome_type="binary"
            )
        ]
        
        # Mock reconstruction to make first consistent, second inconsistent
        def mock_reconstruct(summary):
            if "test1" in summary.url:
                return {'reconstructed_p_value': 0.04, 'reconstructed_effect_size': 0.01}
            else:
                return {'reconstructed_p_value': 0.25, 'reconstructed_effect_size': 0.10}
        
        with patch('code.src.audit.validator.reconstruct_single_summary', side_effect=mock_reconstruct):
            audit_records = validate_all_summaries(summaries)
            
            assert len(audit_records) == 2
            assert audit_records[0].is_consistent is True
            assert audit_records[1].is_consistent is False


class TestFilterForPrevalence:
    """Tests for filtering records for prevalence calculation."""

    def test_filter_excludes_sample_size_mismatch(self):
        """Test that records with sample-size mismatch are excluded."""
        records = [
            AuditRecord(
                url="https://example.com/test1",
                domain="example.com",
                is_consistent=True,
                notes="",
                data_quality_warning=None
            ),
            AuditRecord(
                url="https://example.com/test2",
                domain="example.com",
                is_consistent=True,
                notes="",
                data_quality_warning="sample_size_mismatch"
            ),
            AuditRecord(
                url="https://example.com/test3",
                domain="example.com",
                is_consistent=False,
                notes="p_value_inconsistency",
                data_quality_warning=None
            )
        ]
        
        filtered = filter_for_prevalence(records)
        
        # Should exclude test2 (mismatch) but include test1 and test3
        assert len(filtered) == 2
        urls = [r.url for r in filtered]
        assert "https://example.com/test2" not in urls
        assert "https://example.com/test1" in urls
        assert "https://example.com/test3" in urls

    def test_filter_all_valid(self):
        """Test filtering when no records have mismatches."""
        records = [
            AuditRecord(
                url="https://example.com/test1",
                domain="example.com",
                is_consistent=True,
                notes="",
                data_quality_warning=None
            ),
            AuditRecord(
                url="https://example.com/test2",
                domain="example.com",
                is_consistent=False,
                notes="p_value_inconsistency",
                data_quality_warning=None
            )
        ]
        
        filtered = filter_for_prevalence(records)
        
        # Should include both
        assert len(filtered) == 2


class TestWriteAuditReport:
    """Tests for writing audit report to file."""

    def test_write_audit_report_creates_file(self, tmp_path):
        """Test that write_audit_report creates the expected file."""
        records = [
            AuditRecord(
                url="https://example.com/test1",
                domain="example.com",
                is_consistent=True,
                notes="",
                data_quality_warning=None
            )
        ]
        
        output_path = tmp_path / "audit_report.json"
        
        write_audit_report(records, output_path)
        
        assert output_path.exists()
        
        with open(output_path, 'r') as f:
            data = json.load(f)
        
        assert len(data) == 1
        assert data[0]['url'] == "https://example.com/test1"
        assert data[0]['is_consistent'] is True