"""
Unit tests for the validator module (src/audit/validator.py).
Tests cover:
- Absolute p-difference > 0.05
- Relative effect-size difference > 5%
- Inequality p-value handling
- Sample-size mismatch detection and data_quality_warning generation
"""
import pytest
import numpy as np
from pathlib import Path
from typing import Dict, Any, List, Optional
import json

# Import the module under test using the project's structure
# Note: The import path assumes the test is run from the project root or with PYTHONPATH set
try:
    from code.src.audit.validator import (
        calculate_absolute_p_difference,
        calculate_relative_effect_size_difference,
        detect_sample_size_mismatch,
        check_p_value_consistency,
        check_effect_size_consistency,
        create_audit_record,
        validate_summary,
        validate_all_summaries
    )
    from code.src.models.data_models import ABTestSummary, AuditRecord
except ImportError:
    # Fallback for different directory structures if necessary
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    from code.src.audit.validator import (
        calculate_absolute_p_difference,
        calculate_relative_effect_size_difference,
        detect_sample_size_mismatch,
        check_p_value_consistency,
        check_effect_size_consistency,
        create_audit_record,
        validate_summary,
        validate_all_summaries
    )
    from code.src.models.data_models import ABTestSummary, AuditRecord


# --- Helper Factories ---

def make_summary(
    reported_p: Optional[float] = 0.04,
    reconstructed_p: Optional[float] = 0.03,
    reported_effect: Optional[float] = 0.05,
    reconstructed_effect: Optional[float] = 0.048,
    reported_n_control: Optional[int] = 1000,
    reported_n_treatment: Optional[int] = 1000,
    reconstructed_n_control: Optional[int] = 1000,
    reconstructed_n_treatment: Optional[int] = 1000,
    outcome_type: str = "binary",
    is_inequality: bool = False,
    baseline_rate: Optional[float] = 0.1
) -> ABTestSummary:
    """Factory to create an ABTestSummary with specific values for testing."""
    return ABTestSummary(
        url="http://example.com/test",
        domain="example.com",
        title="Test Title",
        reported_p_value=reported_p,
        reconstructed_p_value=reconstructed_p,
        reported_effect_size=reported_effect,
        reconstructed_effect_size=reconstructed_effect,
        n_control=reported_n_control,
        n_treatment=reported_n_treatment,
        reconstructed_n_control=reconstructed_n_control,
        reconstructed_n_treatment=reconstructed_n_treatment,
        outcome_type=outcome_type,
        is_inequality=is_inequality,
        baseline_conversion_rate=baseline_rate
    )


def make_audit_record(
    is_inconsistent: bool = True,
    has_data_quality_warning: bool = False,
    notes: str = ""
) -> AuditRecord:
    """Factory to create an AuditRecord."""
    return AuditRecord(
        url="http://example.com/test",
        domain="example.com",
        title="Test Title",
        is_inconsistent=is_inconsistent,
        has_data_quality_warning=has_data_quality_warning,
        notes=notes
    )


# --- Test: Absolute p-difference > 0.05 ---

class TestAbsolutePDifference:
    def test_p_difference_exceeds_threshold(self):
        """Verify that a p-difference > 0.05 is flagged as inconsistent."""
        summary = make_summary(reported_p=0.05, reconstructed_p=0.11) # Diff = 0.06
        result = validate_summary(summary, p_threshold=0.05, effect_threshold=0.05)
        
        assert result.is_inconsistent is True
        assert "p-value" in result.notes.lower()

    def test_p_difference_within_threshold(self):
        """Verify that a p-difference <= 0.05 is NOT flagged for p-value inconsistency."""
        summary = make_summary(reported_p=0.05, reconstructed_p=0.09) # Diff = 0.04
        result = validate_summary(summary, p_threshold=0.05, effect_threshold=0.05)
        
        # Should be consistent regarding p-value (assuming effect size is also fine)
        # We check the specific flag logic. If only p-value is checked:
        assert result.is_inconsistent is False

    def test_p_difference_exactly_threshold(self):
        """Verify boundary condition: diff == 0.05 is consistent (strict >)."""
        summary = make_summary(reported_p=0.05, reconstructed_p=0.10) # Diff = 0.05
        result = validate_summary(summary, p_threshold=0.05, effect_threshold=0.05)
        
        assert result.is_inconsistent is False


# --- Test: Relative Effect-Size Difference > 5% ---

class TestEffectSizeDifference:
    def test_effect_diff_exceeds_threshold(self):
        """Verify that a relative effect-size diff > 5% is flagged."""
        # reported=0.10, reconstructed=0.106 -> diff=0.006, rel=6%
        summary = make_summary(reported_effect=0.10, reconstructed_effect=0.106)
        result = validate_summary(summary, p_threshold=0.05, effect_threshold=0.05)
        
        assert result.is_inconsistent is True
        assert "effect" in result.notes.lower()

    def test_effect_diff_within_threshold(self):
        """Verify that a relative effect-size diff <= 5% is NOT flagged."""
        # reported=0.10, reconstructed=0.103 -> diff=0.003, rel=3%
        summary = make_summary(reported_effect=0.10, reconstructed_effect=0.103)
        result = validate_summary(summary, p_threshold=0.05, effect_threshold=0.05)
        
        assert result.is_inconsistent is False

    def test_effect_diff_zero(self):
        """Verify exact match is consistent."""
        summary = make_summary(reported_effect=0.10, reconstructed_effect=0.10)
        result = validate_summary(summary, p_threshold=0.05, effect_threshold=0.05)
        
        assert result.is_inconsistent is False


# --- Test: Inequality Handling ---

class TestInequalityHandling:
    def test_inequality_flagged_as_warning(self):
        """Verify that inequality p-values trigger a data_quality_warning."""
        summary = make_summary(reported_p=0.05, reconstructed_p=0.05, is_inequality=True)
        result = validate_summary(summary, p_threshold=0.05, effect_threshold=0.05)
        
        assert result.has_data_quality_warning is True
        assert "inequality" in result.notes.lower()

    def test_inequality_does_not_force_inconsistency(self):
        """Verify that inequality alone doesn't make it inconsistent if stats match."""
        summary = make_summary(reported_p=0.05, reconstructed_p=0.05, is_inequality=True)
        result = validate_summary(summary, p_threshold=0.05, effect_threshold=0.05)
        
        # It should be marked consistent (stats match) but with a warning
        assert result.is_inconsistent is False
        assert result.has_data_quality_warning is True


# --- Test: Sample-Size Mismatch & Data Quality Warning ---

class TestSampleSizeMismatch:
    def test_sample_size_mismatch_detected(self):
        """Verify that mismatched sample sizes trigger a data_quality_warning."""
        summary = make_summary(
            reported_n_control=1000,
            reconstructed_n_control=1100 # 10% mismatch
        )
        result = validate_summary(summary, p_threshold=0.05, effect_threshold=0.05)
        
        assert result.has_data_quality_warning is True
        assert "sample size" in result.notes.lower()

    def test_sample_size_mismatch_excluded_from_prevalence_logic(self):
        """
        Verify that the record is flagged so it can be excluded from prevalence estimates.
        The validator itself generates the warning; the exclusion logic is in T025c/Prevalence.
        We verify the flag is set correctly.
        """
        summary = make_summary(
            reported_n_control=1000,
            reconstructed_n_control=1500,
            reported_n_treatment=1000,
            reconstructed_n_treatment=1500
        )
        result = validate_summary(summary, p_threshold=0.05, effect_threshold=0.05)
        
        assert result.has_data_quality_warning is True
        assert "sample size" in result.notes.lower()
        # Even if stats are consistent, the warning must be present
        assert result.is_inconsistent is False

    def test_no_sample_size_mismatch(self):
        """Verify that matching sample sizes do not trigger a warning."""
        summary = make_summary(
            reported_n_control=1000,
            reconstructed_n_control=1000
        )
        result = validate_summary(summary, p_threshold=0.05, effect_threshold=0.05)
        
        assert result.has_data_quality_warning is False


# --- Test: Combined Scenarios ---

class TestCombinedScenarios:
    def test_multiple_issues(self):
        """Verify handling of multiple inconsistencies."""
        summary = make_summary(
            reported_p=0.01,
            reconstructed_p=0.08, # Diff > 0.05
            reported_effect=0.10,
            reconstructed_effect=0.15, # Diff > 5%
            reported_n_control=1000,
            reconstructed_n_control=1200 # Mismatch
        )
        result = validate_summary(summary, p_threshold=0.05, effect_threshold=0.05)
        
        assert result.is_inconsistent is True
        assert result.has_data_quality_warning is True
        assert "p-value" in result.notes.lower()
        assert "effect" in result.notes.lower()
        assert "sample size" in result.notes.lower()

    def test_only_sample_size_mismatch(self):
        """Verify that only sample size mismatch results in warning but not inconsistency."""
        summary = make_summary(
            reported_p=0.05,
            reconstructed_p=0.05,
            reported_effect=0.05,
            reconstructed_effect=0.05,
            reported_n_control=1000,
            reconstructed_n_control=1300
        )
        result = validate_summary(summary, p_threshold=0.05, effect_threshold=0.05)
        
        assert result.is_inconsistent is False
        assert result.has_data_quality_warning is True


# --- Test: Batch Validation ---

class TestValidateAll:
    def test_validate_all_summaries(self):
        """Verify that validate_all_summaries processes a list correctly."""
        summaries = [
            make_summary(reported_p=0.05, reconstructed_p=0.05), # Consistent
            make_summary(reported_p=0.01, reconstructed_p=0.10), # Inconsistent
            make_summary(reported_n_control=1000, reconstructed_n_control=1500) # Warning
        ]
        
        records = validate_all_summaries(summaries, p_threshold=0.05, effect_threshold=0.05)
        
        assert len(records) == 3
        assert records[0].is_inconsistent is False
        assert records[0].has_data_quality_warning is False
        
        assert records[1].is_inconsistent is True
        assert records[1].has_data_quality_warning is False
        
        assert records[2].is_inconsistent is False
        assert records[2].has_data_quality_warning is True