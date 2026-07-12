"""
Unit tests for the inconsistency validator module (T025).
Tests FR-004 thresholds and FR-004b sample-size exclusion logic.
"""

import json
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from code.src.models.data_models import ABTestSummary, AuditRecord
from code.src.audit.validator import (
    validate_single_summary,
    validate_all_summaries,
    get_prevalence_records,
    check_sample_size_consistency,
    calculate_p_value_difference,
    calculate_effect_size_difference,
    run_validator,
    P_VALUE_THRESHOLD,
    EFFECT_SIZE_RELATIVE_THRESHOLD
)


class TestSampleSizeConsistency:
    def test_valid_sample_sizes(self):
        summary = ABTestSummary(
            url="http://example.com",
            domain="example.com",
            test_type="binary",
            n_control=1000,
            n_treatment=1000,
            control_rate=0.5,
            treatment_rate=0.55,
            reported_p_value=0.03,
            reported_effect_size=0.05
        )
        is_consistent, error = check_sample_size_consistency(summary)
        assert is_consistent is True
        assert error is None

    def test_missing_sample_sizes(self):
        summary = ABTestSummary(
            url="http://example.com",
            domain="example.com",
            test_type="binary",
            n_control=None,
            n_treatment=1000,
            control_rate=0.5,
            treatment_rate=0.55,
            reported_p_value=0.03,
            reported_effect_size=0.05
        )
        is_consistent, error = check_sample_size_consistency(summary)
        assert is_consistent is False
        assert "Missing sample sizes" in error

    def test_invalid_sample_sizes(self):
        summary = ABTestSummary(
            url="http://example.com",
            domain="example.com",
            test_type="binary",
            n_control=-100,
            n_treatment=1000,
            control_rate=0.5,
            treatment_rate=0.55,
            reported_p_value=0.03,
            reported_effect_size=0.05
        )
        is_consistent, error = check_sample_size_consistency(summary)
        assert is_consistent is False
        assert "Invalid sample sizes" in error

    def test_extreme_mismatch(self):
        summary = ABTestSummary(
            url="http://example.com",
            domain="example.com",
            test_type="binary",
            n_control=10,
            n_treatment=10000,
            control_rate=0.5,
            treatment_rate=0.55,
            reported_p_value=0.03,
            reported_effect_size=0.05
        )
        is_consistent, error = check_sample_size_consistency(summary)
        assert is_consistent is False
        assert "Extreme sample size mismatch" in error


class TestPValueDifference:
    def test_small_difference(self):
        diff = calculate_p_value_difference(0.04, 0.045)
        assert diff < P_VALUE_THRESHOLD

    def test_large_difference(self):
        diff = calculate_p_value_difference(0.04, 0.10)
        assert diff > P_VALUE_THRESHOLD

    def test_none_values(self):
        diff = calculate_p_value_difference(None, 0.05)
        assert diff == float('inf')


class TestEffectSizeDifference:
    def test_small_relative_difference(self):
        diff = calculate_effect_size_difference(0.05, 0.052)  # 4% diff
        assert diff < EFFECT_SIZE_RELATIVE_THRESHOLD

    def test_large_relative_difference(self):
        diff = calculate_effect_size_difference(0.05, 0.06)  # 20% diff
        assert diff > EFFECT_SIZE_RELATIVE_THRESHOLD

    def test_zero_reported_effect(self):
        diff = calculate_effect_size_difference(0.05, 0.0)
        assert diff == float('inf')


class TestValidation:
    def test_consistent_summary(self):
        summary = ABTestSummary(
            url="http://example.com",
            domain="example.com",
            test_type="binary",
            n_control=1000,
            n_treatment=1000,
            control_rate=0.5,
            treatment_rate=0.55,
            reported_p_value=0.03,
            reported_effect_size=0.05,
            reconstructed_p_value=0.032,
            reconstructed_effect_size=0.051
        )
        record = validate_single_summary(summary)
        assert record.is_inconsistent is False
        assert record.p_value_consistent is True
        assert record.effect_size_consistent is True
        assert record.sample_size_consistent is True

    def test_p_value_inconsistency(self):
        summary = ABTestSummary(
            url="http://example.com",
            domain="example.com",
            test_type="binary",
            n_control=1000,
            n_treatment=1000,
            control_rate=0.5,
            treatment_rate=0.55,
            reported_p_value=0.03,
            reported_effect_size=0.05,
            reconstructed_p_value=0.10,  # Diff > 0.05
            reconstructed_effect_size=0.051
        )
        record = validate_single_summary(summary)
        assert record.is_inconsistent is True
        assert record.p_value_consistent is False
        assert "P-value discrepancy" in record.inconsistency_reasons[0]

    def test_effect_size_inconsistency(self):
        summary = ABTestSummary(
            url="http://example.com",
            domain="example.com",
            test_type="binary",
            n_control=1000,
            n_treatment=1000,
            control_rate=0.5,
            treatment_rate=0.55,
            reported_p_value=0.03,
            reported_effect_size=0.05,
            reconstructed_p_value=0.032,
            reconstructed_effect_size=0.06  # 20% diff > 5%
        )
        record = validate_single_summary(summary)
        assert record.is_inconsistent is True
        assert record.effect_size_consistent is False
        assert "Effect size discrepancy" in record.inconsistency_reasons[0]

    def test_sample_size_warning_generation(self):
        summary = ABTestSummary(
            url="http://example.com",
            domain="example.com",
            test_type="binary",
            n_control=None,  # Missing
            n_treatment=1000,
            control_rate=0.5,
            treatment_rate=0.55,
            reported_p_value=0.03,
            reported_effect_size=0.05,
            reconstructed_p_value=0.032,
            reconstructed_effect_size=0.051
        )
        record = validate_single_summary(summary)
        assert record.sample_size_consistent is False
        assert record.data_quality_warning is not None
        assert "Sample size" in record.data_quality_warning


class TestPrevalenceExclusion:
    def test_exclusion_of_mismatched_records(self):
        # Create records with mixed sample size consistency
        record1 = AuditRecord(
            url="http://example.com/1",
            domain="example.com",
            test_type="binary",
            is_inconsistent=False,
            p_value_consistent=True,
            effect_size_consistent=True,
            sample_size_consistent=True,
            data_quality_warning=None,
            inconsistency_reasons=[],
            reconstructed_p_value=0.03,
            reported_p_value=0.03,
            reconstructed_effect_size=0.05,
            reported_effect_size=0.05,
            n_control=1000,
            n_treatment=1000,
            validation_timestamp="2024-01-01T00:00:00"
        )
        
        record2 = AuditRecord(
            url="http://example.com/2",
            domain="example.com",
            test_type="binary",
            is_inconsistent=True,
            p_value_consistent=False,
            effect_size_consistent=True,
            sample_size_consistent=False,  # Mismatch!
            data_quality_warning="Sample size issue",
            inconsistency_reasons=["Sample size mismatch"],
            reconstructed_p_value=0.10,
            reported_p_value=0.03,
            reconstructed_effect_size=0.05,
            reported_effect_size=0.05,
            n_control=None,
            n_treatment=1000,
            validation_timestamp="2024-01-01T00:00:00"
        )
        
        records = [record1, record2]
        prevalence_records = get_prevalence_records(records)
        
        assert len(prevalence_records) == 1
        assert prevalence_records[0].url == "http://example.com/1"
        assert record2 not in prevalence_records


class TestRunValidator:
    def test_end_to_end_validation(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = Path(tmpdir) / "summaries.json"
            output_path = Path(tmpdir) / "audit_report.json"
            
            # Create test data
            summaries = [
                {
                    "url": "http://example.com/1",
                    "domain": "example.com",
                    "test_type": "binary",
                    "n_control": 1000,
                    "n_treatment": 1000,
                    "control_rate": 0.5,
                    "treatment_rate": 0.55,
                    "reported_p_value": 0.03,
                    "reported_effect_size": 0.05,
                    "reconstructed_p_value": 0.032,
                    "reconstructed_effect_size": 0.051
                },
                {
                    "url": "http://example.com/2",
                    "domain": "example.com",
                    "test_type": "binary",
                    "n_control": None,
                    "n_treatment": 1000,
                    "control_rate": 0.5,
                    "treatment_rate": 0.55,
                    "reported_p_value": 0.03,
                    "reported_effect_size": 0.05,
                    "reconstructed_p_value": 0.032,
                    "reconstructed_effect_size": 0.051
                }
            ]
            
            with open(input_path, 'w') as f:
                json.dump(summaries, f)
            
            # Run validator
            records = run_validator(input_path, output_path, log_level="WARNING")
            
            # Verify output file exists
            assert output_path.exists()
            
            # Verify records
            assert len(records) == 2
            assert records[0].is_inconsistent is False
            assert records[1].sample_size_consistent is False
            assert records[1].data_quality_warning is not None
            
            # Verify JSON structure
            with open(output_path, 'r') as f:
                report = json.load(f)
            
            assert "metadata" in report
            assert "records" in report
            assert report["metadata"]["total_records"] == 2
            assert report["metadata"]["sample_size_warning_count"] == 1