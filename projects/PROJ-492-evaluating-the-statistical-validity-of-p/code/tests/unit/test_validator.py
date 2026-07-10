"""
Unit tests for the inconsistency validator.

Tests FR-004 thresholds (absolute p-difference > 0.05, relative effect-size > 5%)
and FR-004b (sample-size mismatch exclusion from prevalence).
"""

import json
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
import numpy as np

from code.src.models.data_models import ABTestSummary, AuditRecord
from code.src.audit.validator import (
    validate_single_summary,
    validate_all_summaries,
    filter_for_prevalence,
    check_sample_size_consistency,
    compute_relative_difference,
    write_audit_report,
    P_VALUE_THRESHOLD,
    EFFECT_SIZE_THRESHOLD
)


class TestComputeRelativeDifference:
    """Tests for relative difference computation."""
    
    def test_identical_values(self):
        assert compute_relative_difference(0.5, 0.5) == 0.0
        assert compute_relative_difference(100, 100) == 0.0
    
    def test_different_values(self):
        result = compute_relative_difference(0.5, 0.6)
        expected = abs(0.5 - 0.6) / 0.6  # 0.1 / 0.6 = 0.1667
        assert abs(result - expected) < 1e-10
    
    def test_zero_values(self):
        assert compute_relative_difference(0, 0) == 0.0
        assert compute_relative_difference(0, 1) == 1.0
        assert compute_relative_difference(1, 0) == 1.0
    
    def test_negative_values(self):
        result = compute_relative_difference(-0.5, -0.6)
        expected = abs(-0.5 - (-0.6)) / 0.6
        assert abs(result - expected) < 1e-10


class TestCheckSampleSizeConsistency:
    """Tests for sample size consistency checking."""
    
    def test_consistent_sample_sizes(self):
        summary = ABTestSummary(
            url="http://example.com/test1",
            domain="example.com",
            sample_size_treatment=1000,
            sample_size_control=1000,
            conversion_rate_treatment=0.1,
            conversion_rate_control=0.08
        )
        is_consistent, error = check_sample_size_consistency(summary)
        assert is_consistent is True
        assert error is None
    
    def test_moderate_mismatch(self):
        summary = ABTestSummary(
            url="http://example.com/test2",
            domain="example.com",
            sample_size_treatment=1000,
            sample_size_control=800,
            conversion_rate_treatment=0.1,
            conversion_rate_control=0.08
        )
        is_consistent, error = check_sample_size_consistency(summary)
        assert is_consistent is True
        assert error is None
    
    def test_extreme_mismatch(self):
        summary = ABTestSummary(
            url="http://example.com/test3",
            domain="example.com",
            sample_size_treatment=1000,
            sample_size_control=50,  # 20x difference
            conversion_rate_treatment=0.1,
            conversion_rate_control=0.08
        )
        is_consistent, error = check_sample_size_consistency(summary)
        assert is_consistent is False
        assert "sample size mismatch" in error.lower()
    
    def test_missing_sample_sizes(self):
        summary = ABTestSummary(
            url="http://example.com/test4",
            domain="example.com",
            sample_size_treatment=None,
            sample_size_control=1000,
            conversion_rate_treatment=0.1,
            conversion_rate_control=0.08
        )
        is_consistent, error = check_sample_size_consistency(summary)
        assert is_consistent is True
        assert error is None


class TestValidateSingleSummary:
    """Tests for single summary validation."""
    
    def test_p_value_within_threshold(self):
        summary = ABTestSummary(
            url="http://example.com/test1",
            domain="example.com",
            p_value=0.04,
            sample_size_treatment=1000,
            sample_size_control=1000
        )
        
        record = validate_single_summary(
            summary=summary,
            reconstructed_p_value=0.045,  # diff = 0.005 < 0.05
            reported_p_value=0.04
        )
        
        assert record.is_inconsistent is False
        assert len(record.inconsistency_reasons) == 0
    
    def test_p_value_exceeds_threshold(self):
        summary = ABTestSummary(
            url="http://example.com/test2",
            domain="example.com",
            p_value=0.04,
            sample_size_treatment=1000,
            sample_size_control=1000
        )
        
        record = validate_single_summary(
            summary=summary,
            reconstructed_p_value=0.10,  # diff = 0.06 > 0.05
            reported_p_value=0.04
        )
        
        assert record.is_inconsistent is True
        assert len(record.inconsistency_reasons) == 1
        assert "P-value discrepancy" in record.inconsistency_reasons[0]
    
    def test_effect_size_within_threshold(self):
        summary = ABTestSummary(
            url="http://example.com/test3",
            domain="example.com",
            effect_size=0.1,
            sample_size_treatment=1000,
            sample_size_control=1000
        )
        
        record = validate_single_summary(
            summary=summary,
            reconstructed_effect_size=0.105,  # 5% relative diff
            reported_effect_size=0.1
        )
        
        assert record.is_inconsistent is False
    
    def test_effect_size_exceeds_threshold(self):
        summary = ABTestSummary(
            url="http://example.com/test4",
            domain="example.com",
            effect_size=0.1,
            sample_size_treatment=1000,
            sample_size_control=1000
        )
        
        record = validate_single_summary(
            summary=summary,
            reconstructed_effect_size=0.12,  # 20% relative diff
            reported_effect_size=0.1
        )
        
        assert record.is_inconsistent is True
        assert len(record.inconsistency_reasons) == 1
        assert "Effect size discrepancy" in record.inconsistency_reasons[0]
    
    def test_sample_size_mismatch_warning(self):
        summary = ABTestSummary(
            url="http://example.com/test5",
            domain="example.com",
            sample_size_treatment=1000,
            sample_size_control=40,  # 25x difference
            conversion_rate_treatment=0.1,
            conversion_rate_control=0.08
        )
        
        record = validate_single_summary(
            summary=summary,
            reconstructed_p_value=0.04,
            reported_p_value=0.04
        )
        
        assert len(record.data_quality_warnings) == 1
        assert "sample size" in record.data_quality_warnings[0].lower()
    
    def test_both_p_and_effect_size_inconsistent(self):
        summary = ABTestSummary(
            url="http://example.com/test6",
            domain="example.com",
            p_value=0.04,
            effect_size=0.1,
            sample_size_treatment=1000,
            sample_size_control=1000
        )
        
        record = validate_single_summary(
            summary=summary,
            reconstructed_p_value=0.10,  # diff > 0.05
            reconstructed_effect_size=0.15,  # 50% relative diff
            reported_p_value=0.04,
            reported_effect_size=0.1
        )
        
        assert record.is_inconsistent is True
        assert len(record.inconsistency_reasons) == 2


class TestValidateAllSummaries:
    """Tests for bulk validation."""
    
    def test_validate_multiple_summaries(self):
        summaries = [
            ABTestSummary(
                url=f"http://example.com/test{i}",
                domain="example.com",
                p_value=0.04,
                sample_size_treatment=1000,
                sample_size_control=1000
            )
            for i in range(3)
        ]
        
        reconstructor_results = {
            "http://example.com/test0": {"p_value": 0.04},
            "http://example.com/test1": {"p_value": 0.10},  # Inconsistent
            "http://example.com/test2": {"p_value": 0.045}
        }
        
        records = validate_all_summaries(summaries, reconstructor_results)
        
        assert len(records) == 3
        assert records[0].is_inconsistent is False
        assert records[1].is_inconsistent is True
        assert records[2].is_inconsistent is False


class TestFilterForPrevalence:
    """Tests for prevalence filtering (FR-004b)."""
    
    def test_filter_excludes_sample_size_mismatches(self):
        # Create records with and without sample size warnings
        records = [
            AuditRecord(
                url="http://example.com/good1",
                domain="example.com",
                is_inconsistent=False,
                inconsistency_reasons=[],
                data_quality_warnings=[],
                reported_p_value=0.04,
                reconstructed_p_value=0.04
            ),
            AuditRecord(
                url="http://example.com/bad1",
                domain="example.com",
                is_inconsistent=False,
                inconsistency_reasons=[],
                data_quality_warnings=["Extreme sample size mismatch: ratio 25.0x exceeds threshold"],
                reported_p_value=0.04,
                reconstructed_p_value=0.04
            ),
            AuditRecord(
                url="http://example.com/good2",
                domain="example.com",
                is_inconsistent=True,
                inconsistency_reasons=["P-value discrepancy"],
                data_quality_warnings=[],
                reported_p_value=0.04,
                reconstructed_p_value=0.10
            ),
            AuditRecord(
                url="http://example.com/bad2",
                domain="example.com",
                is_inconsistent=True,
                inconsistency_reasons=["P-value discrepancy"],
                data_quality_warnings=["sample size mismatch"],
                reported_p_value=0.04,
                reconstructed_p_value=0.10
            )
        ]
        
        filtered = filter_for_prevalence(records)
        
        # Should exclude records with sample size warnings
        assert len(filtered) == 2
        urls = [r.url for r in filtered]
        assert "http://example.com/good1" in urls
        assert "http://example.com/good2" in urls
        assert "http://example.com/bad1" not in urls
        assert "http://example.com/bad2" not in urls


class TestWriteAuditReport:
    """Tests for report writing."""
    
    def test_write_report_creates_file(self, tmp_path):
        records = [
            AuditRecord(
                url="http://example.com/test1",
                domain="example.com",
                is_inconsistent=False,
                inconsistency_reasons=[],
                data_quality_warnings=[],
                reported_p_value=0.04,
                reconstructed_p_value=0.04
            )
        ]
        
        output_path = tmp_path / "audit_report.json"
        write_audit_report(records, output_path)
        
        assert output_path.exists()
        
        with open(output_path, 'r') as f:
            data = json.load(f)
        
        assert len(data) == 1
        assert data[0]['url'] == "http://example.com/test1"
        assert data[0]['is_inconsistent'] is False


class TestThresholds:
    """Tests that thresholds match FR-004 specification."""
    
    def test_p_value_threshold(self):
        assert P_VALUE_THRESHOLD == 0.05
    
    def test_effect_size_threshold(self):
        assert EFFECT_SIZE_THRESHOLD == 0.05  # 5%
