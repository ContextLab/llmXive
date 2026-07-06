"""
Unit tests for the inconsistency validator (T025).
Tests FR-004 thresholds and FR-004b sample-size exclusion logic.
"""
import pytest
from code.src.models.data_models import ABTestSummary
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
)


class TestPValueDifference:
    def test_absolute_p_difference_positive(self):
        diff = calculate_absolute_p_difference(0.04, 0.10)
        assert diff == pytest.approx(0.06)

    def test_absolute_p_difference_negative(self):
        diff = calculate_absolute_p_difference(0.10, 0.04)
        assert diff == pytest.approx(0.06)

    def test_absolute_p_difference_zero(self):
        diff = calculate_absolute_p_difference(0.05, 0.05)
        assert diff == pytest.approx(0.0)


class TestEffectSizeDifference:
    def test_relative_effect_size_difference(self):
        # Reported 0.10, Reconstructed 0.105 -> diff 0.005, rel 0.05
        diff = calculate_relative_effect_size_difference(0.10, 0.105)
        assert diff == pytest.approx(0.05)

    def test_relative_effect_size_difference_small(self):
        # Reported 0.10, Reconstructed 0.101 -> diff 0.001, rel 0.01
        diff = calculate_relative_effect_size_difference(0.10, 0.101)
        assert diff == pytest.approx(0.01)

    def test_relative_effect_size_zero_reported(self):
        # Reported 0.0 -> should return inf
        diff = calculate_relative_effect_size_difference(0.0, 0.05)
        assert diff == float('inf')


class TestSampleSizeMismatch:
    def test_mismatch_missing_data(self):
        summary = ABTestSummary(
            url="http://example.com",
            domain="example.com",
            n_control=None,
            n_treatment=100,
            p_value_reported=0.05,
            p_value_reconstructed=0.05,
            effect_size_reported=0.1,
            effect_size_reconstructed=0.1
        )
        assert detect_sample_size_mismatch(summary) is True

    def test_no_mismatch_complete_data(self):
        summary = ABTestSummary(
            url="http://example.com",
            domain="example.com",
            n_control=100,
            n_treatment=100,
            p_value_reported=0.05,
            p_value_reconstructed=0.05,
            effect_size_reported=0.1,
            effect_size_reconstructed=0.1
        )
        assert detect_sample_size_mismatch(summary) is False


class TestPValueConsistency:
    def test_consistent_p_value(self):
        summary = ABTestSummary(
            url="http://example.com",
            domain="example.com",
            n_control=100,
            n_treatment=100,
            p_value_reported=0.04,
            p_value_reconstructed=0.045, # diff 0.005 < 0.05
            effect_size_reported=0.1,
            effect_size_reconstructed=0.1
        )
        is_consistent, diff = check_p_value_consistency(summary)
        assert is_consistent is True
        assert diff == pytest.approx(0.005)

    def test_inconsistent_p_value(self):
        summary = ABTestSummary(
            url="http://example.com",
            domain="example.com",
            n_control=100,
            n_treatment=100,
            p_value_reported=0.04,
            p_value_reconstructed=0.10, # diff 0.06 > 0.05
            effect_size_reported=0.1,
            effect_size_reconstructed=0.1
        )
        is_consistent, diff = check_p_value_consistency(summary)
        assert is_consistent is False
        assert diff == pytest.approx(0.06)


class TestEffectSizeConsistency:
    def test_consistent_effect_size(self):
        summary = ABTestSummary(
            url="http://example.com",
            domain="example.com",
            n_control=100,
            n_treatment=100,
            p_value_reported=0.05,
            p_value_reconstructed=0.05,
            effect_size_reported=0.10,
            effect_size_reconstructed=0.104 # diff 0.004, rel 0.04 < 0.05
        )
        is_consistent, diff = check_effect_size_consistency(summary)
        assert is_consistent is True
        assert diff == pytest.approx(0.04)

    def test_inconsistent_effect_size(self):
        summary = ABTestSummary(
            url="http://example.com",
            domain="example.com",
            n_control=100,
            n_treatment=100,
            p_value_reported=0.05,
            p_value_reconstructed=0.05,
            effect_size_reported=0.10,
            effect_size_reconstructed=0.106 # diff 0.006, rel 0.06 > 0.05
        )
        is_consistent, diff = check_effect_size_consistency(summary)
        assert is_consistent is False
        assert diff == pytest.approx(0.06)


class TestCreateAuditRecord:
    def test_record_with_warnings(self):
        summary = ABTestSummary(
            url="http://example.com",
            domain="example.com",
            n_control=None,
            n_treatment=100,
            p_value_reported=0.04,
            p_value_reconstructed=0.10,
            effect_size_reported=0.1,
            effect_size_reconstructed=0.1
        )
        record = create_audit_record(
            summary,
            p_consistent=False,
            p_diff=0.06,
            effect_consistent=True,
            effect_diff=0.0,
            sample_size_mismatch=True
        )
        assert record.is_inconsistent is True
        assert record.sample_size_mismatch is True
        assert record.data_quality_warning is not None
        assert "Sample size" in record.data_quality_warning

    def test_record_consistent(self):
        summary = ABTestSummary(
            url="http://example.com",
            domain="example.com",
            n_control=100,
            n_treatment=100,
            p_value_reported=0.04,
            p_value_reconstructed=0.045,
            effect_size_reported=0.1,
            effect_size_reconstructed=0.1
        )
        record = create_audit_record(
            summary,
            p_consistent=True,
            p_diff=0.005,
            effect_consistent=True,
            effect_diff=0.0,
            sample_size_mismatch=False
        )
        assert record.is_inconsistent is False
        assert record.sample_size_mismatch is False
        assert record.data_quality_warning is None


class TestFilterForPrevalence:
    def test_filter_excludes_mismatch(self):
        records = [
            create_audit_record(
                ABTestSummary(url="1", domain="a", n_control=None, n_treatment=1, p_value_reported=0.01, p_value_reconstructed=0.01, effect_size_reported=0.1, effect_size_reconstructed=0.1),
                True, 0.0, True, 0.0, True
            ),
            create_audit_record(
                ABTestSummary(url="2", domain="a", n_control=10, n_treatment=10, p_value_reported=0.01, p_value_reconstructed=0.01, effect_size_reported=0.1, effect_size_reconstructed=0.1),
                True, 0.0, True, 0.0, False
            )
        ]
        filtered = filter_for_prevalence(records)
        assert len(filtered) == 1
        assert filtered[0].url == "2"