"""
Unit tests for the validator module (T025).
"""
import pytest
from pathlib import Path
from code.src.models.data_models import ABTestSummary
from code.src.audit.validator import (
    validate_summary,
    validate_all_summaries,
    filter_for_prevalence,
    calculate_absolute_p_difference,
    calculate_relative_effect_size_difference,
    detect_sample_size_mismatch,
    check_p_value_consistency,
    check_effect_size_consistency
)

def test_p_value_consistency_within_threshold():
    """Test p-value consistency when difference is within threshold."""
    summary = ABTestSummary(
        id="test-1",
        url="http://example.com/1",
        domain="example.com",
        year=2023,
        p_value_reported=0.04,
        p_value_reconstructed=0.042,
        effect_size_reported=0.1,
        effect_size_reconstructed=0.101,
        n_control=1000,
        n_treatment=1000
    )
    is_consistent, diff = check_p_value_consistency(summary)
    assert is_consistent
    assert diff is not None
    assert diff <= 0.05

def test_p_value_consistency_outside_threshold():
    """Test p-value consistency when difference exceeds threshold."""
    summary = ABTestSummary(
        id="test-2",
        url="http://example.com/2",
        domain="example.com",
        year=2023,
        p_value_reported=0.04,
        p_value_reconstructed=0.15,
        effect_size_reported=0.1,
        effect_size_reconstructed=0.101,
        n_control=1000,
        n_treatment=1000
    )
    is_consistent, diff = check_p_value_consistency(summary)
    assert not is_consistent
    assert diff is not None
    assert diff > 0.05

def test_effect_size_consistency_within_threshold():
    """Test effect size consistency when relative difference is within threshold."""
    summary = ABTestSummary(
        id="test-3",
        url="http://example.com/3",
        domain="example.com",
        year=2023,
        p_value_reported=0.04,
        p_value_reconstructed=0.041,
        effect_size_reported=0.1,
        effect_size_reconstructed=0.104, # 4% diff
        n_control=1000,
        n_treatment=1000
    )
    is_consistent, diff = check_effect_size_consistency(summary)
    assert is_consistent
    assert diff is not None
    assert diff <= 0.05

def test_effect_size_consistency_outside_threshold():
    """Test effect size consistency when relative difference exceeds threshold."""
    summary = ABTestSummary(
        id="test-4",
        url="http://example.com/4",
        domain="example.com",
        year=2023,
        p_value_reported=0.04,
        p_value_reconstructed=0.041,
        effect_size_reported=0.1,
        effect_size_reconstructed=0.16, # 60% diff
        n_control=1000,
        n_treatment=1000
    )
    is_consistent, diff = check_effect_size_consistency(summary)
    assert not is_consistent
    assert diff is not None
    assert diff > 0.05

def test_sample_size_mismatch_detected():
    """Test detection of sample size mismatch."""
    summary_mismatch = ABTestSummary(
        id="test-5",
        url="http://example.com/5",
        domain="example.com",
        year=2023,
        p_value_reported=0.04,
        p_value_reconstructed=0.04,
        effect_size_reported=0.1,
        effect_size_reconstructed=0.1,
        n_control=-100, # Invalid
        n_treatment=1000
    )
    assert detect_sample_size_mismatch(summary_mismatch) is True

    summary_missing = ABTestSummary(
        id="test-6",
        url="http://example.com/6",
        domain="example.com",
        year=2023,
        p_value_reported=0.04,
        p_value_reconstructed=0.04,
        effect_size_reported=0.1,
        effect_size_reconstructed=0.1,
        n_control=None,
        n_treatment=1000
    )
    assert detect_sample_size_mismatch(summary_missing) is True

def test_sample_size_valid():
    """Test valid sample sizes."""
    summary_valid = ABTestSummary(
        id="test-7",
        url="http://example.com/7",
        domain="example.com",
        year=2023,
        p_value_reported=0.04,
        p_value_reconstructed=0.04,
        effect_size_reported=0.1,
        effect_size_reconstructed=0.1,
        n_control=1000,
        n_treatment=1000
    )
    assert detect_sample_size_mismatch(summary_valid) is False

def test_filter_for_prevalence_excludes_mismatches():
    """Test that filter_for_prevalence excludes records with sample size mismatches."""
    summary_good = ABTestSummary(
        id="good",
        url="http://example.com/good",
        domain="example.com",
        year=2023,
        p_value_reported=0.04,
        p_value_reconstructed=0.04,
        effect_size_reported=0.1,
        effect_size_reconstructed=0.1,
        n_control=1000,
        n_treatment=1000
    )
    summary_bad = ABTestSummary(
        id="bad",
        url="http://example.com/bad",
        domain="example.com",
        year=2023,
        p_value_reported=0.04,
        p_value_reconstructed=0.04,
        effect_size_reported=0.1,
        effect_size_reconstructed=0.1,
        n_control=-100,
        n_treatment=1000
    )

    records = [validate_summary(summary_good), validate_summary(summary_bad)]
    
    # The bad record should have a data_quality_warning about sample size
    assert any("Sample size mismatch" in w for w in records[1].data_quality_warnings)
    
    filtered = filter_for_prevalence(records)
    assert len(filtered) == 1
    assert filtered[0].id == "good"

def test_validate_summary_creates_record():
    """Test that validate_summary creates a proper AuditRecord."""
    summary = ABTestSummary(
        id="test-record",
        url="http://example.com/test",
        domain="example.com",
        year=2023,
        p_value_reported=0.04,
        p_value_reconstructed=0.15, # Inconsistent
        effect_size_reported=0.1,
        effect_size_reconstructed=0.1,
        n_control=1000,
        n_treatment=1000
    )
    record = validate_summary(summary)
    assert record.id == "test-record"
    assert record.is_inconsistent is True
    assert len(record.inconsistency_reasons) > 0

def test_absolute_p_difference_calculation():
    """Test absolute p-difference calculation."""
    assert calculate_absolute_p_difference(0.05, 0.06) == 0.01
    assert calculate_absolute_p_difference(0.05, 0.10) == 0.05
    assert calculate_absolute_p_difference(None, 0.05) is None
    assert calculate_absolute_p_difference(0.05, None) is None

def test_relative_effect_size_calculation():
    """Test relative effect size difference calculation."""
    # 10% reported, 10.5% reconstructed -> 5% relative diff
    assert calculate_relative_effect_size_difference(0.10, 0.105) == 0.05
    # 10% reported, 11% reconstructed -> 10% relative diff
    assert calculate_relative_effect_size_difference(0.10, 0.11) == 0.10
    assert calculate_relative_effect_size_difference(None, 0.10) is None
    assert calculate_relative_effect_size_difference(0.10, None) is None
    # Avoid division by zero
    assert calculate_relative_effect_size_difference(0.0, 0.1) is None
