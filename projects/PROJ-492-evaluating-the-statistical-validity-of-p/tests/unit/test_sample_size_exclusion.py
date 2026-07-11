"""
Unit tests for T025c: Verify that sample-size mismatch entries are excluded
from aggregate prevalence estimates per FR-004b.

This test ensures that the validator correctly flags records with sample-size
discrepancies and that these records are excluded when calculating aggregate
inconsistency rates.
"""
import json
import os
import pytest
from pathlib import Path
from typing import List, Dict, Any

# Import the validator module
from code.src.audit.validator import (
    validate_all,
    check_sample_size_consistency,
    is_sample_size_mismatch
)
from code.src.models.data_models import ABTestSummary, AuditRecord
from code.src.utils.logger import get_default_logger

# Test fixtures
SAMPLE_SIZE_MISMATCH_RECORD = {
    "url": "https://example.com/test1",
    "baseline_n": 1000,
    "treatment_n": 1000,
    "baseline_rate": 0.05,
    "treatment_rate": 0.07,
    "reported_p_value": 0.03,
    "reconstructed_p_value": 0.029,
    "p_difference": 0.001,
    "effect_size_difference": 0.02,
    "is_inconsistent": False,
    "data_quality_warning": "Sample size mismatch detected",
    "sample_size_mismatch": True
}

VALID_RECORD = {
    "url": "https://example.com/test2",
    "baseline_n": 1000,
    "treatment_n": 1000,
    "baseline_rate": 0.05,
    "treatment_rate": 0.10,
    "reported_p_value": 0.01,
    "reconstructed_p_value": 0.009,
    "p_difference": 0.001,
    "effect_size_difference": 0.05,
    "is_inconsistent": True,
    "data_quality_warning": None,
    "sample_size_mismatch": False
}

INCONSISTENT_WITHOUT_MISMATCH = {
    "url": "https://example.com/test3",
    "baseline_n": 1000,
    "treatment_n": 1000,
    "baseline_rate": 0.05,
    "treatment_rate": 0.15,
    "reported_p_value": 0.01,
    "reconstructed_p_value": 0.08,
    "p_difference": 0.07,
    "effect_size_difference": 0.10,
    "is_inconsistent": True,
    "data_quality_warning": None,
    "sample_size_mismatch": False
}

def test_sample_size_mismatch_detection():
    """Test that sample size mismatches are correctly identified."""
    # Create summaries with known sample size mismatches
    summary1 = ABTestSummary(
        url="https://example.com/mismatch",
        baseline_n=1000,
        treatment_n=1500,  # Different from baseline
        baseline_rate=0.05,
        treatment_rate=0.07,
        reported_p_value=0.03
    )
    
    summary2 = ABTestSummary(
        url="https://example.com/match",
        baseline_n=1000,
        treatment_n=1000,  # Same as baseline
        baseline_rate=0.05,
        treatment_rate=0.07,
        reported_p_value=0.03
    )
    
    # Check sample size consistency
    mismatch_result = check_sample_size_consistency(summary1)
    match_result = check_sample_size_consistency(summary2)
    
    assert mismatch_result["is_mismatch"] is True
    assert mismatch_result["baseline_n"] == 1000
    assert mismatch_result["treatment_n"] == 1500
    
    assert match_result["is_mismatch"] is False
    assert match_result["baseline_n"] == 1000
    assert match_result["treatment_n"] == 1000

def test_is_sample_size_mismatch_function():
    """Test the helper function for checking sample size mismatches."""
    # Test with mismatch
    mismatch_record = {
        "baseline_n": 1000,
        "treatment_n": 1500
    }
    assert is_sample_size_mismatch(mismatch_record) is True
    
    # Test with match
    match_record = {
        "baseline_n": 1000,
        "treatment_n": 1000
    }
    assert is_sample_size_mismatch(match_record) is False
    
    # Test with None values (should not crash)
    none_record = {
        "baseline_n": None,
        "treatment_n": None
    }
    assert is_sample_size_mismatch(none_record) is False

def test_validation_flags_sample_size_mismatches():
    """Test that validation correctly flags sample size mismatches."""
    # Create a summary with sample size mismatch
    summary = ABTestSummary(
        url="https://example.com/mismatch",
        baseline_n=1000,
        treatment_n=1500,
        baseline_rate=0.05,
        treatment_rate=0.07,
        reported_p_value=0.03
    )
    
    # Run validation
    records = validate_all([summary])
    
    assert len(records) == 1
    record = records[0]
    
    # Check that the record has a data quality warning
    assert record.data_quality_warning is not None
    assert "Sample size mismatch" in record.data_quality_warning
    assert record.sample_size_mismatch is True

def test_exclusion_from_prevalence_calculation():
    """Test that sample size mismatch records are excluded from prevalence estimates."""
    # Create a mix of records
    summaries = [
        ABTestSummary(
            url="https://example.com/mismatch",
            baseline_n=1000,
            treatment_n=1500,
            baseline_rate=0.05,
            treatment_rate=0.07,
            reported_p_value=0.03
        ),
        ABTestSummary(
            url="https://example.com/consistent",
            baseline_n=1000,
            treatment_n=1000,
            baseline_rate=0.05,
            treatment_rate=0.10,
            reported_p_value=0.01
        ),
        ABTestSummary(
            url="https://example.com/inconsistent",
            baseline_n=1000,
            treatment_n=1000,
            baseline_rate=0.05,
            treatment_rate=0.15,
            reported_p_value=0.01
        )
    ]
    
    # Run validation
    records = validate_all(summaries)
    
    # Count total records
    total_records = len(records)
    assert total_records == 3
    
    # Count mismatch records
    mismatch_records = [r for r in records if r.sample_size_mismatch]
    assert len(mismatch_records) == 1
    
    # Count non-mismatch records
    non_mismatch_records = [r for r in records if not r.sample_size_mismatch]
    assert len(non_mismatch_records) == 2
    
    # Count inconsistent records among non-mismatch
    inconsistent_non_mismatch = [
        r for r in non_mismatch_records if r.is_inconsistent
    ]
    assert len(inconsistent_non_mismatch) == 1
    
    # Calculate prevalence excluding mismatches
    if len(non_mismatch_records) > 0:
        prevalence_excluding_mismatches = len(inconsistent_non_mismatch) / len(non_mismatch_records)
        # Should be 0.5 (1 inconsistent out of 2 non-mismatch)
        assert abs(prevalence_excluding_mismatches - 0.5) < 0.01
    
    # Calculate prevalence including mismatches (should be different)
    all_inconsistent = [r for r in records if r.is_inconsistent]
    if len(records) > 0:
        prevalence_including_mismatches = len(all_inconsistent) / len(records)
        # Should be 0.333 (1 inconsistent out of 3 total)
        assert abs(prevalence_including_mismatches - 0.333) < 0.01
        
    # Verify that excluding mismatches changes the prevalence
    assert prevalence_excluding_mismatches != prevalence_including_mismatches

def test_audit_record_structure_for_mismatches():
    """Test that AuditRecord correctly structures sample size mismatch data."""
    summary = ABTestSummary(
        url="https://example.com/mismatch",
        baseline_n=1000,
        treatment_n=1500,
        baseline_rate=0.05,
        treatment_rate=0.07,
        reported_p_value=0.03
    )
    
    records = validate_all([summary])
    record = records[0]
    
    # Check that all required fields are present
    assert hasattr(record, 'url')
    assert hasattr(record, 'data_quality_warning')
    assert hasattr(record, 'sample_size_mismatch')
    assert hasattr(record, 'is_inconsistent')
    
    # Check values
    assert record.url == "https://example.com/mismatch"
    assert record.sample_size_mismatch is True
    assert record.data_quality_warning is not None
    assert "Sample size mismatch" in record.data_quality_warning

def test_multiple_mismatch_records():
    """Test handling of multiple sample size mismatch records."""
    summaries = [
        ABTestSummary(
            url=f"https://example.com/mismatch{i}",
            baseline_n=1000,
            treatment_n=1500 + i * 100,
            baseline_rate=0.05,
            treatment_rate=0.07,
            reported_p_value=0.03
        )
        for i in range(5)
    ]
    
    # Add some non-mismatch records
    summaries.extend([
        ABTestSummary(
            url=f"https://example.com/valid{i}",
            baseline_n=1000,
            treatment_n=1000,
            baseline_rate=0.05,
            treatment_rate=0.10,
            reported_p_value=0.01
        )
        for i in range(3)
    ])
    
    records = validate_all(summaries)
    
    # Count mismatch records
    mismatch_records = [r for r in records if r.sample_size_mismatch]
    assert len(mismatch_records) == 5
    
    # Count non-mismatch records
    non_mismatch_records = [r for r in records if not r.sample_size_mismatch]
    assert len(non_mismatch_records) == 3
    
    # Verify all mismatch records have warnings
    for record in mismatch_records:
        assert record.data_quality_warning is not None
        assert "Sample size mismatch" in record.data_quality_warning

def test_prevalence_calculation_with_no_valid_records():
    """Test prevalence calculation when all records have sample size mismatches."""
    summaries = [
        ABTestSummary(
            url=f"https://example.com/mismatch{i}",
            baseline_n=1000,
            treatment_n=1500 + i * 100,
            baseline_rate=0.05,
            treatment_rate=0.07,
            reported_p_value=0.03
        )
        for i in range(3)
    ]
    
    records = validate_all(summaries)
    
    # All records should be mismatch records
    mismatch_records = [r for r in records if r.sample_size_mismatch]
    assert len(mismatch_records) == 3
    
    # Non-mismatch records should be empty
    non_mismatch_records = [r for r in records if not r.sample_size_mismatch]
    assert len(non_mismatch_records) == 0
    
    # Prevalence calculation should handle empty denominator gracefully
    # (In a real implementation, this might raise a warning or return 0)
    # For now, we just verify the filtering works correctly

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
