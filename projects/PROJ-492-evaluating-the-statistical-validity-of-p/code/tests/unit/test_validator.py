"""
Unit tests for the inconsistency validator (T025).

Tests cover:
- Absolute p-difference > 0.05 threshold
- Relative effect-size > 5% threshold
- Sample-size mismatch detection and exclusion from prevalence
- data_quality_warning generation
"""

import pytest
from pathlib import Path
import json
from datetime import datetime

from code.src.models.data_models import ABTestSummary, AuditRecord
from code.src.audit.validator import (
    validate_single_summary,
    validate_all_summaries,
    filter_for_prevalence,
    calculate_relative_effect_size_diff,
    check_sample_size_mismatch,
    SAMPLE_SIZE_MISMATCH_THRESHOLD
)

# Test fixtures
def create_summary(
    url: str = "https://example.com/test",
    domain: str = "example.com",
    year: int = 2024,
    p_value: float = 0.03,
    reconstructed_p_value: float = 0.03,
    effect_size: float = 0.10,
    reconstructed_effect_size: float = 0.10,
    n_control: int = 1000,
    reconstructed_n_control: int = 1000,
    n_treatment: int = 1000,
    reconstructed_n_treatment: int = 1000,
    baseline_conversion: float = 0.15,
    treatment_conversion: float = 0.165
) -> ABTestSummary:
    return ABTestSummary(
        url=url,
        domain=domain,
        year=year,
        p_value=p_value,
        reconstructed_p_value=reconstructed_p_value,
        effect_size=effect_size,
        reconstructed_effect_size=reconstructed_effect_size,
        n_control=n_control,
        reconstructed_n_control=reconstructed_n_control,
        n_treatment=n_treatment,
        reconstructed_n_treatment=reconstructed_n_treatment,
        baseline_conversion=baseline_conversion,
        treatment_conversion=treatment_conversion,
        outcome_type="binary"
    )

class TestPValueThreshold:
    """Test absolute p-difference threshold > 0.05"""
    
    def test_p_value_within_threshold(self):
        """P-diff = 0.03 should not trigger inconsistency"""
        summary = create_summary(
            p_value=0.05,
            reconstructed_p_value=0.02  # diff = 0.03
        )
        record = validate_single_summary(summary)
        
        assert not record.is_inconsistent
        assert "p_value_mismatch" not in record.flags
    
    def test_p_value_exceeds_threshold(self):
        """P-diff = 0.06 should trigger inconsistency"""
        summary = create_summary(
            p_value=0.05,
            reconstructed_p_value=0.11  # diff = 0.06
        )
        record = validate_single_summary(summary)
        
        assert record.is_inconsistent
        assert "p_value_mismatch" in record.flags
    
    def test_p_value_at_threshold_boundary(self):
        """P-diff = 0.05 exactly should not trigger (strictly greater)"""
        summary = create_summary(
            p_value=0.05,
            reconstructed_p_value=0.10  # diff = 0.05
        )
        record = validate_single_summary(summary)
        
        assert not record.is_inconsistent
        assert "p_value_mismatch" not in record.flags
    
    def test_p_value_just_over_threshold(self):
        """P-diff = 0.051 should trigger inconsistency"""
        summary = create_summary(
            p_value=0.05,
            reconstructed_p_value=0.101  # diff = 0.051
        )
        record = validate_single_summary(summary)
        
        assert record.is_inconsistent
        assert "p_value_mismatch" in record.flags

class TestEffectSizeThreshold:
    """Test relative effect-size threshold > 5%"""
    
    def test_effect_size_within_threshold(self):
        """Relative diff = 4% should not trigger inconsistency"""
        summary = create_summary(
            effect_size=0.10,
            reconstructed_effect_size=0.104  # 4% relative diff
        )
        record = validate_single_summary(summary)
        
        assert not record.is_inconsistent
        assert "effect_size_mismatch" not in record.flags
    
    def test_effect_size_exceeds_threshold(self):
        """Relative diff = 6% should trigger inconsistency"""
        summary = create_summary(
            effect_size=0.10,
            reconstructed_effect_size=0.106  # 6% relative diff
        )
        record = validate_single_summary(summary)
        
        assert record.is_inconsistent
        assert "effect_size_mismatch" in record.flags
    
    def test_effect_size_at_threshold_boundary(self):
        """Relative diff = 5% exactly should not trigger (strictly greater)"""
        summary = create_summary(
            effect_size=0.10,
            reconstructed_effect_size=0.105  # 5% relative diff
        )
        record = validate_single_summary(summary)
        
        assert not record.is_inconsistent
        assert "effect_size_mismatch" not in record.flags
    
    def test_effect_size_just_over_threshold(self):
        """Relative diff = 5.1% should trigger inconsistency"""
        summary = create_summary(
            effect_size=0.10,
            reconstructed_effect_size=0.1051  # 5.1% relative diff
        )
        record = validate_single_summary(summary)
        
        assert record.is_inconsistent
        assert "effect_size_mismatch" in record.flags
    
    def test_effect_size_zero_reported(self):
        """Zero reported effect size with non-zero reconstructed should trigger"""
        summary = create_summary(
            effect_size=0.0,
            reconstructed_effect_size=0.01
        )
        record = validate_single_summary(summary)
        
        assert record.is_inconsistent
        assert "effect_size_mismatch" in record.flags

class TestSampleSizeMismatch:
    """Test sample-size mismatch detection and exclusion"""
    
    def test_sample_size_match(self):
        """Matching sample sizes should not trigger warning"""
        summary = create_summary(
            n_control=1000,
            reconstructed_n_control=1000,
            n_treatment=1000,
            reconstructed_n_treatment=1000
        )
        record = validate_single_summary(summary)
        
        assert record.data_quality_warning is None
        assert "sample_size_mismatch" not in record.flags
    
    def test_sample_size_within_tolerance(self):
        """Sample size diff < 5% should not trigger warning"""
        summary = create_summary(
            n_control=1000,
            reconstructed_n_control=1040,  # 4% diff
            n_treatment=1000,
            reconstructed_n_treatment=1040
        )
        record = validate_single_summary(summary)
        
        assert record.data_quality_warning is None
        assert "sample_size_mismatch" not in record.flags
    
    def test_sample_size_exceeds_tolerance(self):
        """Sample size diff > 5% should trigger warning"""
        summary = create_summary(
            n_control=1000,
            reconstructed_n_control=1060,  # 6% diff
            n_treatment=1000,
            reconstructed_n_treatment=1060
        )
        record = validate_single_summary(summary)
        
        assert record.data_quality_warning is not None
        assert "sample_size_mismatch" in record.flags
        assert "Sample size mismatch detected" in record.data_quality_warning
    
    def test_sample_size_mismatch_not_inconsistent(self):
        """Sample size mismatch alone should NOT make record inconsistent for prevalence"""
        summary = create_summary(
            p_value=0.03,
            reconstructed_p_value=0.03,  # No p-value mismatch
            effect_size=0.10,
            reconstructed_effect_size=0.10,  # No effect size mismatch
            n_control=1000,
            reconstructed_n_control=1100,  # 10% diff - triggers warning
            n_treatment=1000,
            reconstructed_n_treatment=1100
        )
        record = validate_single_summary(summary)
        
        # Has warning but is NOT inconsistent
        assert record.data_quality_warning is not None
        assert "sample_size_mismatch" in record.flags
        assert not record.is_inconsistent
    
    def test_sample_size_mismatch_excluded_from_prevalence(self):
        """Records with sample_size_mismatch should be excluded from prevalence"""
        summaries = [
            create_summary(p_value=0.03, reconstructed_p_value=0.03),  # Clean
            create_summary(
                n_control=1000, reconstructed_n_control=1100,  # Mismatch
                p_value=0.03, reconstructed_p_value=0.03
            ),
            create_summary(p_value=0.10, reconstructed_p_value=0.02)  # Inconsistent
        ]
        
        records = validate_all_summaries(summaries)
        prevalence_records = filter_for_prevalence(records)
        
        # Should have 2 records (clean + inconsistent), excluding the mismatch one
        assert len(prevalence_records) == 2
        assert all("sample_size_mismatch" not in r.flags for r in prevalence_records)

class TestCombinedScenarios:
    """Test combinations of violations"""
    
    def test_both_p_and_effect_size_violations(self):
        """Both thresholds exceeded should flag both"""
        summary = create_summary(
            p_value=0.05,
            reconstructed_p_value=0.12,  # diff = 0.07
            effect_size=0.10,
            reconstructed_effect_size=0.12  # 20% relative diff
        )
        record = validate_single_summary(summary)
        
        assert record.is_inconsistent
        assert "p_value_mismatch" in record.flags
        assert "effect_size_mismatch" in record.flags
    
    def test_mismatch_with_p_violation(self):
        """Sample size mismatch + p-value violation"""
        summary = create_summary(
            p_value=0.05,
            reconstructed_p_value=0.12,  # diff = 0.07
            n_control=1000,
            reconstructed_n_control=1100  # 10% diff
        )
        record = validate_single_summary(summary)
        
        assert record.is_inconsistent
        assert "p_value_mismatch" in record.flags
        assert "sample_size_mismatch" in record.flags
        assert record.data_quality_warning is not None

class TestHelperFunctions:
    """Test helper functions directly"""
    
    def test_relative_effect_size_calculation(self):
        """Verify relative effect size calculation"""
        diff = calculate_relative_effect_size_diff(0.10, 0.105)
        assert abs(diff - 0.05) < 1e-6
    
    def test_relative_effect_size_zero_reported(self):
        """Zero reported effect size returns inf"""
        diff = calculate_relative_effect_size_diff(0.0, 0.01)
        assert diff == float('inf')
    
    def test_relative_effect_size_both_zero(self):
        """Both zero returns 0"""
        diff = calculate_relative_effect_size_diff(0.0, 0.0)
        assert diff == 0.0
    
    def test_sample_size_mismatch_check(self):
        """Verify sample size mismatch detection"""
        summary = create_summary(
            n_control=1000,
            reconstructed_n_control=1060
        )
        is_mismatch, msg = check_sample_size_mismatch(summary)
        
        assert is_mismatch
        assert "Sample size mismatch detected" in msg

class TestAuditRecordStructure:
    """Test that AuditRecord contains all required fields"""
    
    def test_audit_record_fields(self):
        """Verify all expected fields are present in AuditRecord"""
        summary = create_summary(
            p_value=0.05,
            reconstructed_p_value=0.12
        )
        record = validate_single_summary(summary)
        
        # Check all expected attributes exist
        assert hasattr(record, 'url')
        assert hasattr(record, 'domain')
        assert hasattr(record, 'year')
        assert hasattr(record, 'is_inconsistent')
        assert hasattr(record, 'flags')
        assert hasattr(record, 'data_quality_warning')
        assert hasattr(record, 'reported_p_value')
        assert hasattr(record, 'reconstructed_p_value')
        assert hasattr(record, 'reported_effect_size')
        assert hasattr(record, 'reconstructed_effect_size')
        assert hasattr(record, 'reported_n_control')
        assert hasattr(record, 'reconstructed_n_control')
        assert hasattr(record, 'reported_n_treatment')
        assert hasattr(record, 'reconstructed_n_treatment')
        assert hasattr(record, 'validation_timestamp')

if __name__ == "__main__":
    pytest.main([__file__, "-v"])