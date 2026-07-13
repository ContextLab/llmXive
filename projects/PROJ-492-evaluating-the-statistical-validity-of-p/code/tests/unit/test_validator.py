"""
Unit tests for the inconsistency validator (T025).

Tests cover:
- Absolute p-difference > 0.05 threshold
- Relative effect-size > 5% threshold
- Inequality handling (None values)
- Sample-size mismatch detection and data_quality_warning generation
"""
import json
import pytest
from pathlib import Path
from datetime import datetime

from code.src.audit.validator import (
    validate_single_summary,
    validate_sample_size_consistency,
    create_audit_record,
    run_validator,
    P_DIFF_THRESHOLD,
    EFFECT_SIZE_RELATIVE_THRESHOLD
)
from code.src.models.data_models import ABTestSummary, AuditRecord


class TestPValueThreshold:
    """Tests for FR-004 absolute p-difference threshold (> 0.05)"""

    def test_p_difference_within_threshold(self):
        """P-difference of 0.03 should be consistent"""
        summary = ABTestSummary(
            url="http://example.com/test1",
            domain="example.com",
            p_value=0.05,
            effect_size=0.1,
            sample_size_a=100,
            sample_size_b=100
        )
        reconstructed_p = 0.07  # diff = 0.02
        
        is_consistent, warnings = validate_single_summary(
            summary, reconstructed_p, 0.1
        )
        
        assert is_consistent is True
        assert len(warnings) == 0

    def test_p_difference_exceeds_threshold(self):
        """P-difference of 0.06 should be inconsistent"""
        summary = ABTestSummary(
            url="http://example.com/test2",
            domain="example.com",
            p_value=0.05,
            effect_size=0.1,
            sample_size_a=100,
            sample_size_b=100
        )
        reconstructed_p = 0.11  # diff = 0.06
        
        is_consistent, warnings = validate_single_summary(
            summary, reconstructed_p, 0.1
        )
        
        assert is_consistent is False
        assert len(warnings) == 1
        assert "P-value discrepancy" in warnings[0]
        assert "0.06" in warnings[0]

    def test_p_difference_exactly_threshold(self):
        """P-difference of exactly 0.05 should be consistent (not > threshold)"""
        summary = ABTestSummary(
            url="http://example.com/test3",
            domain="example.com",
            p_value=0.05,
            effect_size=0.1,
            sample_size_a=100,
            sample_size_b=100
        )
        reconstructed_p = 0.10  # diff = 0.05
        
        is_consistent, warnings = validate_single_summary(
            summary, reconstructed_p, 0.1
        )
        
        assert is_consistent is True
        assert len(warnings) == 0


class TestEffectSizeThreshold:
    """Tests for FR-004 relative effect-size threshold (> 5%)"""

    def test_effect_size_within_threshold(self):
        """5% relative difference should be consistent"""
        summary = ABTestSummary(
            url="http://example.com/test4",
            domain="example.com",
            p_value=0.05,
            effect_size=0.20,
            sample_size_a=100,
            sample_size_b=100
        )
        reconstructed_effect = 0.21  # 5% relative diff
        
        is_consistent, warnings = validate_single_summary(
            summary, 0.05, reconstructed_effect
        )
        
        assert is_consistent is True
        assert len(warnings) == 0

    def test_effect_size_exceeds_threshold(self):
        """10% relative difference should be inconsistent"""
        summary = ABTestSummary(
            url="http://example.com/test5",
            domain="example.com",
            p_value=0.05,
            effect_size=0.20,
            sample_size_a=100,
            sample_size_b=100
        )
        reconstructed_effect = 0.22  # 10% relative diff
        
        is_consistent, warnings = validate_single_summary(
            summary, 0.05, reconstructed_effect
        )
        
        assert is_consistent is False
        assert len(warnings) == 1
        assert "Effect size discrepancy" in warnings[0]
        assert "0.10" in warnings[0]

    def test_effect_size_zero_reported(self):
        """Zero reported effect size should not crash (division by zero)"""
        summary = ABTestSummary(
            url="http://example.com/test6",
            domain="example.com",
            p_value=0.05,
            effect_size=0.0,
            sample_size_a=100,
            sample_size_b=100
        )
        reconstructed_effect = 0.01
        
        is_consistent, warnings = validate_single_summary(
            summary, 0.05, reconstructed_effect
        )
        
        assert is_consistent is True
        assert len(warnings) == 0  # Should not flag due to division by zero protection


class TestInequalityHandling:
    """Tests for handling None/missing values"""

    def test_missing_reported_p_value(self):
        """Missing reported p-value should not cause inconsistency"""
        summary = ABTestSummary(
            url="http://example.com/test7",
            domain="example.com",
            p_value=None,
            effect_size=0.1,
            sample_size_a=100,
            sample_size_b=100
        )
        
        is_consistent, warnings = validate_single_summary(
            summary, 0.05, 0.1
        )
        
        assert is_consistent is True
        assert len(warnings) == 0

    def test_missing_reconstructed_p_value(self):
        """Missing reconstructed p-value should not cause inconsistency"""
        summary = ABTestSummary(
            url="http://example.com/test8",
            domain="example.com",
            p_value=0.05,
            effect_size=0.1,
            sample_size_a=100,
            sample_size_b=100
        )
        
        is_consistent, warnings = validate_single_summary(
            summary, None, 0.1
        )
        
        assert is_consistent is True
        assert len(warnings) == 0

    def test_both_p_values_missing(self):
        """Both p-values missing should be consistent"""
        summary = ABTestSummary(
            url="http://example.com/test9",
            domain="example.com",
            p_value=None,
            effect_size=None,
            sample_size_a=100,
            sample_size_b=100
        )
        
        is_consistent, warnings = validate_single_summary(
            summary, None, None
        )
        
        assert is_consistent is True
        assert len(warnings) == 0


class TestSampleSizeMismatch:
    """Tests for FR-004b sample-size mismatch detection"""

    def test_balanced_sample_sizes(self):
        """Balanced sample sizes should be consistent"""
        summary = ABTestSummary(
            url="http://example.com/test10",
            domain="example.com",
            p_value=0.05,
            effect_size=0.1,
            sample_size_a=100,
            sample_size_b=100
        )
        
        is_consistent, warning = validate_sample_size_consistency(summary)
        
        assert is_consistent is True
        assert warning is None

    def test_extreme_imbalance_detected(self):
        """Extreme imbalance (ratio > 10) should be flagged"""
        summary = ABTestSummary(
            url="http://example.com/test11",
            domain="example.com",
            p_value=0.05,
            effect_size=0.1,
            sample_size_a=10,
            sample_size_b=1000  # ratio = 100
        )
        
        is_consistent, warning = validate_sample_size_consistency(summary)
        
        assert is_consistent is False
        assert warning is not None
        assert "extreme" in warning.lower() or "imbalance" in warning.lower()

    def test_missing_sample_sizes(self):
        """Missing sample sizes should not cause inconsistency"""
        summary = ABTestSummary(
            url="http://example.com/test12",
            domain="example.com",
            p_value=0.05,
            effect_size=0.1,
            sample_size_a=None,
            sample_size_b=100
        )
        
        is_consistent, warning = validate_sample_size_consistency(summary)
        
        assert is_consistent is True
        assert warning is None


class TestDataQualityWarningGeneration:
    """Tests for data_quality_warning message generation"""

    def test_sample_size_warning_included(self):
        """Sample size mismatch should generate data_quality_warning"""
        summary = ABTestSummary(
            url="http://example.com/test13",
            domain="example.com",
            p_value=0.05,
            effect_size=0.1,
            sample_size_a=10,
            sample_size_b=1000
        )
        
        record = create_audit_record(
            summary,
            0.05,
            0.1,
            is_consistent=False,
            warnings=["Sample size issue: Extreme imbalance"],
            sample_size_warning="Extreme sample size imbalance: ratio=100.00"
        )
        
        assert record.data_quality_warning is not None
        assert "Extreme sample size imbalance" in record.data_quality_warning
        assert record.is_consistent is False

    def test_statistical_warning_included(self):
        """Statistical warnings should generate data_quality_warning"""
        summary = ABTestSummary(
            url="http://example.com/test14",
            domain="example.com",
            p_value=0.05,
            effect_size=0.1,
            sample_size_a=100,
            sample_size_b=100
        )
        
        record = create_audit_record(
            summary,
            0.11,  # High p-diff
            0.1,
            is_consistent=False,
            warnings=["P-value discrepancy: reported=0.05, reconstructed=0.11, diff=0.06 > 0.05"],
            sample_size_warning=None
        )
        
        assert record.data_quality_warning is not None
        assert "P-value discrepancy" in record.data_quality_warning


class TestRunValidator:
    """Integration tests for run_validator function"""

    def test_run_validator_creates_output(self, tmp_path):
        """run_validator should create output file with correct structure"""
        summaries = [
            ABTestSummary(
                url="http://example.com/test15",
                domain="example.com",
                p_value=0.05,
                effect_size=0.1,
                sample_size_a=100,
                sample_size_b=100
            )
        ]
        
        reconstructed = [
            {"p_value": 0.05, "effect_size": 0.1}
        ]
        
        output_path = tmp_path / "audit_report.json"
        
        records = run_validator(summaries, reconstructed, output_path)
        
        assert len(records) == 1
        assert output_path.exists()
        
        with open(output_path) as f:
            report = json.load(f)
        
        assert "generated_at" in report
        assert "total_records" in report
        assert "consistent_count" in report
        assert "inconsistent_count" in report
        assert "records" in report
        assert report["total_records"] == 1
        assert report["consistent_count"] == 1
        assert report["inconsistent_count"] == 0

    def test_run_validator_with_mismatched_counts(self):
        """run_validator should raise error for mismatched counts"""
        summaries = [
            ABTestSummary(
                url="http://example.com/test16",
                domain="example.com",
                p_value=0.05,
                effect_size=0.1,
                sample_size_a=100,
                sample_size_b=100
            )
        ]
        
        reconstructed = []  # Empty - mismatch
        
        output_path = Path("/tmp/test_output.json")
        
        with pytest.raises(ValueError, match="Summary and reconstruction counts must match"):
            run_validator(summaries, reconstructed, output_path)

    def test_run_validator_excludes_sample_size_mismatches(self, tmp_path):
        """Sample size mismatch entries should be marked inconsistent (FR-004b)"""
        summaries = [
            ABTestSummary(
                url="http://example.com/test17",
                domain="example.com",
                p_value=0.05,
                effect_size=0.1,
                sample_size_a=100,
                sample_size_b=100  # Balanced
            ),
            ABTestSummary(
                url="http://example.com/test18",
                domain="example.com",
                p_value=0.05,
                effect_size=0.1,
                sample_size_a=10,
                sample_size_b=1000  # Extreme imbalance
            )
        ]
        
        reconstructed = [
            {"p_value": 0.05, "effect_size": 0.1},
            {"p_value": 0.05, "effect_size": 0.1}
        ]
        
        output_path = tmp_path / "audit_report.json"
        records = run_validator(summaries, reconstructed, output_path)
        
        assert len(records) == 2
        assert records[0].is_consistent is True  # Balanced
        assert records[1].is_consistent is False  # Imbalanced
        assert records[1].data_quality_warning is not None
        assert "sample size" in records[1].data_quality_warning.lower()