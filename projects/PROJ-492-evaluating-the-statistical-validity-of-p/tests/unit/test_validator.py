"""
Unit tests for the validator module (T025 implementation).
Covers:
  - Absolute p-difference > 0.05
  - Relative effect-size > 5%
  - Inequality handling (p-values reported as < or >)
  - Sample-size mismatch with data_quality_warning generation
"""
import pytest
import numpy as np
from unittest.mock import patch, MagicMock

# Import from the actual implementation
from code.src.audit.validator import (
    calculate_absolute_p_difference,
    calculate_relative_effect_size_difference,
    detect_sample_size_mismatch,
    check_p_value_consistency,
    check_effect_size_consistency,
    create_audit_record,
    validate_summary,
)
from code.src.models.data_models import ABTestSummary, AuditRecord

# Constants for testing
P_DIFF_THRESHOLD = 0.05
EFFECT_SIZE_THRESHOLD = 0.05  # 5%


class TestCalculateAbsolutePDifference:
    """Tests for absolute p-value difference calculation."""

    def test_identical_p_values(self):
        """When p-values are identical, difference is 0."""
        assert calculate_absolute_p_difference(0.03, 0.03) == 0.0

    def test_small_difference(self):
        """Small difference below threshold."""
        diff = calculate_absolute_p_difference(0.03, 0.04)
        assert diff == 0.01

    def test_large_difference(self):
        """Large difference above threshold."""
        diff = calculate_absolute_p_difference(0.01, 0.10)
        assert diff == 0.09

    def test_reconstructed_larger(self):
        """Reconstructed p-value larger than reported."""
        diff = calculate_absolute_p_difference(0.05, 0.12)
        assert diff == 0.07

    def test_reconstructed_smaller(self):
        """Reconstructed p-value smaller than reported."""
        diff = calculate_absolute_p_difference(0.12, 0.05)
        assert diff == 0.07

    def test_zero_values(self):
        """Both p-values are zero."""
        assert calculate_absolute_p_difference(0.0, 0.0) == 0.0


class TestCalculateRelativeEffectSizeDifference:
    """Tests for relative effect-size difference calculation."""

    def test_identical_effect_sizes(self):
        """When effect sizes are identical, relative difference is 0."""
        assert calculate_relative_effect_size_difference(10.0, 10.0) == 0.0

    def test_small_relative_difference(self):
        """Small relative difference below 5%."""
        # 10% vs 10.4% is 4% relative difference
        diff = calculate_relative_effect_size_difference(10.0, 10.4)
        assert abs(diff - 0.04) < 1e-9

    def test_large_relative_difference(self):
        """Large relative difference above 5%."""
        # 10% vs 11% is 10% relative difference
        diff = calculate_relative_effect_size_difference(10.0, 11.0)
        assert abs(diff - 0.10) < 1e-9

    def test_negative_effect_sizes(self):
        """Handle negative effect sizes correctly."""
        # -5% vs -5.25% is 5% relative difference
        diff = calculate_relative_effect_size_difference(-5.0, -5.25)
        assert abs(diff - 0.05) < 1e-9

    def test_zero_baseline(self):
        """Zero baseline should not cause division by zero in real usage,
        but for this unit test we assume non-zero baselines as per spec."""
        # This case should be handled by upstream validation
        with pytest.raises(ZeroDivisionError):
            calculate_relative_effect_size_difference(0.0, 1.0)


class TestDetectSampleSizeMismatch:
    """Tests for sample size mismatch detection."""

    def test_no_mismatch(self):
        """When sample sizes match, no mismatch detected."""
        assert detect_sample_size_mismatch(100, 100) is False

    def test_small_mismatch(self):
        """Small mismatch detected."""
        assert detect_sample_size_mismatch(100, 105) is True

    def test_large_mismatch(self):
        """Large mismatch detected."""
        assert detect_sample_size_mismatch(100, 200) is True

    def test_control_only(self):
        """When only control size is provided, no mismatch check possible."""
        # Assuming None indicates missing data
        assert detect_sample_size_mismatch(100, None) is False

    def test_treatment_only(self):
        """When only treatment size is provided, no mismatch check possible."""
        assert detect_sample_size_mismatch(None, 100) is False


class TestCheckPValueConsistency:
    """Tests for p-value consistency checking."""

    def test_consistent_within_threshold(self):
        """P-values within threshold are consistent."""
        is_consistent, diff = check_p_value_consistency(0.03, 0.04, threshold=0.05)
        assert is_consistent is True
        assert diff == 0.01

    def test_inconsistent_above_threshold(self):
        """P-values above threshold are inconsistent."""
        is_consistent, diff = check_p_value_consistency(0.01, 0.10, threshold=0.05)
        assert is_consistent is False
        assert diff == 0.09

    def test_inequality_less_than(self):
        """Handle p-value reported as '< 0.05'."""
        # Reported: < 0.05, Reconstructed: 0.03
        # We treat '< 0.05' as 0.05 for comparison
        is_consistent, diff = check_p_value_consistency(0.05, 0.03, threshold=0.05)
        assert is_consistent is True
        assert diff == 0.02

    def test_inequality_greater_than(self):
        """Handle p-value reported as '> 0.05'."""
        # Reported: > 0.05, Reconstructed: 0.03
        # We treat '> 0.05' as 0.05 for comparison (conservative)
        is_consistent, diff = check_p_value_consistency(0.05, 0.03, threshold=0.05)
        assert is_consistent is True
        assert diff == 0.02

    def test_inequality_very_small(self):
        """Handle p-value reported as '< 0.001'."""
        is_consistent, diff = check_p_value_consistency(0.001, 0.0005, threshold=0.05)
        assert is_consistent is True
        assert diff == 0.0005


class TestCheckEffectSizeConsistency:
    """Tests for effect size consistency checking."""

    def test_consistent_within_threshold(self):
        """Effect sizes within 5% relative difference are consistent."""
        is_consistent, rel_diff = check_effect_size_consistency(10.0, 10.4, threshold=0.05)
        assert is_consistent is True
        assert abs(rel_diff - 0.04) < 1e-9

    def test_inconsistent_above_threshold(self):
        """Effect sizes above 5% relative difference are inconsistent."""
        is_consistent, rel_diff = check_effect_size_consistency(10.0, 11.0, threshold=0.05)
        assert is_consistent is False
        assert abs(rel_diff - 0.10) < 1e-9

    def test_zero_effect_sizes(self):
        """Zero effect sizes should be consistent."""
        is_consistent, rel_diff = check_effect_size_consistency(0.0, 0.0, threshold=0.05)
        assert is_consistent is True
        assert rel_diff == 0.0


class TestCreateAuditRecord:
    """Tests for audit record creation."""

    def test_consistent_summary(self):
        """Create record for consistent summary."""
        summary = ABTestSummary(
            url="https://example.com/test1",
            domain="example.com",
            title="Test 1",
            baseline_conversion_rate=0.10,
            treatment_conversion_rate=0.12,
            sample_size_control=1000,
            sample_size_treatment=1000,
            reported_p_value=0.03,
            effect_size=2.0,
            test_type="binary"
        )
        record = create_audit_record(
            summary=summary,
            reconstructed_p_value=0.035,
            reconstructed_effect_size=2.1,
            is_p_consistent=True,
            is_effect_consistent=True,
            has_sample_size_mismatch=False
        )

        assert record.url == "https://example.com/test1"
        assert record.is_consistent is True
        assert record.data_quality_warning is None
        assert record.notes == "All checks passed."

    def test_p_value_inconsistent(self):
        """Create record for p-value inconsistent summary."""
        summary = ABTestSummary(
            url="https://example.com/test2",
            domain="example.com",
            title="Test 2",
            baseline_conversion_rate=0.10,
            treatment_conversion_rate=0.12,
            sample_size_control=1000,
            sample_size_treatment=1000,
            reported_p_value=0.01,
            effect_size=2.0,
            test_type="binary"
        )
        record = create_audit_record(
            summary=summary,
            reconstructed_p_value=0.10,
            reconstructed_effect_size=2.0,
            is_p_consistent=False,
            is_effect_consistent=True,
            has_sample_size_mismatch=False
        )

        assert record.is_consistent is False
        assert "p-value discrepancy" in record.notes

    def test_sample_size_mismatch_warning(self):
        """Create record with data_quality_warning for sample size mismatch."""
        summary = ABTestSummary(
            url="https://example.com/test3",
            domain="example.com",
            title="Test 3",
            baseline_conversion_rate=0.10,
            treatment_conversion_rate=0.12,
            sample_size_control=1000,
            sample_size_treatment=1500,  # Mismatch
            reported_p_value=0.03,
            effect_size=2.0,
            test_type="binary"
        )
        record = create_audit_record(
            summary=summary,
            reconstructed_p_value=0.035,
            reconstructed_effect_size=2.1,
            is_p_consistent=True,
            is_effect_consistent=True,
            has_sample_size_mismatch=True
        )

        assert record.data_quality_warning is not None
        assert "sample size mismatch" in record.data_quality_warning.lower()
        # Even if consistent, mismatch triggers warning
        assert record.is_consistent is True  # Consistency is about stats, not data quality

    def test_multiple_issues(self):
        """Create record with multiple issues."""
        summary = ABTestSummary(
            url="https://example.com/test4",
            domain="example.com",
            title="Test 4",
            baseline_conversion_rate=0.10,
            treatment_conversion_rate=0.12,
            sample_size_control=1000,
            sample_size_treatment=2000,  # Mismatch
            reported_p_value=0.01,
            effect_size=2.0,
            test_type="binary"
        )
        record = create_audit_record(
            summary=summary,
            reconstructed_p_value=0.10,
            reconstructed_effect_size=2.5,
            is_p_consistent=False,
            is_effect_consistent=False,
            has_sample_size_mismatch=True
        )

        assert record.is_consistent is False
        assert record.data_quality_warning is not None
        assert "p-value discrepancy" in record.notes
        assert "effect size discrepancy" in record.notes


class TestValidateSummary:
    """Tests for full summary validation."""

    @patch('code.src.audit.validator.calculate_absolute_p_difference')
    @patch('code.src.audit.validator.calculate_relative_effect_size_difference')
    @patch('code.src.audit.validator.detect_sample_size_mismatch')
    def test_full_validation_consistent(
        self, mock_mismatch, mock_effect, mock_p_diff
    ):
        """Full validation for a consistent summary."""
        mock_p_diff.return_value = 0.01
        mock_effect.return_value = 0.02
        mock_mismatch.return_value = False

        summary = ABTestSummary(
            url="https://example.com/test5",
            domain="example.com",
            title="Test 5",
            baseline_conversion_rate=0.10,
            treatment_conversion_rate=0.12,
            sample_size_control=1000,
            sample_size_treatment=1000,
            reported_p_value=0.03,
            effect_size=2.0,
            test_type="binary"
        )

        record = validate_summary(
            summary=summary,
            reconstructed_p_value=0.04,
            reconstructed_effect_size=2.04,
            p_threshold=0.05,
            effect_threshold=0.05
        )

        assert record.is_consistent is True
        assert record.data_quality_warning is None

    @patch('code.src.audit.validator.calculate_absolute_p_difference')
    @patch('code.src.audit.validator.calculate_relative_effect_size_difference')
    @patch('code.src.audit.validator.detect_sample_size_mismatch')
    def test_full_validation_p_inconsistent(
        self, mock_mismatch, mock_effect, mock_p_diff
    ):
        """Full validation for p-value inconsistent summary."""
        mock_p_diff.return_value = 0.10
        mock_effect.return_value = 0.02
        mock_mismatch.return_value = False

        summary = ABTestSummary(
            url="https://example.com/test6",
            domain="example.com",
            title="Test 6",
            baseline_conversion_rate=0.10,
            treatment_conversion_rate=0.12,
            sample_size_control=1000,
            sample_size_treatment=1000,
            reported_p_value=0.01,
            effect_size=2.0,
            test_type="binary"
        )

        record = validate_summary(
            summary=summary,
            reconstructed_p_value=0.11,
            reconstructed_effect_size=2.04,
            p_threshold=0.05,
            effect_threshold=0.05
        )

        assert record.is_consistent is False
        assert "p-value discrepancy" in record.notes

    @patch('code.src.audit.validator.calculate_absolute_p_difference')
    @patch('code.src.audit.validator.calculate_relative_effect_size_difference')
    @patch('code.src.audit.validator.detect_sample_size_mismatch')
    def test_full_validation_sample_size_mismatch(
        self, mock_mismatch, mock_effect, mock_p_diff
    ):
        """Full validation with sample size mismatch warning."""
        mock_p_diff.return_value = 0.01
        mock_effect.return_value = 0.02
        mock_mismatch.return_value = True

        summary = ABTestSummary(
            url="https://example.com/test7",
            domain="example.com",
            title="Test 7",
            baseline_conversion_rate=0.10,
            treatment_conversion_rate=0.12,
            sample_size_control=1000,
            sample_size_treatment=2000,  # Mismatch
            reported_p_value=0.03,
            effect_size=2.0,
            test_type="binary"
        )

        record = validate_summary(
            summary=summary,
            reconstructed_p_value=0.04,
            reconstructed_effect_size=2.04,
            p_threshold=0.05,
            effect_threshold=0.05
        )

        assert record.is_consistent is True  # Stats are consistent
        assert record.data_quality_warning is not None
        assert "sample size mismatch" in record.data_quality_warning.lower()

    @patch('code.src.audit.validator.calculate_absolute_p_difference')
    @patch('code.src.audit.validator.calculate_relative_effect_size_difference')
    @patch('code.src.audit.validator.detect_sample_size_mismatch')
    def test_full_validation_inequality_handling(
        self, mock_mismatch, mock_effect, mock_p_diff
    ):
        """Full validation with inequality p-value handling."""
        mock_p_diff.return_value = 0.01
        mock_effect.return_value = 0.02
        mock_mismatch.return_value = False

        summary = ABTestSummary(
            url="https://example.com/test8",
            domain="example.com",
            title="Test 8",
            baseline_conversion_rate=0.10,
            treatment_conversion_rate=0.12,
            sample_size_control=1000,
            sample_size_treatment=1000,
            reported_p_value=0.05,  # Representing '< 0.05'
            effect_size=2.0,
            test_type="binary"
        )

        # Reconstructed is 0.04, difference is 0.01 (consistent)
        record = validate_summary(
            summary=summary,
            reconstructed_p_value=0.04,
            reconstructed_effect_size=2.04,
            p_threshold=0.05,
            effect_threshold=0.05
        )

        assert record.is_consistent is True
        assert record.data_quality_warning is None