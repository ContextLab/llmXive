"""
Integration test for validator thresholds (FR-004 Verification).

This test verifies that the validator correctly flags inconsistencies based on
defined thresholds:
- Absolute p-difference > 0.05
- Relative effect-size > 5%

Per coverage-executability-08d5764f, this test must pass to confirm FR-004 compliance.
"""

import json
import pytest
import tempfile
from pathlib import Path
from typing import List, Dict, Any

# Import from existing API surface
from code.src.audit.validator import (
    calculate_absolute_p_difference,
    calculate_relative_effect_size_difference,
    check_p_value_consistency,
    check_effect_size_consistency,
    validate_summary,
    create_audit_record,
)
from code.src.models.data_models import ABTestSummary, AuditRecord


# FR-004 Threshold constants
ABSOLUTE_P_THRESHOLD = 0.05
RELATIVE_EFFECT_SIZE_THRESHOLD = 0.05  # 5%


def test_absolute_p_difference_calculation():
    """Test that absolute p-difference is calculated correctly."""
    # Within threshold
    assert calculate_absolute_p_difference(0.03, 0.05) == pytest.approx(0.02, abs=1e-9)
    
    # Exactly at threshold
    assert calculate_absolute_p_difference(0.00, 0.05) == pytest.approx(0.05, abs=1e-9)
    
    # Beyond threshold
    assert calculate_absolute_p_difference(0.00, 0.10) == pytest.approx(0.10, abs=1e-9)
    
    # Edge case: both p-values are 0
    assert calculate_absolute_p_difference(0.0, 0.0) == 0.0


def test_relative_effect_size_difference_calculation():
    """Test that relative effect-size difference is calculated correctly."""
    # Within threshold (5%)
    # effect_size1 = 0.10, effect_size2 = 0.105 -> relative diff = 0.05 (5%)
    assert calculate_relative_effect_size_difference(0.10, 0.105) == pytest.approx(0.05, abs=1e-9)
    
    # Beyond threshold
    # effect_size1 = 0.10, effect_size2 = 0.11 -> relative diff = 0.10 (10%)
    assert calculate_relative_effect_size_difference(0.10, 0.11) == pytest.approx(0.10, abs=1e-9)
    
    # Edge case: effect_size1 is 0
    assert calculate_relative_effect_size_difference(0.0, 0.05) == pytest.approx(float('inf'), abs=1e-9)


def test_p_value_consistency_within_threshold():
    """Test that p-values within threshold are NOT flagged as inconsistent."""
    summary = ABTestSummary(
        url="https://example.com/test1",
        domain="tech",
        publication_year=2024,
        outcome_type="binary",
        baseline_conversion_rate=0.10,
        treatment_conversion_rate=0.12,
        baseline_sample_size=1000,
        treatment_sample_size=1000,
        reported_p_value=0.03,
        reconstructed_p_value=0.04,  # Within 0.05 threshold
    )
    
    is_consistent, message = check_p_value_consistency(summary)
    assert is_consistent is True
    assert "inconsistent" not in message.lower()


def test_p_value_consistency_beyond_threshold():
    """Test that p-values beyond threshold ARE flagged as inconsistent."""
    summary = ABTestSummary(
        url="https://example.com/test2",
        domain="tech",
        publication_year=2024,
        outcome_type="binary",
        baseline_conversion_rate=0.10,
        treatment_conversion_rate=0.12,
        baseline_sample_size=1000,
        treatment_sample_size=1000,
        reported_p_value=0.01,
        reconstructed_p_value=0.08,  # Beyond 0.05 threshold (diff = 0.07)
    )
    
    is_consistent, message = check_p_value_consistency(summary)
    assert is_consistent is False
    assert "inconsistent" in message.lower() or "difference" in message.lower()


def test_effect_size_consistency_within_threshold():
    """Test that effect sizes within threshold are NOT flagged as inconsistent."""
    summary = ABTestSummary(
        url="https://example.com/test3",
        domain="e-commerce",
        publication_year=2024,
        outcome_type="binary",
        baseline_conversion_rate=0.10,
        treatment_conversion_rate=0.11,  # 10% relative increase
        baseline_sample_size=1000,
        treatment_sample_size=1000,
        reported_effect_size=0.10,
        reconstructed_effect_size=0.105,  # Within 5% threshold
    )
    
    is_consistent, message = check_effect_size_consistency(summary)
    assert is_consistent is True
    assert "inconsistent" not in message.lower()


def test_effect_size_consistency_beyond_threshold():
    """Test that effect sizes beyond threshold ARE flagged as inconsistent."""
    summary = ABTestSummary(
        url="https://example.com/test4",
        domain="finance",
        publication_year=2024,
        outcome_type="binary",
        baseline_conversion_rate=0.10,
        treatment_conversion_rate=0.15,  # 50% relative increase
        baseline_sample_size=1000,
        treatment_sample_size=1000,
        reported_effect_size=0.50,
        reconstructed_effect_size=0.60,  # Beyond 5% threshold (20% relative diff)
    )
    
    is_consistent, message = check_effect_size_consistency(summary)
    assert is_consistent is False
    assert "inconsistent" in message.lower() or "difference" in message.lower()


def test_validate_summary_p_value_threshold():
    """Test validate_summary correctly flags p-value threshold violations."""
    # Create a summary with p-value inconsistency
    summary = ABTestSummary(
        url="https://example.com/test5",
        domain="healthcare",
        publication_year=2024,
        outcome_type="binary",
        baseline_conversion_rate=0.10,
        treatment_conversion_rate=0.12,
        baseline_sample_size=1000,
        treatment_sample_size=1000,
        reported_p_value=0.02,
        reconstructed_p_value=0.10,  # Beyond 0.05 threshold
    )
    
    audit_record = validate_summary(summary)
    
    assert audit_record.is_p_value_inconsistent is True
    assert audit_record.data_quality_warning is not None
    assert "p-value" in audit_record.data_quality_warning.lower()


def test_validate_summary_effect_size_threshold():
    """Test validate_summary correctly flags effect-size threshold violations."""
    # Create a summary with effect-size inconsistency
    summary = ABTestSummary(
        url="https://example.com/test6",
        domain="saas",
        publication_year=2024,
        outcome_type="binary",
        baseline_conversion_rate=0.10,
        treatment_conversion_rate=0.15,
        baseline_sample_size=1000,
        treatment_sample_size=1000,
        reported_effect_size=0.50,
        reconstructed_effect_size=0.70,  # Beyond 5% threshold
    )
    
    audit_record = validate_summary(summary)
    
    assert audit_record.is_effect_size_inconsistent is True
    assert audit_record.data_quality_warning is not None
    assert "effect size" in audit_record.data_quality_warning.lower()


def test_validate_summary_both_thresholds_passed():
    """Test validate_summary does NOT flag when both thresholds are met."""
    summary = ABTestSummary(
        url="https://example.com/test7",
        domain="tech",
        publication_year=2024,
        outcome_type="binary",
        baseline_conversion_rate=0.10,
        treatment_conversion_rate=0.12,
        baseline_sample_size=1000,
        treatment_sample_size=1000,
        reported_p_value=0.03,
        reconstructed_p_value=0.04,  # Within threshold
        reported_effect_size=0.20,
        reconstructed_effect_size=0.21,  # Within threshold
    )
    
    audit_record = validate_summary(summary)
    
    assert audit_record.is_p_value_inconsistent is False
    assert audit_record.is_effect_size_inconsistent is False
    assert audit_record.data_quality_warning is None


def test_create_audit_record_with_threshold_flags():
    """Test create_audit_record properly sets threshold-based flags."""
    summary = ABTestSummary(
        url="https://example.com/test8",
        domain="e-commerce",
        publication_year=2024,
        outcome_type="binary",
        baseline_conversion_rate=0.10,
        treatment_conversion_rate=0.12,
        baseline_sample_size=1000,
        treatment_sample_size=1000,
        reported_p_value=0.01,
        reconstructed_p_value=0.09,  # Beyond threshold
    )
    
    audit_record = create_audit_record(summary)
    
    # The record should flag the inconsistency
    assert audit_record.url == "https://example.com/test8"
    assert audit_record.is_p_value_inconsistent is True


def test_integration_threshold_verification_via_temp_file():
    """
    Integration test: Write synthetic data, run validation, verify threshold flags.
    
    This simulates a real pipeline run to ensure thresholds work end-to-end.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        
        # Create test summaries with known threshold violations
        test_summaries = [
            # Should PASS (within thresholds)
            ABTestSummary(
                url="https://example.com/pass1",
                domain="tech",
                publication_year=2024,
                outcome_type="binary",
                baseline_conversion_rate=0.10,
                treatment_conversion_rate=0.12,
                baseline_sample_size=1000,
                treatment_sample_size=1000,
                reported_p_value=0.03,
                reconstructed_p_value=0.04,
            ),
            # Should FAIL (p-value beyond threshold)
            ABTestSummary(
                url="https://example.com/fail_p",
                domain="e-commerce",
                publication_year=2024,
                outcome_type="binary",
                baseline_conversion_rate=0.10,
                treatment_conversion_rate=0.12,
                baseline_sample_size=1000,
                treatment_sample_size=1000,
                reported_p_value=0.01,
                reconstructed_p_value=0.09,
            ),
            # Should FAIL (effect size beyond threshold)
            ABTestSummary(
                url="https://example.com/fail_effect",
                domain="finance",
                publication_year=2024,
                outcome_type="binary",
                baseline_conversion_rate=0.10,
                treatment_conversion_rate=0.15,
                baseline_sample_size=1000,
                treatment_sample_size=1000,
                reported_effect_size=0.50,
                reconstructed_effect_size=0.70,
            ),
            # Should FAIL (both thresholds)
            ABTestSummary(
                url="https://example.com/fail_both",
                domain="healthcare",
                publication_year=2024,
                outcome_type="binary",
                baseline_conversion_rate=0.10,
                treatment_conversion_rate=0.12,
                baseline_sample_size=1000,
                treatment_sample_size=1000,
                reported_p_value=0.02,
                reconstructed_p_value=0.10,
                reported_effect_size=0.20,
                reconstructed_effect_size=0.30,
            ),
        ]
        
        # Validate all summaries
        audit_records = []
        for summary in test_summaries:
            record = validate_summary(summary)
            audit_records.append(record)
        
        # Verify threshold-based flagging
        # Record 0: Should be consistent
        assert audit_records[0].is_p_value_inconsistent is False
        assert audit_records[0].is_effect_size_inconsistent is False
        
        # Record 1: Should have p-value inconsistency
        assert audit_records[1].is_p_value_inconsistent is True
        
        # Record 2: Should have effect-size inconsistency
        assert audit_records[2].is_effect_size_inconsistent is True
        
        # Record 3: Should have both inconsistencies
        assert audit_records[3].is_p_value_inconsistent is True
        assert audit_records[3].is_effect_size_inconsistent is True


def test_threshold_boundary_cases():
    """Test exact boundary cases for thresholds."""
    # Exactly at p-value threshold (0.05 difference)
    summary_at_p_threshold = ABTestSummary(
        url="https://example.com/boundary_p",
        domain="tech",
        publication_year=2024,
        outcome_type="binary",
        baseline_conversion_rate=0.10,
        treatment_conversion_rate=0.12,
        baseline_sample_size=1000,
        treatment_sample_size=1000,
        reported_p_value=0.00,
        reconstructed_p_value=0.05,  # Exactly at threshold
    )
    
    # FR-004 says "> 0.05", so exactly 0.05 should NOT be flagged
    is_consistent, _ = check_p_value_consistency(summary_at_p_threshold)
    assert is_consistent is True
    
    # Just beyond p-value threshold (0.0501 difference)
    summary_beyond_p_threshold = ABTestSummary(
        url="https://example.com/beyond_p",
        domain="tech",
        publication_year=2024,
        outcome_type="binary",
        baseline_conversion_rate=0.10,
        treatment_conversion_rate=0.12,
        baseline_sample_size=1000,
        treatment_sample_size=1000,
        reported_p_value=0.00,
        reconstructed_p_value=0.0501,  # Just beyond threshold
    )
    
    is_consistent, _ = check_p_value_consistency(summary_beyond_p_threshold)
    assert is_consistent is False


def test_validator_thresholds_with_continuous_outcomes():
    """Test thresholds work correctly for continuous outcomes."""
    # Continuous outcome with p-value inconsistency
    continuous_summary = ABTestSummary(
        url="https://example.com/continuous",
        domain="tech",
        publication_year=2024,
        outcome_type="continuous",
        baseline_conversion_rate=0.0,  # Not applicable for continuous
        treatment_conversion_rate=0.0,  # Not applicable for continuous
        baseline_sample_size=1000,
        treatment_sample_size=1000,
        reported_p_value=0.01,
        reconstructed_p_value=0.09,  # Beyond threshold
    )
    
    audit_record = validate_summary(continuous_summary)
    assert audit_record.is_p_value_inconsistent is True


class TestValidatorThresholdsIntegration:
    """
    pytest-style integration test class for FR-004 threshold verification.
    
    These tests ensure the validator correctly implements FR-004 thresholds:
    - Absolute p-difference > 0.05 triggers inconsistency flag
    - Relative effect-size difference > 5% triggers inconsistency flag
    """
    
    def test_p_value_threshold_flagging(self):
        """Verify p-value threshold flagging works correctly."""
        summary = ABTestSummary(
            url="https://example.com/threshold_test",
            domain="tech",
            publication_year=2024,
            outcome_type="binary",
            baseline_conversion_rate=0.10,
            treatment_conversion_rate=0.12,
            baseline_sample_size=1000,
            treatment_sample_size=1000,
            reported_p_value=0.02,
            reconstructed_p_value=0.10,
        )
        
        audit_record = validate_summary(summary)
        assert audit_record.is_p_value_inconsistent is True
    
    def test_effect_size_threshold_flagging(self):
        """Verify effect-size threshold flagging works correctly."""
        summary = ABTestSummary(
            url="https://example.com/effect_threshold",
            domain="e-commerce",
            publication_year=2024,
            outcome_type="binary",
            baseline_conversion_rate=0.10,
            treatment_conversion_rate=0.15,
            baseline_sample_size=1000,
            treatment_sample_size=1000,
            reported_effect_size=0.50,
            reconstructed_effect_size=0.60,
        )
        
        audit_record = validate_summary(summary)
        assert audit_record.is_effect_size_inconsistent is True
    
    def test_no_flag_when_within_thresholds(self):
        """Verify no flags when all values are within thresholds."""
        summary = ABTestSummary(
            url="https://example.com/within_threshold",
            domain="tech",
            publication_year=2024,
            outcome_type="binary",
            baseline_conversion_rate=0.10,
            treatment_conversion_rate=0.12,
            baseline_sample_size=1000,
            treatment_sample_size=1000,
            reported_p_value=0.03,
            reconstructed_p_value=0.04,
            reported_effect_size=0.20,
            reconstructed_effect_size=0.21,
        )
        
        audit_record = validate_summary(summary)
        assert audit_record.is_p_value_inconsistent is False
        assert audit_record.is_effect_size_inconsistent is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

# FR-004 Verification complete
# coverage-executability-08d5764f: All threshold tests must pass