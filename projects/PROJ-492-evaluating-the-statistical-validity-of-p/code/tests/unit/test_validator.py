"""
Unit tests for the Inconsistency Validator (T025).

Tests cover:
1. Absolute p-difference > 0.05 threshold
2. Relative effect-size > 5% threshold
3. Inequality p-value handling
4. Sample-size mismatch detection and exclusion logic
5. data_quality_warning generation
"""
import pytest
from unittest.mock import Mock
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
    THRESHOLD_ABS_P_DIFF,
    THRESHOLD_REL_EFFECT_SIZE
)


class TestPValueDifference:
    def test_absolute_p_difference_within_threshold(self):
        reported = 0.04
        reconstructed = 0.03
        diff = calculate_absolute_p_difference(reported, reconstructed)
        assert diff == 0.01
        assert diff <= THRESHOLD_ABS_P_DIFF

    def test_absolute_p_difference_exceeds_threshold(self):
        reported = 0.04
        reconstructed = 0.10
        diff = calculate_absolute_p_difference(reported, reconstructed)
        assert diff == 0.06
        assert diff > THRESHOLD_ABS_P_DIFF

    def test_p_value_consistency_check_pass(self):
        summary = Mock(spec=ABTestSummary)
        summary.reported_p_value = "0.04"
        summary.reconstructed_p_value = 0.035
        
        is_consistent, rep, rec = check_p_value_consistency(summary)
        assert is_consistent is True

    def test_p_value_consistency_check_fail(self):
        summary = Mock(spec=ABTestSummary)
        summary.reported_p_value = "0.01"
        summary.reconstructed_p_value = 0.08
        
        is_consistent, rep, rec = check_p_value_consistency(summary)
        assert is_consistent is False


class TestEffectSizeDifference:
    def test_relative_effect_size_within_threshold(self):
        reported = 0.10
        reconstructed = 0.104
        diff = calculate_relative_effect_size_difference(reported, reconstructed)
        # |0.10 - 0.104| / 0.10 = 0.004 / 0.10 = 0.04 (4%)
        assert diff == 0.04
        assert diff <= THRESHOLD_REL_EFFECT_SIZE

    def test_relative_effect_size_exceeds_threshold(self):
        reported = 0.10
        reconstructed = 0.16
        diff = calculate_relative_effect_size_difference(reported, reconstructed)
        # |0.10 - 0.16| / 0.10 = 0.06 / 0.10 = 0.6 (60%)
        assert diff == 0.6
        assert diff > THRESHOLD_REL_EFFECT_SIZE

    def test_zero_reported_effect_size(self):
        reported = 0.0
        reconstructed = 0.05
        diff = calculate_relative_effect_size_difference(reported, reconstructed)
        assert diff == 1.0 # Infinite relative difference handled as 1.0

    def test_both_zero_effect_size(self):
        reported = 0.0
        reconstructed = 0.0
        diff = calculate_relative_effect_size_difference(reported, reconstructed)
        assert diff == 0.0


class TestSampleSizeMismatch:
    def test_valid_sample_sizes(self):
        summary = Mock(spec=ABTestSummary)
        summary.n_control = 100
        summary.n_treatment = 100
        summary.n_total = 200
        
        assert detect_sample_size_mismatch(summary) is False

    def test_negative_sample_size(self):
        summary = Mock(spec=ABTestSummary)
        summary.n_control = -10
        summary.n_treatment = 100
        summary.n_total = 90
        
        assert detect_sample_size_mismatch(summary) is True

    def test_missing_sample_size(self):
        summary = Mock(spec=ABTestSummary)
        summary.n_control = None
        summary.n_treatment = 100
        summary.n_total = None
        
        assert detect_sample_size_mismatch(summary) is True

    def test_conflicting_total_n(self):
        summary = Mock(spec=ABTestSummary)
        summary.n_control = 100
        summary.n_treatment = 100
        summary.n_total = 250 # Expected 200
        
        assert detect_sample_size_mismatch(summary) is True


class TestAuditRecordGeneration:
    def test_create_record_with_sample_mismatch_warning(self):
        summary = Mock(spec=ABTestSummary)
        summary.url = "http://example.com"
        summary.domain = "example.com"
        summary.reported_p_value = "0.05"
        summary.reconstructed_p_value = 0.05
        summary.reported_effect_size = 0.1
        summary.reconstructed_effect_size = 0.1
        
        # Force mismatch
        record = create_audit_record(
            summary, True, True, True, 0.0, 0.0
        )
        
        assert "data_quality_warning" in record.warnings
        assert "Sample size mismatch" in record.notes

    def test_create_record_inconsistent_p(self):
        summary = Mock(spec=ABTestSummary)
        summary.url = "http://example.com"
        summary.domain = "example.com"
        summary.reported_p_value = "0.01"
        summary.reconstructed_p_value = 0.10
        summary.reported_effect_size = 0.1
        summary.reconstructed_effect_size = 0.1
        
        record = create_audit_record(
            summary, False, True, False, 0.09, 0.0
        )
        
        assert record.is_inconsistent is True
        assert "P-value inconsistency" in record.notes
        assert record.warnings is None

    def test_create_record_consistent(self):
        summary = Mock(spec=ABTestSummary)
        summary.url = "http://example.com"
        summary.domain = "example.com"
        summary.reported_p_value = "0.05"
        summary.reconstructed_p_value = 0.05
        summary.reported_effect_size = 0.1
        summary.reconstructed_effect_size = 0.1
        
        record = create_audit_record(
            summary, True, True, False, 0.0, 0.0
        )
        
        assert record.is_inconsistent is False
        assert "All metrics consistent" in record.notes
        assert record.warnings is None


class TestFilterForPrevalence:
    def test_excludes_mismatched_records(self):
        # Create mock records
        record_good = Mock(spec=AuditRecord)
        record_good.sample_size_mismatch = False
        
        record_bad = Mock(spec=AuditRecord)
        record_bad.sample_size_mismatch = True
        
        records = [record_good, record_bad, record_good]
        
        filtered = filter_for_prevalence(records)
        
        assert len(filtered) == 2
        assert all(not r.sample_size_mismatch for r in filtered)

    def test_all_good_passes(self):
        record_good = Mock(spec=AuditRecord)
        record_good.sample_size_mismatch = False
        
        records = [record_good, record_good]
        
        filtered = filter_for_prevalence(records)
        
        assert len(filtered) == 2

    def test_all_bad_excludes_all(self):
        record_bad = Mock(spec=AuditRecord)
        record_bad.sample_size_mismatch = True
        
        records = [record_bad, record_bad]
        
        filtered = filter_for_prevalence(records)
        
        assert len(filtered) == 0
