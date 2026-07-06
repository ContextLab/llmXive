"""
Unit tests for the validator module (T027).

Tests cover:
- Absolute p-difference > 0.05 threshold
- Relative effect-size > 5% threshold
- Inequality handling
- Sample-size mismatch with data_quality_warning generation
"""
import pytest
from pathlib import Path
import json
from datetime import datetime
from unittest.mock import MagicMock, patch

import numpy as np

from code.src.models.data_models import ABTestSummary, AuditRecord, OutcomeType
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
    ABSOLUTE_P_DIFF_THRESHOLD,
    RELATIVE_EFFECT_SIZE_THRESHOLD
)


class TestCalculateAbsolutePDifference:
    """Tests for absolute p-value difference calculation."""
    
    def test_normal_difference(self):
        """Test calculation with normal values."""
        result = calculate_absolute_p_difference(0.03, 0.08)
        assert result == 0.05
    
    def test_zero_difference(self):
        """Test calculation when values are equal."""
        result = calculate_absolute_p_difference(0.05, 0.05)
        assert result == 0.0
    
    def test_none_values(self):
        """Test handling of None values."""
        result = calculate_absolute_p_difference(None, 0.05)
        assert result == float('inf')
        
        result = calculate_absolute_p_difference(0.05, None)
        assert result == float('inf')
        
        result = calculate_absolute_p_difference(None, None)
        assert result == float('inf')


class TestCalculateRelativeEffectSizeDifference:
    """Tests for relative effect-size difference calculation."""
    
    def test_normal_relative_difference(self):
        """Test calculation with normal values."""
        # (0.10 - 0.05) / 0.05 = 1.0 (100% difference)
        result = calculate_relative_effect_size_difference(0.10, 0.05)
        assert result == 1.0
    
    def test_within_threshold(self):
        """Test calculation when difference is within 5% threshold."""
        # (0.0525 - 0.05) / 0.05 = 0.05 (5% difference)
        result = calculate_relative_effect_size_difference(0.0525, 0.05)
        assert result == 0.05
    
    def test_zero_reported_effect(self):
        """Test handling when reported effect is zero."""
        result = calculate_relative_effect_size_difference(0.01, 0.0)
        assert result == float('inf')
        
        result = calculate_relative_effect_size_difference(0.0, 0.0)
        assert result == 0.0
    
    def test_none_values(self):
        """Test handling of None values."""
        result = calculate_relative_effect_size_difference(None, 0.05)
        assert result == float('inf')
        
        result = calculate_relative_effect_size_difference(0.05, None)
        assert result == float('inf')


class TestDetectSampleSizeMismatch:
    """Tests for sample size mismatch detection."""
    
    def test_no_mismatch(self):
        """Test when sample sizes match well."""
        result = detect_sample_size_mismatch(1000, 1000, 1000, 1000)
        assert result is False
    
    def test_small_mismatch(self):
        """Test when sample sizes have small difference (< 10%)."""
        result = detect_sample_size_mismatch(1000, 1000, 1050, 1050)
        assert result is False  # 5% difference is below 10% threshold
    
    def test_large_mismatch(self):
        """Test when sample sizes have large difference (> 10%)."""
        result = detect_sample_size_mismatch(1000, 1000, 1200, 1200)
        assert result is True  # 20% difference exceeds 10% threshold
    
    def test_none_values(self):
        """Test when any value is None."""
        result = detect_sample_size_mismatch(None, 1000, 1000, 1000)
        assert result is True
        
        result = detect_sample_size_mismatch(1000, 1000, 1000, None)
        assert result is True
    
    def test_zero_total(self):
        """Test when reported total is zero."""
        result = detect_sample_size_mismatch(0, 0, 100, 100)
        assert result is True


class TestCheckPValueConsistency:
    """Tests for p-value consistency checking."""
    
    def test_consistent_within_threshold(self):
        """Test when p-values are within threshold."""
        # Difference of 0.04 is less than 0.05 threshold
        is_consistent, diff = check_p_value_consistency(0.04, 0.08)
        assert is_consistent is True
        assert diff == 0.04
    
    def test_inconsistent_above_threshold(self):
        """Test when p-values exceed threshold."""
        # Difference of 0.06 is greater than 0.05 threshold
        is_consistent, diff = check_p_value_consistency(0.03, 0.09)
        assert is_consistent is False
        assert diff == 0.06
    
    def test_exactly_at_threshold(self):
        """Test when difference is exactly at threshold."""
        is_consistent, diff = check_p_value_consistency(0.04, 0.09)
        assert is_consistent is True  # <= threshold
        assert diff == 0.05


class TestCheckEffectSizeConsistency:
    """Tests for effect size consistency checking."""
    
    def test_consistent_within_threshold(self):
        """Test when effect sizes are within 5% relative threshold."""
        # 4% relative difference
        is_consistent, diff = check_effect_size_consistency(0.052, 0.05)
        assert is_consistent is True
        assert abs(diff - 0.04) < 0.0001
    
    def test_inconsistent_above_threshold(self):
        """Test when effect sizes exceed 5% relative threshold."""
        # 10% relative difference
        is_consistent, diff = check_effect_size_consistency(0.055, 0.05)
        assert is_consistent is False
        assert abs(diff - 0.10) < 0.0001
    
    def test_exactly_at_threshold(self):
        """Test when relative difference is exactly at threshold."""
        is_consistent, diff = check_effect_size_consistency(0.0525, 0.05)
        assert is_consistent is True  # <= threshold
        assert abs(diff - 0.05) < 0.0001


class TestCreateAuditRecord:
    """Tests for AuditRecord creation."""
    
    def test_consistent_summary(self):
        """Test creation for a consistent summary."""
        summary = ABTestSummary(
            url="https://example.com/test1",
            domain="example.com",
            outcome_type=OutcomeType.BINARY,
            p_value=0.05,
            effect_size=0.05,
            sample_size_a=1000,
            sample_size_b=1000
        )
        
        record = create_audit_record(
            summary=summary,
            is_p_consistent=True,
            p_difference=0.01,
            is_effect_consistent=True,
            effect_difference=0.02,
            has_sample_size_mismatch=False,
            reconstruction_success=True,
            reconstruction_method="z-test"
        )
        
        assert record.is_inconsistent is False
        assert len(record.notes) == 0
        assert len(record.data_quality_warnings) == 0
    
    def test_p_value_inconsistent(self):
        """Test creation when p-value is inconsistent."""
        summary = ABTestSummary(
            url="https://example.com/test2",
            domain="example.com",
            outcome_type=OutcomeType.BINARY,
            p_value=0.05,
            effect_size=0.05,
            sample_size_a=1000,
            sample_size_b=1000
        )
        
        record = create_audit_record(
            summary=summary,
            is_p_consistent=False,
            p_difference=0.08,
            is_effect_consistent=True,
            effect_difference=0.02,
            has_sample_size_mismatch=False,
            reconstruction_success=True,
            reconstruction_method="z-test"
        )
        
        assert record.is_inconsistent is True
        assert any("P-value difference" in note for note in record.notes)
    
    def test_sample_size_mismatch_generates_warning(self):
        """Test that sample size mismatch generates data_quality_warning (FR-004b)."""
        summary = ABTestSummary(
            url="https://example.com/test3",
            domain="example.com",
            outcome_type=OutcomeType.BINARY,
            p_value=0.05,
            effect_size=0.05,
            sample_size_a=1000,
            sample_size_b=1000
        )
        
        record = create_audit_record(
            summary=summary,
            is_p_consistent=True,
            p_difference=0.01,
            is_effect_consistent=True,
            effect_difference=0.02,
            has_sample_size_mismatch=True,
            reconstruction_success=True,
            reconstruction_method="z-test"
        )
        
        # FR-004b: Sample size mismatch should generate a warning
        assert len(record.data_quality_warnings) > 0
        assert any("sample size mismatch" in warning.lower() for warning in record.data_quality_warnings)
        # Sample size mismatch entries should NOT be marked as inconsistent for prevalence
        assert record.is_inconsistent is False
    
    def test_reconstruction_failure(self):
        """Test creation when reconstruction fails."""
        summary = ABTestSummary(
            url="https://example.com/test4",
            domain="example.com",
            outcome_type=OutcomeType.CONTINUOUS,
            p_value=0.05,
            effect_size=0.05,
            sample_size_a=1000,
            sample_size_b=1000
        )
        
        record = create_audit_record(
            summary=summary,
            is_p_consistent=True,
            p_difference=0.01,
            is_effect_consistent=True,
            effect_difference=0.02,
            has_sample_size_mismatch=False,
            reconstruction_success=False,
            reconstruction_method=None
        )
        
        assert any("reconstruction failed" in note.lower() for note in record.notes)


class TestValidateSummary:
    """Tests for single summary validation."""
    
    def test_valid_summary(self):
        """Test validation of a consistent summary."""
        summary = ABTestSummary(
            url="https://example.com/valid",
            domain="example.com",
            outcome_type=OutcomeType.BINARY,
            p_value=0.05,
            effect_size=0.05,
            sample_size_a=1000,
            sample_size_b=1000,
            p_value_reconstructed=0.051,
            effect_size_reconstructed=0.051,
            sample_size_a_reconstructed=1000,
            sample_size_b_reconstructed=1000,
            reconstruction_method="z-test"
        )
        
        record = validate_summary(summary)
        
        assert record.is_inconsistent is False
        assert len(record.data_quality_warnings) == 0
    
    def test_sample_size_mismatch(self):
        """Test validation detects sample size mismatch (FR-004b)."""
        summary = ABTestSummary(
            url="https://example.com/mismatch",
            domain="example.com",
            outcome_type=OutcomeType.BINARY,
            p_value=0.05,
            effect_size=0.05,
            sample_size_a=1000,
            sample_size_b=1000,
            p_value_reconstructed=0.05,
            effect_size_reconstructed=0.05,
            sample_size_a_reconstructed=1200,  # 20% mismatch
            sample_size_b_reconstructed=1200,
            reconstruction_method="z-test"
        )
        
        record = validate_summary(summary)
        
        # Should have warning but not be marked inconsistent for prevalence
        assert len(record.data_quality_warnings) > 0
        assert any("sample size mismatch" in w.lower() for w in record.data_quality_warnings)
        assert record.is_inconsistent is False  # Excluded from prevalence


class TestFilterForPrevalence:
    """Tests for filtering records for prevalence estimation (FR-004b)."""
    
    def test_excludes_sample_size_mismatch(self):
        """Test that records with sample size mismatch are excluded."""
        records = [
            AuditRecord(
                url="https://example.com/valid",
                domain="example.com",
                outcome_type=OutcomeType.BINARY,
                is_inconsistent=False,
                data_quality_warnings=[],
                notes=[]
            ),
            AuditRecord(
                url="https://example.com/mismatch",
                domain="example.com",
                outcome_type=OutcomeType.BINARY,
                is_inconsistent=False,
                data_quality_warnings=["Sample size mismatch detected"],
                notes=["Sample size mismatch detected"]
            )
        ]
        
        filtered = filter_for_prevalence(records)
        
        assert len(filtered) == 1
        assert filtered[0].url == "https://example.com/valid"
    
    def test_excludes_reconstruction_failure(self):
        """Test that records with reconstruction failure are excluded."""
        records = [
            AuditRecord(
                url="https://example.com/valid",
                domain="example.com",
                outcome_type=OutcomeType.BINARY,
                is_inconsistent=False,
                data_quality_warnings=[],
                notes=[]
            ),
            AuditRecord(
                url="https://example.com/failed",
                domain="example.com",
                outcome_type=OutcomeType.BINARY,
                is_inconsistent=False,
                data_quality_warnings=[],
                notes=["Statistical reconstruction failed"]
            )
        ]
        
        filtered = filter_for_prevalence(records)
        
        assert len(filtered) == 1
        assert filtered[0].url == "https://example.com/valid"
    
    def test_includes_valid_records(self):
        """Test that valid records are included."""
        records = [
            AuditRecord(
                url="https://example.com/valid1",
                domain="example.com",
                outcome_type=OutcomeType.BINARY,
                is_inconsistent=True,  # Inconsistent but valid for prevalence
                data_quality_warnings=[],
                notes=["P-value difference exceeds threshold"]
            ),
            AuditRecord(
                url="https://example.com/valid2",
                domain="example.com",
                outcome_type=OutcomeType.BINARY,
                is_inconsistent=False,
                data_quality_warnings=[],
                notes=[]
            )
        ]
        
        filtered = filter_for_prevalence(records)
        
        assert len(filtered) == 2


class TestWriteAuditReport:
    """Tests for writing audit report to JSON."""
    
    def test_writes_correct_file(self, tmp_path):
        """Test that the report is written to the correct file."""
        records = [
            AuditRecord(
                url="https://example.com/test",
                domain="example.com",
                outcome_type=OutcomeType.BINARY,
                is_inconsistent=False,
                data_quality_warnings=[],
                notes=[]
            )
        ]
        
        output_path = tmp_path / "test_report.json"
        result_path = write_audit_report(records, str(output_path))
        
        assert result_path == output_path
        assert output_path.exists()
        
        with open(output_path, 'r') as f:
            data = json.load(f)
        
        assert len(data) == 1
        assert data[0]['url'] == "https://example.com/test"


class TestValidateAllSummaries:
    """Tests for validating multiple summaries."""
    
    def test_validates_all(self):
        """Test that all summaries are validated."""
        summaries = [
            ABTestSummary(
                url=f"https://example.com/test{i}",
                domain="example.com",
                outcome_type=OutcomeType.BINARY,
                p_value=0.05,
                effect_size=0.05,
                sample_size_a=1000,
                sample_size_b=1000,
                p_value_reconstructed=0.05,
                effect_size_reconstructed=0.05,
                sample_size_a_reconstructed=1000,
                sample_size_b_reconstructed=1000,
                reconstruction_method="z-test"
            )
            for i in range(5)
        ]
        
        records = validate_all_summaries(summaries)
        
        assert len(records) == 5
        for i, record in enumerate(records):
            assert record.url == f"https://example.com/test{i}"
    
    def test_handles_errors_gracefully(self):
        """Test that validation handles errors gracefully."""
        summaries = [
            ABTestSummary(
                url="https://example.com/valid",
                domain="example.com",
                outcome_type=OutcomeType.BINARY,
                p_value=0.05,
                effect_size=0.05,
                sample_size_a=1000,
                sample_size_b=1000,
                p_value_reconstructed=0.05,
                effect_size_reconstructed=0.05,
                sample_size_a_reconstructed=1000,
                sample_size_b_reconstructed=1000,
                reconstruction_method="z-test"
            ),
            ABTestSummary(
                url="https://example.com/invalid",
                domain="example.com",
                outcome_type=OutcomeType.BINARY,
                p_value=0.05,
                effect_size=0.05,
                sample_size_a=1000,
                sample_size_b=1000,
                p_value_reconstructed=None,  # Missing reconstruction
                effect_size_reconstructed=None,
                sample_size_a_reconstructed=None,
                sample_size_b_reconstructed=None,
                reconstruction_method=None
            )
        ]
        
        records = validate_all_summaries(summaries)
        
        assert len(records) == 2
        # Both should be returned, even if one has issues
        assert records[0].url == "https://example.com/valid"
        assert records[1].url == "https://example.com/invalid"
        # Second should have reconstruction failure noted
        assert any("reconstruction failed" in note.lower() for note in records[1].notes)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])